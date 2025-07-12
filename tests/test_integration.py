import os
import sys
import time
import runpy
import random
import pytest
import socket
import subprocess

from unittest.mock import patch

# Local imports
import client
import server


# Fixture
@pytest.fixture(scope="module")
def free_tcp_port():
    # Dynamically pick a free port
    s = socket.socket()
    s.bind(('', 0))
    addr, port = s.getsockname()
    s.close()
    return port


# Helper
def end_subp_gather_output(proc, terminate=True):
    if terminate:
        proc.terminate()

    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    output = stdout.decode() + stderr.decode()

    return output

## Test normal operation

# Default parameters
# Verifies:
#   - All expected heartbeats are received by server
#   - Client automatically exits if server dies
#   - Server does not see any errors or warnings
def test_integration_default_params():
    # Run server
    server_proc = subprocess.Popen([sys.executable, 'server.py'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(0.5)  # Wait for server to start

    # Run client
    client_proc = subprocess.Popen([sys.executable, 'client.py'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    duration_s = random.randint(3, 10)
    time.sleep(duration_s)  # Let some heartbeats be transmitted

    server_output = end_subp_gather_output(server_proc)

    # Client should exit automatically once server stops
    client_output = end_subp_gather_output(client_proc, terminate=False)

    # Client should have exited because of BrokenPipeError, caught by client.py
    assert client_proc.returncode == 1
    assert "Server may have abruptly closed" in client_output

    # Verify that server received and logged heartbeats
    # Depending on timing, the last heartbeat may not be transmitted during the
    #   sleep time
    for i in range(1, duration_s-1):
        assert f"Sequence #{i}" in server_output

    # Verify no errors
    assert "WARNING" not in server_output
    assert "ERROR" not in server_output

# Custom parameters
def test_integration_custom_params(free_tcp_port):
    port = str(free_tcp_port)
    # Run server
    server_proc = subprocess.Popen([sys.executable, 'server.py', '-p', port,
        '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(0.5)  # Wait for server to start

    # Run client
    client_proc = subprocess.Popen([sys.executable, 'client.py', '-p', port,
        '-i 10'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(2)  # Let some heartbeats be transmitted

    server_output = end_subp_gather_output(server_proc)

    # Client should exit automatically once server stops
    client_output = end_subp_gather_output(client_proc, terminate=False)

    # Client should have exited because of BrokenPipeError, caught by client.py
    assert client_proc.returncode == 1
    assert "Server may have abruptly closed" in client_output

    # Verify server received and logged at least one heartbeat
    assert "Sequence #2" in server_output

    # Check if debug logging was included
    assert "DEBUG" in server_output

    # Verify no errors
    assert "WARNING" not in server_output
    assert "ERROR" not in server_output

# Test with a remote host
def test_client_connect_remote_host():
    host = 'google.com'
    port = '80'

    client_proc = subprocess.Popen([sys.executable, 'client.py', '-ho',
        host, '-p', port, '-i', '100'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(2)  # Let some heartbeats be transmitted

    # Force stop client
    client_output = end_subp_gather_output(client_proc, terminate=True)

    # Check to make sure connection was successful
    assert f"Successfully connected to {host}:{port}" in client_output

    # Ensure heartbeat was sent
    assert "Sequence #4: Sending heartbeat at" in client_output


## Test failing cases

# Run client before server starts
def test_client_spawn_before_server():
    # Run client
    client_proc = subprocess.Popen([sys.executable, 'client.py'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    client_output = end_subp_gather_output(client_proc, terminate=False)

    # Client should have exited because of ConnectionRefusedError
    assert client_proc.returncode == 1
    assert "Failed to connect to server" in client_output

# Test with host that does not exist/resolve correctly
def test_client_invalid_host():
    client_proc = subprocess.Popen([sys.executable, 'client.py', '-ho',
        'example_test.com'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    client_output = end_subp_gather_output(client_proc, terminate=False)

    # Client should hav exited because of socket.gaierror
    assert client_proc.returncode == 1
    assert "Name or service not known" in client_output

# Test if port-in-use error is handled gracefully
def test_server_port_in_use(free_tcp_port):
    port = str(free_tcp_port)

    time.sleep(0.5)  # Let socket from free_tcp_port() be freed

    server1_proc = subprocess.Popen([sys.executable, 'server.py', '-p', port,
        '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(1)  # Let server1 bind socket

    server2_proc = subprocess.Popen([sys.executable, 'server.py', '-p', port,
        '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Server 2 should have exited automatically because of port being in use
    server2_output = end_subp_gather_output(server2_proc, terminate=False)

    # Check if server2 exited with exit code 1 - expected when port-in-use error
    # is gracefully handled
    assert server2_proc.returncode == 1

    # Check if expected error was logged
    assert "Address already in use" in server2_output

    end_subp_gather_output(server1_proc)  # Clean up

# Test if server can accept a new client connection if the first client dies
def test_server_works_with_new_client(free_tcp_port):
    port = str(free_tcp_port)

    server_proc = subprocess.Popen([sys.executable, 'server.py', '-p', port],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(1)  # Let server start up

    client1_proc = subprocess.Popen([sys.executable, 'client.py', '-p', port,
        '-i', '500'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(2)  # Let some heartbeats be transmitted

    # Force stop client
    end_subp_gather_output(client1_proc, terminate=True)

    # Connect new client
    client2_proc = subprocess.Popen([sys.executable, 'client.py', '-p', port,
        '-i', '400'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(2)  # Let some heartbeats be transmitted

    server_output = end_subp_gather_output(server_proc)  # End server

    # Ensure server detected client leaving
    client_connection_close_log = "Connection likely closed by client"
    assert client_connection_close_log in server_output

    # Split server stdout+stderr into each client's connection
    server_out_list = server_output.split(client_connection_close_log)
    server_out_client1 = server_out_list[0]
    server_out_client2 = server_out_list[1]

    # Ensure server received heartbeat from first client
    assert "Sequence #2" in server_out_client1

    # Check if server detected client disconnect
    assert "No data received." in server_out_client1

    # Verify heartbeats sent by new client (client2) were received by server
    assert "Sequence #4" in server_out_client2

    # Cleanup
    end_subp_gather_output(client2_proc, terminate=False)
