# TCP Heartbeat Client-Server

This project implements a simple TCP client-server system in Python where:

- The **client** sends periodic heartbeat messages with a sequence number and timestamp.
- The **server** receives and logs these heartbeats, and analyzes them for delay and missed messages.

---


## Project Structure
```
├── client.py              # TCP client that sends heartbeat messages
├── server.py              # TCP server that receives and analyzes heartbeats
├── helpers.py             # Shared utility functions for validating arguments
├── tests/
│ ├── conftest.py          # Shared Fixtures for tests
│ ├── test_server_unit.py  # Unit tests for server logic
│ ├── test_client_unit.py  # Unit tests for client logic
│ └── test_integration.py  # Integration tests for client-server
├── pytest.ini             # Configuration for pytest
├── LICENSE
└── README.md
```

## Requirements

### To run the application
- Python 3.8+

### To run tests
- Python 3.8+
- python3-venv
- python3-pip
- pytest


## Usage - Running the application

### 1. Clone the Repository

```bash
git clone https://github.com/MohitKhattar/TCP-Heartbeat.git
cd TCP-Heartbeat
```

### 2. Run the server in a terminal

To start the server on port 1234:
```bash
python3 server.py --port 1234
```
_If using a priveleged port (such as 123, 80), please run the server as root (e.g. with sudo)._


| Argument              | Description                                    | Default     |
|-----------------------|------------------------------------------------|-------------|
| `--port` / `-p`       | Port number to connect to (0-65535, inclusive) | `6510`      |
| `--debug` / `-d`      | Enable debug logging (analyze timing)          | `False`     |

_Note: No command-line arguments are required_

### 3. Run the client in another terminal

To start sending heartbeat messages over a TCP socket to the server listening on port 1234 every 100ms:
```bash
python3 client.py --port 1234 --interval 100
```

### Command-Line Arguments

| Argument              | Description                                    | Default     |
|-----------------------|------------------------------------------------|-------------|
| `--host` / `-ho`      | IP or hostname of the server (local or remote) | `localhost` |
| `--port` / `-p`       | Port number to connect to (0-65535, inclusive) | `6510`      |
| `--interval` / `-i`   | Time between heartbeats in milliseconds        | `1000` (1s) |


_Note: No command-line arguments are required_


## Example output

### Example client output
```
INFO:root:Successfully connected to localhost:1234
INFO:root:Sequence #1: Sending heartbeat at 1752356183.5769.
INFO:root:Sequence #2: Sending heartbeat at 1752356183.6781.
INFO:root:Sequence #3: Sending heartbeat at 1752356183.7790.
INFO:root:Sequence #4: Sending heartbeat at 1752356183.8798.
INFO:root:Sequence #5: Sending heartbeat at 1752356183.9805.
...
```

### Example server output
```
INFO:root:Awaiting connection from client on port 1234...
INFO:root:Accepted connection from ('127.0.0.1', 37506)
INFO:root:Received data at 1752356183.5778: 'Sequence #1: Sending heartbeat at 1752356183.5769. '
INFO:root:Received data at 1752356183.6788: 'Sequence #2: Sending heartbeat at 1752356183.6781. '
INFO:root:Received data at 1752356183.7796: 'Sequence #3: Sending heartbeat at 1752356183.7790. '
INFO:root:Received data at 1752356183.8803: 'Sequence #4: Sending heartbeat at 1752356183.8798. '
INFO:root:Received data at 1752356183.9811: 'Sequence #5: Sending heartbeat at 1752356183.9805. '
...
```

## Running Tests
This project uses `pytest` for testing.

### 1. Set up virtual environment

Please make sure to install python3-venv, if needed.

Once python3-venv is installed, run
```bash
python3 -m venv .venv
source .venv/bin/activate
```
to set up and activate the virtual environment.

### 2. Install pytest

Please make sure to install python3-pip, if not installed already.

Next, run
```bash
pip3 install pytest
```
to install the pytest library.

### 3. Run tests

To run tests, please navigate to the root directory of the project (`cd TCP-Heartbeat`) and run
```bash
pytest
```
to run all tests, or
```bash
pytest tests/test_client_unit.py
```
to run a particular set of tests (client unit tests, in the above example).

## Features
- Periodic heartbeat messages with sequence and timestamp
- Server-side delay and loss detection
- Unit and integration test coverage
- Configurable via command-line arguments

## Known Limitations / Future Improvements

### 1. No Acks sent by server or checked by client
- At the moment, the client will continue to send its heartbeat messages without checking for an acknowledgement from the server to make sure it was received and parsed.

### 2. Recovery from temporary firewall rule blocking transmission of heartbeats
- If a firewall rule is created blocking the server from listening to the heartbeats, then the client will continue sending its heartbeats without knowing that the server did not receive them.

- Once this firewall rule is removed, the server will receive all the heartbeat messages that were missed as a single data packet.

- The server will then parse the first missed heartbeat and ignore the rest. It will mark the rest of the heartbeat sequence numbers (all except the first in the large data packet) as "missed" and carry on as normal with the new heartbeats being sent live.

### 3. Two or more clients sending heartbeats at the same time
- If two or more clients send heartbeats to the server at the same time, then only the first client to establish the connection will have its heartbeats heard by the server.

- Once the first client stops sending its heartbeats, all of the second clients heartbeats (that were missed by the server until this point) will be received by the server at once as a single data packet.

- Just like in limitation #2, the server will parse the first heartbeat from the second client and ignore the rest. It will mark the rest of the heartbeat sequence numbers (all except the first) as "missed" and carry on as normal with the new heartbeats being sent live.


### 4. PyTest's Coverage analysis does not work well with the subprocess module
- Running `pytest` with coverage analysis (`--cov=<path>`) makes some tests fail.
- This likely has to do with subprocess and the way the `coverage` module interacts with multiple processes spawned using the subprocess module.


## License
This project is licensed under the MIT License. See [LICENSE](https://github.com/MohitKhattar/TCP-Heartbeat/blob/main/LICENSE) for details.
