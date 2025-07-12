import sys
import time
import socket
import logging
import argparse

# Local import - Type check helpers
import helpers

def parse_args():
    parser = argparse.ArgumentParser(description="Receive heartbeat from client")

    parser.add_argument('-p', '--port', default='6510',
        type=helpers.check_valid_port,
        help='Destination Port between 0 and 65535, inclusive')
    parser.add_argument('-d', '--debug', default=False, action='store_true',
        help='Enable debug logging')

    return parser.parse_args()

## Helpers

def substr_index_data_start(string, substr):
    index = string.find(substr)

    if index == -1:
        raise Exception(f"Substring {substr} not found in string {string}")

    return index + len(substr)  # Data starts after substr passed in

def get_seq_num(data):
    # Expected format: "Sequence #{seq_num}: Sending heartbeat at {timestamp}. "
    seq_num = data[substr_index_data_start(data, '#') : data.find(':')]
    return int(seq_num)

def get_timestamp(data):
    # Expected format: "Sequence #{seq_num}: Sending heartbeat at {timestamp}. "
    timestamp = data[substr_index_data_start(data, ' at ') : data.find('. ')]
    return float(timestamp)

## Helpers - End

def bind_socket_and_listen(socket, port):
    try:
        # Tuple with host and port expected
        socket.bind(('localhost', port))
    except PermissionError as e:
        logging.error(f"Failed to bind port {port} with "
            f"permission error ({str(e)}). Please try rerunning with sudo "
            "to use a priveleged port")
        sys.exit(1)

    socket.listen(1)

def receive_heartbeat(connection):
    bytes = connection.recv(1024)
    time_recvd = time.time()

    data = bytes.decode('utf-8')
    if not data:  # Connection likely closed by client
        logging.warning(f"No data received. Connection likely closed by client.")
        return data, time_recvd

    logging.info(f"Received data at {time_recvd:.4f}: '{data}'")

    return data, time_recvd

def analyze_heartbeat(data, last_seq_recvd, time_recvd):
    try:
        # Check if any messages were missed
        seq_num = get_seq_num(data)
        if seq_num > (last_seq_recvd+1):
            logging.warning("Missed heartbeat(s) with sequence number "
                f"{*range(last_seq_recvd+1, seq_num),}")

        # Measure delay between sending and receiving heartbeat
        time_sent = get_timestamp(data)
        duration_ms = (time_recvd - time_sent) * 1000
        logging.debug(f"Message took {duration_ms:.4f}ms to be received.")

        return seq_num
    except Exception as e:
        logging.warning(f"Failed to analyze heartbeat with data: {data}.\n"
            f"Error: {str(e)}")

        return last_seq_recvd


if __name__ == '__main__':
    args = parse_args()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        bind_socket_and_listen(s, args.port)

        while True:  # Continue running even if client closes connection
            logging.info(f"Awaiting connection from client on port "
                f"{args.port}...")
            last_seq_recvd = 0

            connection, client_addr = s.accept()

            with connection:
                logging.info(f"Accepted connection from {client_addr}")

                # Runs per heartbeat message received for established connection
                while True:
                    try:
                        data, time_recvd = receive_heartbeat(connection)
                        if not data:
                            break  # Connection broken. Await new connection

                        last_seq_recvd = analyze_heartbeat(data, last_seq_recvd,
                            time_recvd)


                    except Exception as e:
                        logging.error(f"Exception caught while receiving data: "
                            f"{str(e)}")
                        break
