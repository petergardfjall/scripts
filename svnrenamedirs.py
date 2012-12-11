#!/usr/bin/env python
"""
A deep svn rename operation that renames all directories with a certain name
in a directory tree that are located in directories whose path matches a given
pattern.
"""
import logging
import re
import optparse
import os
import sys


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()


if __name__ == "__main__":
    usage = """usage: %prog [options] <old-dir-name> <new-dir-name>
    
    A recursive svn rename operation that renames directories in a directory
    tree. All directories in the tree named <old-dir-name> will be
    renamed to <new-dir-name>.

    A path filter (see --pattern) can be used to further limit the set
    of directories that are considered for renaming.
    """
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--rootdir", dest="rootdir",
                  help="The directory where the tree search will start. "\
                    "Default: '.'", metavar="DIR", default=".")
    parser.add_option("--pattern", dest="pattern",
                  help="Only directories whose path matches this regular expression will "\
                      "be acted upon. Default: '.*$'", metavar="REGEXP", default=".*$")
    parser.add_option("--dryrun", dest="dryrun", action="store_true",
                      help="Don't carry out any changes.")

    (options, args) = parser.parse_args()
    if (len(args) < 2):
        parser.print_help()
        sys.exit(1)
    olddir = args[0]
    newdir = args[1]
    if options.dryrun:
        log.info("Dry-run mode: no changes are carried out.")
    log.info("Searching for directories whose path match '{0}' starting at '{1}'. " 
             "Any directory named '{2}' will be svn-renamed to '{3}'.".format(options.pattern, options.rootdir, olddir, newdir))
    for root, dirs, files in os.walk(options.rootdir):
        dirs = [ directory for directory in dirs if re.match(options.pattern, os.path.join(root, directory)) ]
        # ignore .svn (sub)directories
        dirs = [ directory for directory in dirs if not ".svn" in os.path.join(root, directory) ]        
        for dirname in dirs:
            dirpath = os.path.join(root, dirname)
            if olddir in os.listdir(dirpath):
                oldpath = os.path.join(dirpath, olddir)
                newpath = os.path.join(dirpath, newdir)
                move_command = "svn rename {0} {1}".format(oldpath, newpath)
                log.info(move_command)
                if not options.dryrun:
                    # carry out actual svn renaming 
                    exitcode = os.system(move_command)
                    if exitcode != 0:
                        log.error("error: failed to svn rename directory {0} to {1}".format(oldpath, newpath))
                        sys.exit(1)

    if options.dryrun:
        log.info("Dry-run mode: no changes were carried out.")

