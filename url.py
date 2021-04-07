#!/usr/bin/env python

import argparse
import urllib.parse
import sys

def encode(args):
    print(urllib.parse.quote(args.value))

def decode(args):
    print(urllib.parse.unquote(args.url))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='URL manipulation tool')

    subparsers = parser.add_subparsers(help='Available sub-commands')
    encode_cmd = subparsers.add_parser('encode', help='URL-encode a value')
    encode_cmd.add_argument('value', help='Value to be URL-encoded')
    encode_cmd.set_defaults(action=encode)

    decode_cmd = subparsers.add_parser('decode', help='decode URL')
    decode_cmd.add_argument('url', help='URL to be decoded')
    decode_cmd.set_defaults(action=decode)

    args = parser.parse_args()

    if not hasattr(args, "action"):
        print("please specify a subcommand (--help for usage)")
        sys.exit(1)

    args.action(args)
