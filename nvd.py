#! /usr/bin/env python3

import argparse
from datetime import datetime, timezone
import http.client
import logging
import json
import os
import sys
import time
import urllib.parse

LOG = logging.getLogger(__name__)
LOG_LEVEL = 'INFO'
if 'LOG_LEVEL' in os.environ:
    LOG_LEVEL = getattr(logging, os.environ['LOG_LEVEL'].upper())
LOG = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(message)s', stream=sys.stdout)

CVE_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
PAGE_SIZE = 2000
# Recommended in https://nvd.nist.gov/developers/api-workflows
PAGE_DELAY_SEC = 6

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
    u = urllib.parse.urlparse(url)
    conn = http.client.HTTPSConnection(u.netloc)
    try:
        LOG.debug("connecting to %s", u.geturl())
        conn.request("GET", u.geturl())
        resp = conn.getresponse()
        if resp.status in [301, 302]:
            LOG.debug("%s redirected: %d (%s): %s", u.netloc, resp.status, resp.reason, resp.headers["Location"])
            return get(resp.headers["Location"])
        return Response(resp)
    finally:
        conn.close()

def get_json(url):
    resp = get(url)
    if resp.status != 200:
        raise RuntimeError(f'request failed: {resp.status} ({resp.reason})')
    return json.loads(resp.body)


def get_cve_page(url, offset, page_size):
    """Retrieves a single result page for the query in the given URL."""
    paged_url=f'{url}&startIndex={offset}&resultsPerPage={page_size}'
    page = get_json(paged_url)
    LOG.debug('got page: %s', json.dumps(page,indent=2))
    has_more = (offset + page_size - 1) < page['totalResults']
    return page['vulnerabilities'], has_more


def all_cves(url, page_size=PAGE_SIZE):
    """Loads all vulnerability pages that match the query in the given URL."""
    cves = []
    offset = 0
    page_num = 0
    while True:
        page_num += 1
        LOG.debug("getting page %d ...", page_num)
        vulnerabilities, has_more  = get_cve_page(url, offset, page_size)
        cves += vulnerabilities
        if not has_more:
            break
        offset += page_size
        time.sleep(PAGE_DELAY_SEC)

    return cves

def pretty_json(value):
    return json.dumps(value, indent=2)

def get_cve(args):
    """Implementation of the `get` subcommand."""
    if not args.cve:
        raise ValueError('missing CVE ID')
    cves = all_cves(f'{args.cve_api_url}?cveId={args.cve}', page_size=args.page_size)
    print(pretty_json(cves))

def keyword_search(args):
    """Implementation of the `search` subcommand."""
    if not args.keyword:
        raise ValueError('missing keyword(s)')
    encoded_keywords = urllib.parse.quote(" ".join(args.keyword), safe='')
    cves = all_cves(f'{args.cve_api_url}?keywordSearch={encoded_keywords}', page_size=args.page_size)
    print(pretty_json(cves))

def list_cve_updates(args):
    """Implementation of the `search` subcommand."""
    if not args.since:
        raise ValueError('missing since')
    if not args.until:
        raise ValueError('missing until')

    since = datetime.strptime(args.since, '%Y-%m-%dT%H:%M:%S.%f').astimezone(tz=timezone.utc)
    until = datetime.strptime(args.until, '%Y-%m-%dT%H:%M:%S.%f').astimezone(tz=timezone.utc)
    encoded_since = urllib.parse.quote(since.strftime('%Y-%m-%dT%H:%M:%S.%f'), safe='')
    encoded_until = urllib.parse.quote(until.strftime('%Y-%m-%dT%H:%M:%S.%f'), safe='')
    cves = all_cves(f'{args.cve_api_url}?lastModStartDate={encoded_since}&lastModEndDate={encoded_until}', page_size=args.page_size)
    print(pretty_json(cves))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Fetches vulnerabilities (CVEs) from NVD's API.

See https://nvd.nist.gov/developers/vulnerabilities
""")
    parser.add_argument("--cve-api-url", dest="cve_api_url", default=CVE_API_URL, help="CVE API to use.")
    parser.add_argument("--page-size", type=int, default=PAGE_SIZE, help="Page size to use for pagination.")
    parser.add_argument("--verbose", action='store_true', default=False, help="Print body in error responses.")

    subparsers = parser.add_subparsers(help="subcommands")

    get_cmd = subparsers.add_parser("get", help="Retrieve a particular CVE.")
    get_cmd.add_argument("cve", help="CVE identifier. For example, CVE-1999-0095.")
    get_cmd.set_defaults(action=get_cve)

    list_updates_cmd = subparsers.add_parser("list-updates", help="List CVEs updated since a given time.")
    list_updates_cmd.add_argument("since", help="List CVE updates since this point in time (in local time). Format: 2006-01-02T15:04:05.999")
    list_updates_cmd.add_argument("--until", default=datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                                  help="The end time for the update query (in local time). Default: current time. Format: 2006-01-02T15:04:05.999")
    list_updates_cmd.set_defaults(action=list_cve_updates)

    search_cmd = subparsers.add_parser("search", help="Search for CVEs with matching keywords in its description.")
    search_cmd.add_argument("keyword", nargs="+", help="Keyword to search for (option can occur multiple times).")
    search_cmd.set_defaults(action=keyword_search)

    args = parser.parse_args()
    if not hasattr(args, "action"):
        print("please specify a subcommand (--help for usage)")
        sys.exit(1)

    args.action(args)
