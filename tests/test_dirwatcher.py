#!/usr/bin/env python

import unittest
import errno
import os
import argparse
from datetime import datetime as dt
import logging.handlers
import logging
import time
import signal

__author__ = 'Ken Stephens'

logger = logging.getLogger(__file__)
files = {}
exit_flag = False
def watch_dir(args):
    """
    Look at the directory that you're watching
    Get a list of files
    Add files to files dictionary if they're not already in it
    Log a message if you're adding something to dictionary that's not already there--log as a new file
    Look through files dictionary and compare that to the list of files in the directory
    If file is not in your dictionary anymore you have to log that you removed the file from your dictionary
    """
    logger.info('Watching directory: {}, File Extension: {}, Polling Interval: {}, Magic Text: {}'.format(
        args.path, args.ext, args.interval, args.magic
    ))
    file_list = os.listdir(args.path)
    for f in file_list:
        if f.endswith(args.ext) and f not in files:
            files[f] = 0
            logger.info(f"{f} added to watchlist.")
    for f in list(files):
        if f not in file_list:
            logger.info(f"{f} removed from watchlist.")
            del files[f]
    for f in files:
        files[f] = find_magic(
            os.path.join(args.path, f),
            files[f],
            args.magic
        )

def find_magic(filename, starting_line, magic_word):

    line_number = 0
    with open(filename) as f:
        for line_number, line in enumerate(f):
            if line_number >= starting_line:
                if magic_word in line:
                    logger.info(
                        f"This file: {filename} found:  {magic_word} on line: {line_number + 1}"
                    )
    return line_number + 1
def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped here as well (SIGHUP?)
    Basically it just sets a global flag, and main() will exit it's loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    # Logs associated signal name (New way)
    logger.warn('Received ' + signal.Signals(sig_num).name)
    # Logs associated signal name (the python2 way)
    signames = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                    if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.warn('Received ' + signames[sig_num])
    global exit_flag
    exit_flag = True
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--ext', type=str, default='.txt',
                        help='Text file extension to watch')
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='Number of seconds between polling')
    parser.add_argument('path', help='Directory path to watch')
    parser.add_argument('magic', help='String to watch for')
    return parser
def main():
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d-%Y &%H:%M:%S'
    )
    logger.setLevel(logging.DEBUG)
    app_start_time = dt.now()
    logger.info(
        '\n'
        '-------------------------------------------------\n'
        '   Running {0}\n'
        '   Started on {1}\n'
        '-------------------------------------------------\n'
        .format(__file__, app_start_time.isoformat())
    )
    parser = create_parser()
    args = parser.parse_args()
    # Connect these two signals from the OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # signal_handler will get called if OS sends either of these
    while not exit_flag:
        try:
            # Call to watch_dir Function
            watch_dir(args)
        except OSError as e:
            # UNHANDLED exception
            # Log an ERROR level message here
            if e.errno == errno.ENOENT:
                logger.error(f"{args.path} directory not found")
                time.sleep(2)
            else:
                logger.error(e)
        except Exception as e:
            logger.error(f"UNHANDLED EXCEPTION:{e}")
            # Sleeps while loop so cpu usage isn't at 100%
        time.sleep(int(float(args.interval)))
    # Final exit point
    # Logs a message that program is shutting down
    # Overall uptime since program start
    uptime = dt.now() - app_start_time
    logger.info(
        '\n'
        '-------------------------------------------------\n'
        '   Stopped {}\n'
        '   Uptime was {}\n'
        '-------------------------------------------------\n'
        .format(__file__, str(uptime))
    )
    logging.shutdown()
if __name__ == "__main__":
    main()