#!/usr/bin/env python

import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Start our unittests')
    parser.add_argument('--path', help = 'sets the PYTHONPATH for the test')
    parser.add_argument('--test', help = 'sets the filename containing the tests to run')
    args = parser.parse_args()
    python_path = {"PYTHONPATH" : args.path}
    return subprocess.call(args=args.test, env=python_path)

if __name__ == '__main__':
    main()
