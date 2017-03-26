#!/usr/bin/env python
"""
Replaces all occurences of a certain word with a replacement
word in files of an svn directory tree.

A file path filter (see --pattern) can be used to further limit the set of
files that are considered for renaming.
"""

import difflib
import filecmp
import logging
import re
import optparse
import os
import shutil
import sys


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()

def showdiff(file1, file2):
    with open(file1, "r") as f1:
        with open(file2, "r") as f2:
            diffrows = difflib.unified_diff(f1.readlines(), f2.readlines(), fromfile="before", tofile="after")
    for diffrow in diffrows:
        sys.stdout.write(diffrow)
    

def search_and_replace(filepath, searchfor, replacewith, options={}):
    copypath = filepath + ".copy"
    with open(filepath, "r") as reader:
        with open(copypath, "w") as writer:
            for line in reader:
                writer.write(line.replace(searchfor, replacewith))
    # if there is a diff: replace source with copy.
    if not filecmp.cmp(filepath, copypath):
        log.info("Modified {0}".format(filepath))
        if options.showdiffs:
            showdiff(filepath, copypath)
        if not options.dryrun:
            shutil.copy(copypath, filepath)
    os.remove(copypath)


def is_secret(dirpath):
    if dirpath == '/':
        return False
    dirname = os.path.basename(dirpath)
    parent = os.path.dirname(dirpath)
    return dirname.startswith('.') or is_secret(parent)


if __name__ == "__main__":
    usage = """usage: %prog [options] <search-for> <replace-with>

    Replaces all occurences of a certain word with a replacement
    word in files of a directory tree.

    A file path filter (see --pattern) can be used to further limit the set of
    files that are considered for renaming.
    """
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--rootdir", dest="rootdir",
                  help="The directory where the tree search will start. "\
                      "Default: ${PWD}", metavar="DIR",
                      default=os.environ["PWD"])
    parser.add_option("--pattern", dest="pattern",
                  help="Only files matching this regular expression will "\
                      "be acted upon. Default: '.*$' (process any file/dir except ones with leading '.')", metavar="REGEXP", default=r".*$")
    parser.add_option("--process-secret-dirs", action="store_true",
                      help="Include secret directories (whose name starts with a leading dot '.'). Default is to ignore secret dirs.")
    parser.add_option("--dryrun", dest="dryrun", action="store_true",
                      help="Don't carry out any changes.")
    parser.add_option("--showdiffs", dest="showdiffs", action="store_true",
                      help="Show differences between original files and "\
                      "updated files.")
    
    (options, args) = parser.parse_args()
    if (len(args) < 2):
        parser.print_help()
        sys.exit(1)
    searchfor = args[0]
    replacewith = args[1]
    if options.dryrun:
        log.info("Dry-run mode: no changes are carried out.")    
    log.info("Searching for files matching '{0}' starting at '{1}'. " 
             "Occurrences of '{2}' will be replaced with '{3}'.".format(options.pattern, options.rootdir, searchfor, replacewith))
    for currdir, dirs, files in os.walk(options.rootdir):
        if is_secret(currdir) and not options.process_secret_dirs:
            # ignore secret directory (leading '.')
            log.debug("ignoring secret directory %s", currdir)
            continue
        
        files = [ f for f in files if re.match(options.pattern, f) ]
      
        for dirfile in files:
            filepath = os.path.join(currdir, dirfile)
            log.debug(filepath)
            search_and_replace(filepath, searchfor, replacewith, options)
    
    if options.dryrun:
        log.info("Dry-run mode: no changes were carried out.")
