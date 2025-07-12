import sys
import random
import pytest

from unittest.mock import patch

# Local import
import client


## Test args

# Host
def test_remote_host():
    remote_host = '10.30.21.1'
    port = '350'

    test_args = ['client.py', '--host', remote_host, '--port', port]
    with patch.object(sys, 'argv', test_args):
        args = client.parse_args()
        assert args.host == remote_host
        assert args.port == int(port)

# Port
def test_random_valid_port():
    port = random.randint(0, 65535)

    test_args = ['client.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        args = client.parse_args()
        assert args.port == port

def test_invalid_port_ge_max():
    port = random.randint(65536, sys.maxsize)
    test_args = ['client.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = client.parse_args()

        assert sysexit.value.code == 2

def test_invalid_port_le_min():
    port = random.randint(-sys.maxsize, -1)
    test_args = ['client.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = client.parse_args()

        assert sysexit.value.code == 2

def test_invalid_port_string():
    port = "Port of Subs"

    test_args = ['client.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = client.parse_args()

        assert sysexit.value.code == 2

# Interval
def test_valid_interval():
    interval = random.randint(1, sys.maxsize)

    test_args = ['client.py', '--interval', str(interval)]
    with patch.object(sys, 'argv', test_args):
        args = client.parse_args()
        assert args.interval == interval

def test_invalid_interval_negative():
    interval = random.randint(-sys.maxsize, -1)

    test_args = ['client.py', '--interval', str(interval)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = client.parse_args()

        assert sysexit.value.code == 2

def test_invalid_interval_zero():
    interval = 0

    test_args = ['client.py', '--interval', str(interval)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = client.parse_args()

        assert sysexit.value.code == 2

def test_invalid_interval_string():
    interval = "every 2 minutes"

    test_args = ['client.py', '--interval', str(interval)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = client.parse_args()

        assert sysexit.value.code == 2

## Test functions

# establish_connection()
def test_establish_connection_success(mock_logging_info, mock_socket):
    host = 'localhost'
    port = 12345
    client.establish_connection(mock_socket, host, port)

    mock_socket.connect.assert_called_once_with((host, port))
    mock_logging_info.assert_called_once_with(
        f"Successfully connected to {host}:{port}")

def test_establish_connection_refused(mock_logging_error, mock_sys_exit,
    mock_socket):
    mock_socket.connect.side_effect = ConnectionRefusedError("refused")

    client.establish_connection(mock_socket, 'localhost', 1234)

    mock_logging_error.assert_called_once()
    mock_sys_exit.assert_called_once_with(1)

# send_heartbeat()
def test_send_heartbeat_success(mock_logging_info, patched_time, mock_socket):
    client.send_heartbeat(mock_socket, 5)

    expected_msg = "Sequence #5: Sending heartbeat at 1752000000.6510. "
    mock_logging_info.assert_called_once_with(expected_msg)
    mock_socket.sendall.assert_called_once_with(expected_msg.encode('utf-8'))

def test_send_heartbeat_broken_pipe(mock_logging_error, mock_sys_exit,
    patched_time, mock_socket):
    mock_socket.sendall.side_effect = BrokenPipeError("pipe broke")

    client.send_heartbeat(mock_socket, 1)

    mock_logging_error.assert_called_once()
    mock_sys_exit.assert_called_once_with(1)


# start_heartbeat_loop()
@patch("client.send_heartbeat")
@patch("client.time.sleep", return_value=None)
def test_heartbeat_loop_runs_three_times(mock_sleep, mock_send, mock_socket):
    interval = 100  # milliseconds

    # Stop after 3 heartbeats using side effect
    def side_effect(*args, **kwargs):
        if mock_sleep.call_count == 3:
            raise SystemExit()

    mock_sleep.side_effect = side_effect

    with pytest.raises(SystemExit):
        client.start_heartbeat_loop(mock_socket, interval)

    # Check send_heartbeat was called with incrementing sequence numbers
    mock_send.assert_any_call(mock_socket, 1)
    mock_send.assert_any_call(mock_socket, 2)
    mock_send.assert_any_call(mock_socket, 3)
    assert mock_send.call_count == 3

    # Check time.sleep was called three times
    assert mock_sleep.call_count == 3
