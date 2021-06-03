#! /usr/bin/env python3

import argparse
from argparse import HelpFormatter, RawTextHelpFormatter
import http.client
import logging
import os
import shutil
import sys
import traceback
from urllib.parse import urlparse

LOG_LEVEL = logging.INFO
if 'LOG_LEVEL' in os.environ:
    LOG_LEVEL = getattr(logging, os.environ['LOG_LEVEL'].upper())
LOG = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(message)s')

class Archive:
    def __init__(self, repo, dist, area, arch):
        self.repo = repo.strip('/')
        self.dist = dist.strip('/')
        self.area = area.strip('/')
        self.arch = arch.strip('/')

    def packages_url(self):
        return f'{self.repo}/dists/{self.dist}/{self.area}/binary-{self.arch}/Packages.gz'

    def sources_url(self):
        return f'{self.repo}/dists/{self.dist}/{self.area}/source/Sources.gz'

    def _download_to(self, url:str, dest_path:str):
        u = urlparse(url)
        if u.scheme == 'http':
            conn = http.client.HTTPConnection(u.netloc)
        else:
            conn = http.client.HTTPSConnection(u.netloc)

        LOG.debug("downloading %s to %s ...", url, dest_path)
        try:
            conn.request("GET", u.path)
            resp = conn.getresponse()
            if not resp.status == 200:
                raise ValueError(f'http error: {resp.status}')
            with resp as src:
                with open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        finally:
            conn.close()

    def download_packages(self, dest_path :str):
        self._download_to(self.packages_url(), dest_path)

    def download_sources(self, dest_path :str):
        self._download_to(self.sources_url(), dest_path)


def packages(args):
    """Implementation of the `packages` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch)
    archive.download_packages(args.dest_path)


def sources(args):
    """Implementation of the `sources` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch)
    archive.download_sources(args.dest_path)



DESCRIPTION="""
Downloads apt repository archives.

The LOG_LEVEL environment variable controls log output.

Examples:

    # get Packages.gz
    apt-repo-dl.py --repo=http://dl.google.com/linux/chrome/deb --dist=stable packages
    # get Sources.gz
    apt-repo-dl.py --repo=http://dl.google.com/linux/chrome/deb --dist=stable sources


    apt-repo-dl.py --repo=http://packages.microsoft.com/repos/code --dist=stable --area=main --arch=arm64 packages
"""

class MyHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,argparse.RawTextHelpFormatter):
    """Help text formatter which both outputs defaults when calling `--help` and
    also accepts newlines in the description text."""
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=MyHelpFormatter)
    parser.add_argument("--repo", default="http://se.archive.ubuntu.com/ubuntu", help="APT repository such as `https://ftp.debian.org/debian`.")
    parser.add_argument("--dist", default="focal", help="Distribution. For example `stable` or `buster`.")
    parser.add_argument("--area", default="main", help="Archive area. For example, `main`, `contrib`, `non-free`.")
    parser.add_argument("--arch", default="amd64", help="Architecture (only relevant for binary packages). For example `i386`, `amd64`.")
    parser.add_argument("--verbose", action='store_true', default=False, help="Print body in error responses.")

    subparsers = parser.add_subparsers(help="subcommands")

    packages_cmd = subparsers.add_parser("packages", help="Download Packages.gz archive")
    packages_cmd.add_argument("--dest", dest="dest_path", default="Packages.gz", help="Download destination.")
    packages_cmd.set_defaults(action=packages)

    sources_cmd = subparsers.add_parser("sources", help="Download Sources.gz archive")
    sources_cmd.add_argument("--dest", dest="dest_path", default="Sources.gz", help="Download destination.")
    sources_cmd.set_defaults(action=sources)

    args = parser.parse_args()

    if not hasattr(args, "action"):
        print("please specify a subcommand (--help for usage)")
        sys.exit(1)

    try:
        args.action(args)
    except Exception as e:
        if args.verbose:
            traceback.print_exc()
        print(str(e))
        sys.exit(1)
