#! /usr/bin/env python3

import argparse
from argparse import HelpFormatter, RawTextHelpFormatter
from datetime import datetime, timedelta
import gzip
import http.client
from io import StringIO
import logging
import json
import os
import re
import shutil
import sys
import tempfile
import traceback
import typing
from urllib.parse import urlparse

LOG_LEVEL = logging.INFO
if 'LOG_LEVEL' in os.environ:
    LOG_LEVEL = getattr(logging, os.environ['LOG_LEVEL'].upper())
LOG = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stdout)

def read_to(f :typing.IO[str], regexp :str) -> typing.Optional[str]:
    """Reads lines from a file until one is encountered with the given
    line_prefix or EOF is reached. The latter is indicated by a None return."""
    for line in f:
        if re.match(regexp, line):
            return line
    return None

def file_age(path :str) -> int:
    """Returns the age of a file in seconds."""
    delta = datetime.now() - datetime.fromtimestamp(os.stat(path).st_mtime)
    return delta.seconds

class Archive:
    def __init__(self, repo, dist, area, arch, max_cache_age:int=3600):
        """Initialize an Archive.

        :keyword max_cache_age: If an already downloaded Packages.gz/Sources.gz
          file is found older than this, it will be downloaded anew.
        """
        self.repo = repo.strip('/')
        self.dist = dist.strip('/')
        self.area = area.strip('/')
        self.arch = arch.strip('/')
        self.max_cache_age = max_cache_age

    def packages_url(self):
        return f'{self.repo}/dists/{self.dist}/{self.area}/binary-{self.arch}/Packages.gz'

    def sources_url(self):
        return f'{self.repo}/dists/{self.dist}/{self.area}/source/Sources.gz'

    def packages_cache_path(self):
        scheme = urlparse(self.packages_url()).scheme + "://"
        path = self.packages_url().lstrip(scheme)
        return os.path.join("/tmp", path)

    def sources_cache_path(self):
        scheme = urlparse(self.sources_url()).scheme + "://"
        path = self.packages_url().lstrip(scheme)
        return os.path.join("/tmp", path)

    def get_release_components(self):
        body = self._get(self._releases_url(), )
        for line in body.split("\n"):
            if line.startswith("Components: "):
                return line.split(":")[1].strip()

    def _releases_url(self):
        return f'{self.repo}/dists/{self.dist}/Release'

    def _get(self, url:str):
        LOG.debug("GETing %s ...", url)
        u = urlparse(url)
        conn = self._connect(u)
        try:
            conn.request("GET", u.path)
            resp = conn.getresponse()
            if not resp.status == 200:
                raise ValueError(f'http error: {resp.status}')
            return resp.read().decode("utf-8")
        finally:
            conn.close()

    def _download_to(self, url:str, dest_path:str):
        LOG.debug("downloading %s to %s ...", url, dest_path)
        path_dir = os.path.dirname(dest_path)
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)
        u = urlparse(url)
        conn = self._connect(u)
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

    def _connect(self, url):
        if url.scheme == 'http':
            conn = http.client.HTTPConnection(url.netloc)
        else:
            conn = http.client.HTTPSConnection(url.netloc)
        return conn


    def download_packages(self, dest_path :str):
        self._download_to(self.packages_url(), dest_path)

    def download_sources(self, dest_path :str):
        self._download_to(self.sources_url(), dest_path)

    def list_packages(self):
        pkgs_file = self._update_packages_cache()
        pkgs = []
        with gzip.open(pkgs_file, mode='rt', encoding='utf-8') as f:
            while True:
                line = read_to(f, '^Package: ')
                if line is None:
                    break
                pkg_name = re.match(r'^Package: (.*)$', line)[1]
                line = read_to(f, '^Version: ')
                if line is None:
                    break
                pkg_version = re.match(r'^Version: (.*)$', line)[1]
                pkgs.append(f'{pkg_name}@{pkg_version}')
            return pkgs

    def _update_packages_cache(self) -> str:
        pkgs_file = self.packages_cache_path()
        if not os.path.isfile(pkgs_file) or (file_age(pkgs_file) > self.max_cache_age):
            LOG.debug("downloading new Packages.gz file to %s", pkgs_file)
            self.download_packages(pkgs_file)
        else:
            LOG.debug("reusing cached %s (age: %d seconds)", pkgs_file, file_age(pkgs_file))
        return pkgs_file

    def get_pkg_paragraph(self, pkg :str) -> str:
        pkgs_file = self._update_packages_cache()

        buf = StringIO()
        with gzip.open(pkgs_file, mode='rt', encoding='utf-8') as f:
            line = read_to(f, f'^Package: {pkg}$')
            if line is None:
                raise ValueError(f'no such package: {pkg}')
            buf.write(line)
            for line in f:
                if not line.strip():
                    break
                buf.write(line)

        return buf.getvalue()

def download_packages_file(args):
    """Implementation of the `download-packages-file` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch, max_cache_age=args.max_cache_age)
    archive.download_packages(args.dest_path)


def download_sources_file(args):
    """Implementation of the `download-sources-file` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch, max_cache_age=args.max_cache_age)
    archive.download_sources(args.dest_path)

def components(args):
    """Implementation of the `components` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch, max_cache_age=args.max_cache_age)
    print(archive.get_release_components())

def list_packages(args):
    """Implementation of the `list-packages` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch, max_cache_age=args.max_cache_age)
    print(json.dumps(archive.list_packages(), indent=2))

def show_package(args):
    """Implementation of the `show-package` subcommand."""
    archive = Archive(repo=args.repo, dist=args.dist, area=args.area, arch=args.arch, max_cache_age=args.max_cache_age)
    print(archive.get_pkg_paragraph(args.package))


DESCRIPTION="""
Downloads apt repository archives.

The LOG_LEVEL environment variable controls log output.

Examples:

    # get Packages.gz
    apt-repo-dl.py --repo=http://dl.google.com/linux/chrome/deb --dist=stable packages
    # get Sources.gz
    apt-repo-dl.py --repo=http://archive.canonical.com/ubuntu --dist=focal --area=partner sources

    apt-repo-dl.py --repo=http://packages.microsoft.com/repos/code --dist=stable --area=main --arch=arm64 packages
"""

class MyHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,argparse.RawTextHelpFormatter):
    """Help text formatter which both outputs defaults when calling `--help` and
    also accepts newlines in the description text."""
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=MyHelpFormatter)
    parser.add_argument("--repo", default="https://ftp.debian.org/debian", help="APT repository such as `http://se.archive.ubuntu.com/ubuntu`.")
    parser.add_argument("--dist", default="stable", help="Distribution. For example `focal`, `stable` or `buster`.")
    parser.add_argument("--area", default="main", help="Archive area. For example, `main`, `contrib`, `non-free`.")
    parser.add_argument("--arch", default="amd64", help="Architecture (only relevant for binary packages). For example `i386`, `amd64`.")
    parser.add_argument("--verbose", action='store_true', default=False, help="Print body in error responses.")
    parser.add_argument("--max-cache-age", type=int, default=86400, help="Max cache age in seconds.")

    subparsers = parser.add_subparsers(help="subcommands")

    dl_packages_cmd = subparsers.add_parser("download-packages-file", help="Download Packages.gz archive")
    dl_packages_cmd.add_argument("--dest", dest="dest_path", default="Packages.gz", help="Download destination.")
    dl_packages_cmd.set_defaults(action=download_packages_file)

    dl_sources_cmd = subparsers.add_parser("download-sources-file", help="Download Sources.gz archive")
    dl_sources_cmd.add_argument("--dest", dest="dest_path", default="Sources.gz", help="Download destination.")
    dl_sources_cmd.set_defaults(action=download_sources_file)

    list_packages_cmd = subparsers.add_parser("list-packages", help="List all packages found in the Packages.gz archive")
    list_packages_cmd.set_defaults(action=list_packages)

    show_package_cmd = subparsers.add_parser("show-package", help="Show a particular package found in the Packages.gz archive")
    show_package_cmd.add_argument("package", help="Package name")
    show_package_cmd.set_defaults(action=show_package)

    components_cmd = subparsers.add_parser("components", help="Discover release components for a particular repo+distro.")
    components_cmd.set_defaults(action=components)

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
