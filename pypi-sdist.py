#! /usr/bin/env python3

import argparse
import http.client
import logging
import json
import sys
from urllib.parse import urlparse

LOG = logging.getLogger(__name__)

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
            LOG.debug("pypi.org redirected: %d (%s): %s", resp.status, resp.reason, resp.headers["Location"])
            return get(resp.headers["Location"])
        return Response(resp)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Determines the source (sdist) download URL for a python package from metadata in a Python Package Index (PyPi by default).")
    parser.add_argument(
        "package", help="The package of interest. For example, 'jinja2'.")
    parser.add_argument(
        "version", help="The package version of interest. For example, '2.9.6'.")
    parser.add_argument("--package-index", dest="package_index", default="pypi.org", help="Package Index to use.")
    parser.add_argument("--verbose", action='store_true', default=False, help="Print body in error responses.")

    args = parser.parse_args()

    resp = get(f"https://{args.package_index}/pypi/{args.package}/json")
    if resp.status != 200:
        LOG.error("pypi.org query failed: %d (%s)", resp.status, resp.reason)
        if args.verbose:
            LOG.error("%s", resp.body)
        sys.exit(1)

    j = json.loads(resp.body)
    for version, dists in j["releases"].items():
        if version == args.version:
            for dist in dists:
                if dist["packagetype"] == "sdist":
                    print(dist["url"])
                    break
