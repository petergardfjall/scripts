#!/usr/bin/env python

import argparse
import urllib.parse
import sys


def encode(args):
    print(urllib.parse.quote_plus(args.value))


def decode(args):
    print(urllib.parse.unquote_plus(args.url))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query parameter manipulation tool')

    subparsers = parser.add_subparsers(help='Available sub-commands')
    encode_cmd = subparsers.add_parser('encode', help='Query-escape a value')
    encode_cmd.add_argument('value', help='Value to be query-escaped.')
    encode_cmd.set_defaults(action=encode)

    decode_cmd = subparsers.add_parser('decode', help='Query-unescape a value')
    decode_cmd.add_argument('url', help='Value to be query-unescaped.')
    decode_cmd.set_defaults(action=decode)

    args = parser.parse_args()

    if not hasattr(args, "action"):
        print("please specify a subcommand (--help for usage)")
        sys.exit(1)

    args.action(args)
