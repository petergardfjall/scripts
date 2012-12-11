#!/usr/bin/env python
"""
    A simple program that downloads a bunch of files from an FTP directory.
    By default, all files in the target directory are downloaded but a
    regexp filter can be passed to allow cherry-picking of files.
"""
import ftplib
from ftplib import FTP
import logging
import optparse
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger()

if __name__ == "__main__":
    usage = "usage: %prog [options] <ftp directory path>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--filter", dest="filter",
                  help="File name regular expression that will "\
                      "be used as filter on the files in the target "\
                      "directory. Default: '.*'",
                      metavar="REGEXP", default=".*")
    (options, args) = parser.parse_args()
    if (len(args) < 1):
        parser.print_help()
        sys.exit(1)
    
    baseurl = "ftp://ita.ee.lbl.gov/traces/WorldCup/"
    baseurl = baseurl.replace("ftp://", "")
    (host, path) = baseurl.split("/", 1)
    logger.info("Connecting to FTP server {0}".format(host))
    ftp = FTP(host)
    ftp.login()
    logger.info("Changing directory to {0}".format(path))
    ftp.cwd(path)
    files = ftp.nlst()
    matching_files = [f for f in files if re.match(options.filter, f)]
    logger.debug("The following files in {0} matched filter '{1}':\n  {2}".format(path, options.filter, "\n  ".join(matching_files)))
    for file_to_download in matching_files:
        logger.info("Downloading {0} ...".format(file_to_download))
        ftp.retrbinary(
            "RETR {0}".format(file_to_download),
            open(file_to_download, 'wb').write
        )
    ftp.quit()
    logger.info("Done.")


    
