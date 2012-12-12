#! /usr/bin/env python

"""
Searches a file for all occurences of a regular expression (with at least
one capture group) and outputs a particular capture group for each line
that matches the regular expression.
"""

import logging
import optparse
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()

if __name__ == "__main__":
    usage = """usage: %prog [options] <capture-regexp> <capture-group> FILE

    Searches a file for all occurences of <capture-regexp> and for each
    match the capture group with number <capture-group> is output.

    Example:
    
      Search for occurences of 'id=\"...\"' in a file:
      
        %prog '.*(id=\"\S+\").*' 1 file.xml
    """
    parser = optparse.OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    if (len(args) < 3):
        parser.print_help()
        sys.exit(1)
    capture_regexp = re.compile(args[0])
    capture_group_number = int(args[1])
    filepath = args[2]
    if capture_group_number > capture_regexp.groups:
        log.error("capture-group number (%d) is greater than number of capture groups in the capture-regexp (%d)" % (capture_group_number, capture_regexp.groups))
        parser.print_help()
        sys.exit(1)
    
    log.info("Looking for lines matching regular expression: %s" % capture_regexp.pattern)
    log.info("Capture group to output: %d" % capture_group_number)

    with open(filepath, "r") as f:
        for line in f:
            match = capture_regexp.match(line)
            if match:
                print match.group(capture_group_number)
