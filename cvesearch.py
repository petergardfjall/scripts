#!/usr/bin/env python3

import argparse
import http.client
import json
import logging
import os
import sys
import urllib.parse

LOG_LEVEL = logging.INFO
if "DEBUG_LOG" in os.environ:
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger(__name__)

DESCRIPTION ="""Searches CVEs via the https://cve.circl.lu/api."""

def get_json(url):
    LOG.debug("getting: %s", url)
    url = urllib.parse.urlparse(url)

    conn = http.client.HTTPSConnection(url.netloc)
    try:
        conn.request("GET", url.path)
        r = conn.getresponse()
        LOG.debug("%d: %s", r.status, r.reason)
        if r.status != 200:
            raise RuntimeError("GET failed: {}: {}".format(r.status, r.reason))
        return json.loads(r.read())
    finally:
        conn.close()


def vendor_list(args):
    data = get_json("https://cve.circl.lu/api/browse/")
    print(json.dumps(data, indent=4))


def vendor_products(args):
    data = get_json("https://cve.circl.lu/api/browse/{}".format(args.vendor))
    print(json.dumps(data, indent=4))


def cve_byvp(args):
    """Search CVEs by vendor and product."""
    data = get_json("https://cve.circl.lu/api/search/{v}/{p}".format(
        v=args.vendor, p=args.product))
    print(json.dumps(data, indent=4))


def cve_byid(args):
    """Search CVEs by ID (CVE-2016-3333)."""
    data = get_json("https://cve.circl.lu/api/cve/{id}".format(id=args.id))
    print(json.dumps(data, indent=4))

def cve_bycpe(args):
    """Search CVEs by CPE (cpe:2.3:a:vmware:springsource_spring_framework:*:*:*:*:*:*:*:*)."""
    data = get_json("https://cve.circl.lu/api/cvefor/{cpe}".format(cpe=args.cpe))
    print(json.dumps(data, indent=4))


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    subparsers = parser.add_subparsers()

    vendor_list_parser = subparsers.add_parser("vendor-list", help="list all vendors")
    vendor_list_parser.set_defaults(func=vendor_list)

    vendor_show_parser = subparsers.add_parser("vendor-products", help="list products for a vendor")
    vendor_show_parser.add_argument("vendor", help="The vendor to browse")
    vendor_show_parser.set_defaults(func=vendor_products)

    cve_byvp_parser = subparsers.add_parser("cve-byvp", help="list CVEs for a vendor/product pair")
    cve_byvp_parser.add_argument("vendor", help="The vendor to search for.")
    cve_byvp_parser.add_argument("product", help="The product to search for.")
    cve_byvp_parser.set_defaults(func=cve_byvp)

    cve_byid_parser = subparsers.add_parser("cve-byid", help="show a particular CVE.")
    cve_byid_parser.add_argument("id", metavar="cve-id", help="The CVE id (such as CVE-2016-3333).")
    cve_byid_parser.set_defaults(func=cve_byid)

    cve_bycpe_parser = subparsers.add_parser("cve-bycpe", help="list CVEs for a CPE.")
    cve_bycpe_parser.add_argument("cpe", metavar="cpe", help="The CPE URI (such as cpe:2.3:a:vmware:springsource_spring_framework:*:*:*:*:*:*:*:*).")
    cve_bycpe_parser.set_defaults(func=cve_bycpe)

    args = parser.parse_args()
    if not "func" in args:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
