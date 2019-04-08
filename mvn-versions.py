#!/usr/bin/env python3

import argparse
import fileinput
import http.client
import json
import logging
import os
import re
import sys
import urllib.parse


LOG_LEVEL = logging.INFO
if "DEBUG_LOG" in os.environ:
    LOG_LEVEL= logging.DEBUG

logging.basicConfig(level=LOG_LEVEL, format="%(levelname)5s %(message)s", stream=sys.stderr)
LOG = logging.getLogger(__name__)


ARTIFACT_PURL = re.compile(r'pkg:maven/([^\/]+)/([^@\?#]+).*')
"""The regexp pattern that a maven purl should match. Can either include or
exclude the version. For example:

   pkg:maven/com.amazonaws/aws-java-sdk-lambda

or

   pkg:maven/com.amazonaws/aws-java-sdk-lambda@1.0.0
"""


def find_versions(group_id, artifact_id):
    """Find all available versions for a Maven artifact (if its available in Maven
    central)."""
    versions = []

    query = 'q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=10000&wt=json'.format(
        group_id=group_id, artifact_id=artifact_id)
    search_url = "/solrsearch/select?{query}".format(query=query)

    LOG.debug("searching: %s", search_url)
    conn = http.client.HTTPSConnection("search.maven.org")
    try:
        conn.request("GET", search_url)
        r = conn.getresponse()
        LOG.debug("%d: %s", r.status, r.reason)
        if r.status != 200:
            raise RuntimeError("GET failed: {}: {}".format(r.status, r.reason))
        data = json.loads(r.read())
        LOG.debug(json.dumps(data,indent=4))
        if not "docs" in data["response"] or len(data["response"]["docs"]) == 0:
            raise RuntimeError("no versions found for {}/{}".format(group_id, artifact_id))
        for artifact in data["response"]["docs"]:
            versions.append(artifact["v"])
    finally:
        conn.close()
    return versions


DESCRIPTION = """Reads maven purls (possibly without versions) from stdin, and for each maven
artifact in the input, determines all available versions for the maven artifact
(in Maven central) and outputs this list (as version-qualified purls) on stdout.

Sample execution:

    $ echo "pkg:maven/com.google.inject/guice" | ./mvn-versions.py
    pkg:maven/com.google.inject/guice@4.2.2
    pkg:maven/com.google.inject/guice@4.2.1
    pkg:maven/com.google.inject/guice@4.2.0
    pkg:maven/com.google.inject/guice@4.1.0
    pkg:maven/com.google.inject/guice@4.0
    pkg:maven/com.google.inject/guice@4.0-beta5
    pkg:maven/com.google.inject/guice@4.0-beta4
    pkg:maven/com.google.inject/guice@4.0-beta
    pkg:maven/com.google.inject/guice@3.0
    pkg:maven/com.google.inject/guice@3.0-rc3
    pkg:maven/com.google.inject/guice@2.0-no_aop
    pkg:maven/com.google.inject/guice@3.0-rc2
    pkg:maven/com.google.inject/guice@2.0
    pkg:maven/com.google.inject/guice@1.0

"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=DESCRIPTION)
    args = parser.parse_args()

    for line in fileinput.input():
        line = line.strip()
        if line == "" or line.startswith("#"):
            continue

        match = ARTIFACT_PURL.match(line)
        if match:
            group_id = match.group(1)
            artifact_id = match.group(2)
        else:
            LOG.error("invalid purl: %s", line)
            continue

        LOG.debug("finding versions for artifact: %s, %s", group_id, artifact_id)
        try:
            versions = find_versions(group_id, artifact_id)
        except Exception as e:
            LOG.error("failed to find versions for %s: %s", line, str(e))
            continue
            
        for v in versions:
            purl = "pkg:maven/{group_id}/{artifact_id}@{version}".format(
                group_id=group_id, artifact_id=artifact_id,
                version=v)
            sys.stdout.write(purl + "\n")
