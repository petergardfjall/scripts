#! /usr/bin/env python3

import argparse
import http.client
import logging
import json
import re
import sys
from urllib.parse import urlparse

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


PACKAGE_LINK = re.compile(r'<a href="[^"]+">([^<]+)</a>')
"""Pattern that matches a package link in the PyPi simple project API"""

class Response:
    def __init__(self, http_response):
        """
        http.client.HTTPResponse
        """
        self.headers = http_response.headers
        self.status = http_response.status
        self.reason = http_response.reason
        self.body = http_response.read().decode("utf-8")
        http_response.close()


def get(url):
    u = urlparse(url)
    conn = http.client.HTTPSConnection(u.netloc)
    try:
        conn.request("GET", u.path)
        resp = conn.getresponse()
        if resp.status in [301, 302]:
            LOG.debug("%s redirected: %d (%s): %s", u.netloc, resp.status, resp.reason, resp.headers["Location"])
            return get(resp.headers["Location"])
        return Response(resp)
    finally:
        conn.close()

def get_package_metadata(package_index, package, version=None):
    pkg_path = package
    if version:
        pkg_path += f"/{version}"

    return get(f"https://{package_index}/pypi/{pkg_path}/json")




def get_package_metadata_or_die(package_index, package, version=None):
    """Return a dict holding the metadata for a certain package."""
    resp = get_package_metadata(package_index, package, version)
    if resp.status != 200:
        LOG.error("pypi.org query failed: %d (%s)", resp.status, resp.reason)
        sys.exit(1)
    return json.loads(resp.body)

def list_packages_or_die(package_index):
    resp = get(f"https://{package_index}/simple")
    if resp.status != 200:
        LOG.error("pypi.org query failed: %d (%s)", resp.status, resp.reason)
        sys.exit(1)
    pkgs = []
    for line in resp.body.split('\n'):
        m = PACKAGE_LINK.match(line.lstrip())
        if m:
            pkgs.append(m.group(1))
    return pkgs

def sdist(args):
    """Implementation of the `sdist` subcommand."""
    pkg = get_package_metadata_or_die(args.package_index, args.package)
    for version, dists in pkg["releases"].items():
        if version == args.version:
            for dist in dists:
                if dist["packagetype"] == "sdist":
                    print(dist["url"])
                    break

def bdists(args):
    """Implementation of the `bdists` subcommand."""
    pkg = get_package_metadata_or_die(args.package_index, args.package)
    bdists = []
    for version, dists in pkg["releases"].items():
        if version == args.version:
            for dist in dists:
                if dist["packagetype"].startswith("bdist"):
                    bdists.append(dist)
    print(json.dumps(bdists, indent=4))


def versions(args):
    """Implementation of the `versions` subcommand."""
    pkg = get_package_metadata_or_die(args.package_index, args.package)
    print("\n".join(list(pkg["releases"].keys())))



def show(args):
    """Implementation of the `show` subcommand."""
    pkg = get_package_metadata_or_die(args.package_index, args.package, args.version)
    print(json.dumps(pkg, indent=4))

def list_packages(args):
    """Implementation of the `list` subcommand."""
    pkg = list_packages_or_die(args.package_index)
    print(json.dumps(pkg, indent=4))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetches python package metadata from a Python Package Index (PyPi by default).")
    parser.add_argument("--package-index", dest="package_index", default="pypi.org", help="Package Index to use.")
    parser.add_argument("--verbose", action='store_true', default=False, help="Print body in error responses.")

    subparsers = parser.add_subparsers(help="subcommands")

    list_cmd = subparsers.add_parser("list", help="List all PyPi package names")
    list_cmd.set_defaults(action=list_packages)

    show_cmd = subparsers.add_parser("show", help="Show all PyPi metadata for a package")
    show_cmd.add_argument(
        "package", help="The package to show information for. For example, 'jinja2'.")
    show_cmd.add_argument(
        "version", nargs='?', default=None, help="The package version to show information for. For example, '2.9.6'.")
    show_cmd.set_defaults(action=show)

    versions_cmd = subparsers.add_parser("versions", help="Show available versions for a package")
    versions_cmd.add_argument(
        "package", help="The package of interest. For example, 'jinja2'.")
    versions_cmd.set_defaults(action=versions)

    sdist_cmd = subparsers.add_parser("sdist", help="Show source (sdist) download URL for a package version")
    sdist_cmd.add_argument(
        "package", help="The package of interest. For example, 'jinja2'.")
    sdist_cmd.add_argument(
        "version", help="The package version of interest. For example, '2.9.6'.")
    sdist_cmd.set_defaults(action=sdist)

    bdists_cmd = subparsers.add_parser("bdists", help="Show binary distributions for a package version")
    bdists_cmd.add_argument(
        "package", help="The package of interest. For example, 'jinja2'.")
    bdists_cmd.add_argument(
        "version", help="The package version of interest. For example, '2.9.6'.")
    bdists_cmd.set_defaults(action=bdists)


    args = parser.parse_args()
    if not hasattr(args, "action"):
        print("please specify a subcommand (--help for usage)")
        sys.exit(1)

    args.action(args)
