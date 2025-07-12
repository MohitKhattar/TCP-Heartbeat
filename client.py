import sys
import time
import socket
import logging
import argparse

# Local import - Type check helpers
import helpers

def parse_args():
    parser = argparse.ArgumentParser(description="""Send a 'heartbeat' message
        over a TCP socket at regular intervals""")

    parser.add_argument('-ho', '--host', default='localhost',
        help='Destination Host IP for message')
    parser.add_argument('-p', '--port', default='6510',
        type=helpers.check_valid_port,
        help='Destination Port between 0 and 65535, inclusive')
    parser.add_argument('-i', '--interval', default='1000',
        type=helpers.check_positive_int,
        help='Interval at which to send heartbeat messages in milliseconds')

    return parser.parse_args()


def establish_connection(socket, host, port):
    try:
        # Tuple with host and port expected
        socket.connect((host, port))
        logging.info(f"Successfully connected to {host}:{port}")
    except ConnectionRefusedError as e:
        logging.error("Failed to connect to server. "
            f"Please make sure server is running on port {port}."
            f"\nError: {str(e)}")
        sys.exit(1)

def send_heartbeat(socket, sequence_num):
    data = (f"Sequence #{sequence_num}: Sending heartbeat at {time.time():.4f}. ")
    logging.info(data)

    try:
        socket.sendall(data.encode('utf-8'))  # Convert to bytes
    except (BrokenPipeError, ConnectionResetError) as e:
        logging.error("Failed to send heartbeat to server. "
            f"Server may have abruptly closed. \n Error: {str(e)}")
        sys.exit(1)

def start_heartbeat_loop(socket, interval):
    sequence_num = 0

    while True:
        sequence_num += 1
        send_heartbeat(socket, sequence_num)

        time.sleep(interval / 1000)  # Convert interval to seconds

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        establish_connection(s, args.host, args.port)

        start_heartbeat_loop(s, args.interval)
