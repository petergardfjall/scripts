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
import xml.etree.ElementTree
import xml.dom.pulldom

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
    def __init__(self, repo, max_cache_age:int=3600):
        """Initialize an Archive.

        :keyword max_cache_age: If an already downloaded package list
          file is found older than this, it will be downloaded anew.
        """
        self.repo = repo.strip('/')
        self.max_cache_age = max_cache_age

    def repomd_url(self):
        """Return the repository URL for the repomd.xml file."""
        return f'{self.repo}/repodata/repomd.xml'

    def package_list_url(self):
        """Return the repository URL for the current primary.xml.gz package list
        (as indicated by the repomd.xml file)."""
        repomd_xml = self._get(self.repomd_url())
        repomd_root = xml.etree.ElementTree.fromstring(repomd_xml)

        primary_path = repomd_root.findall('./data[@type="primary"]/location', namespaces={'': 'http://linux.duke.edu/metadata/repo'})[0].attrib['href']
        return f'{self.repo}/{primary_path}'


    def package_list_cache_path(self):
        scheme = urlparse(self.package_list_url()).scheme + "://"
        path = self.package_list_url().lstrip(scheme)
        return os.path.join("/tmp", path)


    # def get_release_components(self):
    #     body = self._get(self._releases_url(), )
    #     for line in body.split("\n"):
    #         if line.startswith("Components: "):
    #             return line.split(":")[1].strip()

    def _get(self, url:str):
        LOG.debug("GETing %s ...", url)
        u = urlparse(url)
        conn = self._connect(u)
        try:
            conn.request("GET", u.path)
            resp = conn.getresponse()
            if not resp.status == 200:
                if resp.status in [301,302]:
                    redirect_url = str(resp.getheader('location'))
                    return self._get(redirect_url)
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
                if resp.status in [301,302]:
                    redirect_url = str(resp.getheader('location'))
                    self._download_to(redirect_url, dest_path)
                    return
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


    def download_package_list(self, dest_path :str):
        self._download_to(self.package_list_url(), dest_path)

    def list_packages(self):
        pkgs_file = self._update_package_list_cache()
        pkgs = []
        with gzip.open(pkgs_file, mode='rt', encoding='utf-8') as f:
            event_stream = xml.dom.pulldom.parse(f)
            for event, node in event_stream:
                if event == xml.dom.pulldom.START_ELEMENT and node.tagName == "package":
                    event_stream.expandNode(node)
                    # merge text nodes that are split into multiple child nodes
                    node.normalize()
                    name_elem = node.getElementsByTagName('name')[0]
                    v_elem = node.getElementsByTagName('version')[0]
                    arch_elem = node.getElementsByTagName('arch')[0]
                    pkg_name = name_elem.firstChild.nodeValue
                    pkg_version = f"{v_elem.attributes['ver'].value}-{v_elem.attributes['rel'].value}"
                    arch = arch_elem.firstChild.nodeValue
                    pkgs.append(f'{pkg_name}@{pkg_version}?arch={arch}')
        return pkgs

    def get_package(self, package_name:str):
        pkgs_file = self._update_package_list_cache()
        with gzip.open(pkgs_file, mode='rt', encoding='utf-8') as f:
            event_stream = xml.dom.pulldom.parse(f)
            for event, node in event_stream:
                if event == xml.dom.pulldom.START_ELEMENT and node.tagName == "package":
                    event_stream.expandNode(node)
                    # merge text nodes that are split into multiple child nodes
                    node.normalize()
                    name_elem = node.getElementsByTagName('name')[0]
                    pkg_name = name_elem.firstChild.nodeValue
                    if pkg_name == package_name:
                        return node.toprettyxml(indent='', newl='')
        return None

    def _update_package_list_cache(self) -> str:
        cache_path = self.package_list_cache_path()
        if not os.path.isfile(cache_path) or (file_age(cache_path) > self.max_cache_age):
            LOG.debug("downloading new packge list file to %s", cache_path)
            self.download_package_list(cache_path)
        else:
            LOG.debug("reusing cached %s (age: %d seconds)", cache_path, file_age(cache_path))
        return cache_path


def download_package_list(args):
    """Implementation of the `download-package-list` subcommand."""
    archive = Archive(repo=args.repo, max_cache_age=args.max_cache_age)
    archive.download_package_list(args.dest_path)


def list_packages(args):
    """Implementation of the `list-packages` subcommand."""
    archive = Archive(repo=args.repo, max_cache_age=args.max_cache_age)
    print(json.dumps(archive.list_packages(), indent=2))

def show_package(args):
    """Implementation of the `show-package` subcommand."""
    archive = Archive(repo=args.repo, max_cache_age=args.max_cache_age)
    print(archive.get_package(args.package))


DESCRIPTION="""
Download and inspect RPM package lists.

The LOG_LEVEL environment variable controls log output.

Examples:

    # download primary.xml.gz
    rpm-inspect.py --repo=http://mirror.centos.org/centos/7/os/x86_64 download-package-list --dest=centos-7-bin.xml.gz
    rpm-inspect.py --repo=https://vault.centos.org/7.9.2009/os/Source download-package-list --dest=centos-7-src.xml.gz

    # list packages
    rpm-inspect.py --repo=http://mirror.centos.org/centos/8/AppStream/x86_64/os/ list-packages

    # show a particular package
    rpm-inspect.py --repo=http://download.opensuse.org/tumbleweed/repo/src-oss show-package curl
"""

class MyHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,argparse.RawTextHelpFormatter):
    """Help text formatter which both outputs defaults when calling `--help` and
    also accepts newlines in the description text."""
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=MyHelpFormatter)
    parser.add_argument("--repo", default="https://mirror.nsc.liu.se/centos-store/8.4.2105/BaseOS/Source/", help="RPM repository such as `http://download.opensuse.org/tumbleweed/repo/oss` or `http://download.opensuse.org/tumbleweed/repo/src-oss`.")
    parser.add_argument("--verbose", action='store_true', default=False, help="Print body in error responses.")
    parser.add_argument("--max-cache-age", type=int, default=86400, help="Max cache age in seconds.")

    subparsers = parser.add_subparsers(help="subcommands")

    dl_packages_cmd = subparsers.add_parser("download-package-list", help="Download primary.xml.gz archive")
    dl_packages_cmd.add_argument("--dest", dest="dest_path", default="primary.xml.gz", help="Download destination.")
    dl_packages_cmd.set_defaults(action=download_package_list)


    list_packages_cmd = subparsers.add_parser("list-packages", help="List all packages found in the package list")
    list_packages_cmd.set_defaults(action=list_packages)

    show_package_cmd = subparsers.add_parser("show-package", help="Show a particular package found in the package list. Note: only the first occurence of a package is shown.")
    show_package_cmd.add_argument("package", help="Package name")
    show_package_cmd.set_defaults(action=show_package)


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
