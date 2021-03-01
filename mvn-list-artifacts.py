#!/usr/bin/env python

"""List maven artifacts found in a certain category on mvnrepository.com

"""
import argparse
import http.client
import logging
import math
import os
import re
import sys
from html.parser import HTMLParser


LOG_LEVEL = logging.INFO
if "LOG_DEBUG" in os.environ:
    LOG_LEVEL = logging.DEBUG

logging.basicConfig(
    level=LOG_LEVEL,
    format=("%(asctime)s [%(levelname)s] "
            "[%(threadName)s:%(name)s:%(funcName)s:%(lineno)d] "
            "%(message)s"),
    stream=sys.stdout)

LOG = logging.getLogger(__name__)


category_pages = {
    'popular': 'popular',
    'aop-programming': 'open-source/aop-programming',
    'cache-implementations': 'open-source/cache-implementations',
    'cloud-computing-integration': 'open-source/cloud-computing-integration',
    'core-utilities': 'open-source/core-utilities',
    'collections': 'open-source/collections',
    'command-line-parsers': 'open-source/command-line-parsers',
    'date-time-utilities': 'open-source/date-time-utilities',
    'dependency-injection': 'open-source/dependency-injection',
    'eclipse-runtime': 'open-source/eclipse-runtime',
    'http-clients': 'open-source/http-clients',
    'io-utilities': 'open-source/io-utilities',
    'json-libraries': 'open-source/json-libraries',
    'logging-frameworks': 'open-source/logging-frameworks',
    'message-queue-clients': 'open-source/message-queue-clients',
    'object-serialization': 'open-source/object-serialization',
    'orm': 'open-source/orm',
    'testing-frameworks': 'open-source/testing-frameworks',
    'transactions': 'open-source/transactions',
    'web-apps': 'open-source/web-apps',
    'web-frameworks': 'open-source/web-frameworks',
    'web-servers': 'open-source/web-servers',

}



class ArtifactPageParser(HTMLParser):
    """Parses out artifacts from a mvnrepository.com web page."""

    def __init__(self):
        super().__init__()
        self._artifacts = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            LOG.debug('a tag: %s', attrs)
            for (attr, val) in attrs:
                if attr == 'href':
                    m = re.match(r'^/artifact/([^/]+)/([^/]+)$', val)
                    if m:
                        group_id = m.group(1)
                        artifact_id = m.group(2)
                        self._artifacts.add(f'{group_id}/{artifact_id}')

    def get_artifacts(self):
        return self._artifacts


def artifacts_get(category, page_num):
    """Retrieve all artifacts from mvnrepository.com/popular on the given page."""

    conn = http.client.HTTPSConnection("mvnrepository.com")
    try:
        path = category_pages[category]
        conn.request("GET", f'/{path}?p={page_num}')
        r = conn.getresponse()
        if r.status == 404 and page_num > 1:
            # assume we've moved passed pagination end
            return []

        if r.status != 200:
            raise RuntimeError("GET failed: {}: {}".format(r.status, r.reason))
        parser = ArtifactPageParser()
        parser.feed(r.read().decode('utf-8'))
        return parser.get_artifacts()
    finally:
        conn.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="List Maven projects by popularity.")
    parser.add_argument("--artifacts", metavar="<NUM>", type=int, default=100,
                        help="Number of artifacts to load (10 projects per page).")
    parser.add_argument('--category', choices=list(category_pages.keys()),
                        type=str, default='popular',
                        help='The mvnrepository.com category to list.')

    args = parser.parse_args()

    # ten artifacts are listed per page.
    num_pages = int(math.ceil(args.artifacts / 10))
    for page in range(1, num_pages + 1):
        artifacts = artifacts_get(args.category, page)
        if not artifacts:
            sys.exit(0)
        for artifact in artifacts:
            print(artifact)
