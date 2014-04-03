#!/usr/bin/env python
#
# A script that reads from stdin and prints the input back on stdout with
# all environment variables references resolved.
#

import os, sys
print os.path.expandvars(sys.stdin.read())