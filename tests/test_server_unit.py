import sys
import random
import pytest

from unittest.mock import patch

# Local import
import server

## Test args

# Port
def test_random_valid_port():
    port = random.randint(0, 65535)

    test_args = ['server.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        args = server.parse_args()
        assert args.port == port

def test_invalid_port_ge_max():
    port = random.randint(65536, sys.maxsize)
    test_args = ['server.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = server.parse_args()

        assert sysexit.value.code == 2

def test_invalid_port_le_min():
    port = random.randint(-sys.maxsize, -1)
    test_args = ['server.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = server.parse_args()

        assert sysexit.value.code == 2

def test_invalid_port_string():
    port = "Port of Subs"

    test_args = ['server.py', '--port', str(port)]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as sysexit:
            args = server.parse_args()

        assert sysexit.value.code == 2

# Debug logging
def test_debug_logging_set():
    test_args = ['server.py', '--debug']
    with patch.object(sys, 'argv', test_args):
        args = server.parse_args()
        assert args.debug == True

def test_debug_logging_unset():
    test_args = ['server.py']
    with patch.object(sys, 'argv', test_args):
        args = server.parse_args()
        assert args.debug == False


## Test functions

# substr_index_data_start()
def test_substr_index_start_valid():
    s = "Differentiable Swift"
    assert server.substr_index_data_start(s, "able ") == 15
    assert server.substr_index_data_start(s, "S") == 16

def test_substr_index_start_missing():
    s = "Millrock Dr"
    missing_substr = "Holladay"

    with pytest.raises(Exception, match=f"Substring {missing_substr} not found"):
        server.substr_index_data_start(s, missing_substr)

# get_seq_num()
def test_get_seq_num_valid(valid_heartbeat_msg):
    seq_num, timestamp, message = valid_heartbeat_msg
    assert server.get_seq_num(message) == seq_num

def test_get_seq_num_invalid_format():
    with pytest.raises(Exception, match=f"Substring # not found"):
        server.get_seq_num("Sending heartbeat at 1752265713.1532. ")

# get_timestamp()
def test_get_timestamp_valid(valid_heartbeat_msg):
    seq_num, timestamp, message = valid_heartbeat_msg
    assert server.get_timestamp(message) == float(timestamp)

def test_get_timestamp_incomplete_message():
    with pytest.raises(Exception, match=f"Substring  at  not found"):
        server.get_timestamp("Sequence #84121: Sending heartbea")

def test_get_timestamp_invalid_format():
    with pytest.raises(ValueError, match=f"could not convert string to float"):
        server.get_timestamp("Sending heartbeat at twenty minutes past noon. ")


# bind_socket_and_listen()
def test_bind_socket_permission_error(mock_logging_error, mock_sys_exit,
    mock_socket):
    mock_socket.bind.side_effect = PermissionError("Permission denied")

    server.bind_socket_and_listen(mock_socket, 80)

    mock_sys_exit.assert_called_once_with(1)
    mock_logging_error.assert_called_once()

def test_bind_socket_success(mock_socket):
    server.bind_socket_and_listen(mock_socket, 12345)

    mock_socket.bind.assert_called_once_with(('localhost', 12345))
    mock_socket.listen.assert_called_once_with(1)


# receive_heartbeat()
@patch("client.logging.info")
def test_receive_heartbeat_success(mock_log, valid_heartbeat_msg, patched_time,
    mock_connection):
    seq_num, timestamp, message = valid_heartbeat_msg

    mock_connection.recv.return_value = message.encode('utf-8')

    msg_recvd, time_recvd = server.receive_heartbeat(mock_connection)

    assert msg_recvd == message
    mock_log.assert_called_once_with(
        f"Received data at {patched_time:.4f}: '{message}'")
    assert time_recvd == patched_time

def test_receive_heartbeat_empty_data(mock_logging_warn, mock_connection):
    mock_connection.recv.return_value = b""

    msg_recvd, time_recvd = server.receive_heartbeat(mock_connection)

    assert msg_recvd == ""
    mock_logging_warn.assert_called_once_with(
        "No data received. Connection likely closed by client.")

# analyze_heartbeat()
def test_analyze_heartbeat_success(mock_logging_warn, mock_logging_debug,
    valid_heartbeat_msg):
    seq_num, timestamp, message = valid_heartbeat_msg

    time_recvd = float(timestamp) + 1  # 1s later
    last_seq = seq_num - 1

    result = server.analyze_heartbeat(message, last_seq, time_recvd)

    assert result == seq_num
    mock_logging_warn.assert_not_called()
    mock_logging_debug.assert_called_once_with(
        "Message took 1000.0000ms to be received.")

def test_analyze_heartbeat_with_missed_sequence(mock_logging_warn, mock_logging_debug,
    valid_heartbeat_msg):
    seq_num, timestamp, message = valid_heartbeat_msg

    last_seq = seq_num - random.randint(2, 200)  # Simulating missed heartbeats

    result = server.analyze_heartbeat(message, last_seq, float(timestamp))

    assert result == seq_num
    mock_logging_warn.assert_called_once_with(
        f"Missed heartbeat(s) with sequence number {*range(last_seq+1, seq_num),}")

def test_analyze_heartbeat_malformed_data(mock_logging_warn):
    bad_data = "No sequence info here"
    result = server.analyze_heartbeat(bad_data, 10, 1752000000.1234)

    assert result == 10
    mock_logging_warn.assert_called_once()
