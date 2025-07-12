import argparse

def check_positive_int(arg):
    try:
        val = int(arg)
        if val <= 0:
            raise argparse.ArgumentTypeError(f"{val} is not a positive integer")

        return val
    except ValueError:
        raise argparse.ArgumentTypeError(f"{arg} is not an integer")

def check_valid_port(arg):
    try:
        val = int(arg)
        if val < 0 or val > 65535:
            raise argparse.ArgumentTypeError(f"{val} is not a valid port "
                "between 0 and 65535")

        return val
    except ValueError:
        raise argparse.ArgumentTypeError(f"{arg} is not an integer")
