import sys
import time
import pytest
import random

from unittest.mock import MagicMock, patch

@pytest.fixture
def patched_time():
    time = 1752000000.6510
    with patch('time.time', return_value=time):
        yield time

@pytest.fixture
def mock_socket():
    return MagicMock()

@pytest.fixture
def mock_connection():
    return MagicMock()

@pytest.fixture
def mock_sys_exit():
    with patch("sys.exit") as mock_exit:
        yield mock_exit

@pytest.fixture
def mock_logging_error():
    with patch("logging.error") as mock_log:
        yield mock_log

@pytest.fixture
def mock_logging_warn():
    with patch("logging.warning") as mock_log:
        yield mock_log

@pytest.fixture
def mock_logging_info():
    with patch("logging.info") as mock_log:
        yield mock_log

@pytest.fixture
def mock_logging_debug():
    with patch("logging.debug") as mock_log:
        yield mock_log

@pytest.fixture
def valid_heartbeat_msg():
    seq_num = random.randint(1, sys.maxsize)
    # e.g. 1752269066.1234
    timestamp = f"{random.randint(1, int(time.time()))}.{random.randint(1, 9999):04}"

    message = f"Sequence #{seq_num}: Sending heartbeat at {timestamp}. "
    return seq_num, timestamp, message
