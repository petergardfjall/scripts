#!/usr/bin/env python
"""
Replaces all file name occurences of a certain word with a replacement
word in an svn directory tree.

This is essentially a recursive svn rename operation that renames all
files in a directory tree in order to replace all file name occurrences
of target word with a replacement word.

A file path filter (see --pattern) can be used to further limit the set of
files that are considered for renaming.
"""
import logging
import re
import optparse
import os
import sys


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()


if __name__ == "__main__":
    usage = """usage: %prog [options] <replace word> <replacement word>

    Replaces all file name occurences of a certain word with a replacement
    word in an svn directory tree.

    This is essentially a recursive svn rename operation that renames all
    files in a directory tree in order to replace all file name occurrences
    of target word with a replacement word.

    A file path filter (see --pattern) can be used to further limit the set of
    files that are considered for renaming.
    """
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--rootdir", dest="rootdir",
                  help="The directory where the tree search will start. "\
                    "Default: '.'", metavar="DIR", default=".")
    parser.add_option("--pattern", dest="pattern",
                  help="Only files whose path matches this regular expression will "\
                      "be acted upon. Default: '.*$'", metavar="REGEXP", default=".*$")
    parser.add_option("--dryrun", dest="dryrun", action="store_true",
                      help="Don't carry out any changes.")

    (options, args) = parser.parse_args()
    if (len(args) < 2):
        parser.print_help()
        sys.exit(1)
    replace_word = args[0]
    replacement_word = args[1]
    if options.dryrun:
        log.info("Dry-run mode: no changes are carried out.")
    log.info("Searching for files whose path match '{0}' starting at '{1}'. " 
             "Any file containing the word '{2}' will be svn-renamed to have "
             "all such occurences replaced with '{3}'.".format(options.pattern, options.rootdir, replace_word, replacement_word))
    for root, dirs, files in os.walk(options.rootdir):
        # get all files in tree matching the pattern
        files = [ f for f in files if re.match(options.pattern, os.path.join(root, f)) ]
        # ignore files under .svn directories
        files = [ f for f in files if not ".svn" in os.path.join(root, f) ]
        for filename in files:
            filepath = os.path.join(root, filename)
            if replace_word in filename:
                newpath = os.path.join(root, filename.replace(replace_word, replacement_word))
                rename_command = "svn rename {0} {1}".format(filepath, newpath)
                log.info(rename_command)
                if not options.dryrun:
                    # carry out actual svn renaming 
                    exitcode = os.system(rename_command)
                    if exitcode != 0:
                        log.error("error: failed to svn rename file {0} to {1}".format(filepath, newpath))
                        sys.exit(1)

    if options.dryrun:
        log.info("Dry-run mode: no changes were carried out.")

