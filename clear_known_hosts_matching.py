#!/usr/bin/env python

#
# Note: in order for this script to work you need to make
# sure that host names are written to your known_hosts file.
# This is accomplished by setting "HashKnownHosts no" in your
# /etc/ssh/ssh_config. Refer to 'man ssh_config' for details.
#

import logging
import re
import optparse
import os
import shutil
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()

if __name__ == "__main__":
    usage = """usage: %prog [options] <search-pattern>

    Removes all lines in $HOME/.ssh/known_hosts containing the given pattern."""
    parser = optparse.OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit(1)
    pattern = args[0]
    log.info("deleting all files with pattern '%s'" % pattern)
    known_hosts = "%s/.ssh/known_hosts" % (os.environ["HOME"])
    nonmatching_lines = ""
    num_matches = 0
    with open(known_hosts) as hostsfile:
        for line in hostsfile:
            if re.match(pattern, line) or (line.strip() == ""):
                num_matches = num_matches + 1
                continue
            nonmatching_lines += line
    with open(known_hosts, "w") as hostsfile:
        hostsfile.write(nonmatching_lines)
    log.info("Removed %d entries." % (num_matches))
    

