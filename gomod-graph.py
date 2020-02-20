#!/usr/bin/env python3

import argparse
import http.client
import logging
import json
import os.path
import re
import subprocess
import sys
from urllib.parse import urlparse

LOG_LEVEL = logging.WARN
if os.environ.get("LOG_LEVEL") == "DEBUG":
    LOG_LEVEL = logging.DEBUG

LOG = logging.getLogger(__name__)
logging.basicConfig(format="%(message)s", level=LOG_LEVEL, stream=sys.stdout)


class ModuleEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

class Module:
    def __init__(self, name, effective_version=None, desired_version=None):
        self.name = name
        # version that will be used in build (seen in 'go list -m all')
        self.effective_version = effective_version
        # version of module desired by a consuming module in 'go mod graph'
        self.desired_version = desired_version
        # module name -> module
        self.child_modules = {}

    def id(self):
        id = self.name
        if self.effective_version:
            id += "@" + self.effective_version
        return id

    def todict(self):
        return self.__dict__


def get_root_module(module_root_dir):
    """Return the name of the Go module with the specified root directory."""
    output = subprocess.check_output(["go", "list", "-m"], cwd=module_root_dir)
    return output.decode('utf-8').strip()


def get_effective_module_versions(module_root_dir):
    """Return the map of effective module versions included in the build for the Go
    module rooted at the specified directory. The function returns a map of
    module name -> version.

    """
    module_versions = {}

    # View final versions that will be used in a build for all direct and
    # indirect dependencies.
    output = subprocess.check_output(["go", "list", "-m", "all"],
                                     cwd=module_root_dir)
    lines = output.decode('utf-8')
    for line in lines.split("\n"):
        m = re.match(r'(\S+)\s*(\S+)?', line)
        if m:
            mod_name = m.group(1)
            mod_version = m.group(2)
            module_versions[mod_name] = mod_version

    return module_versions


def build_module_graph(module_root_dir, effective_module_versions):
    """Return a map of modules (and their dependencies) by parsing module
    connections from 'go mod graph'.

    :param module_root_dir: Directory containing go.mod
    :param effective_module_versions: Map of effective module versions used in
      build: `<mod name> -> <effective module version>`.
    """

    module_map = {}

    # Each line in the output has two fields: the first column is a consuming
    # module, and the second column is one of that module's requirements
    # (including the version required by that consuming module). Note that not
    # all of these dependencies are included in the build; some versions are
    # ones desired by a consuming module. Those effective module versions that
    # are actually included in the build are found from 'go list -m all'.
    output = subprocess.check_output(["go", "mod", "graph"],
                                     cwd=module_root_dir)
    lines = output.decode('utf-8')
    for line in lines.split("\n"):
        # parse out entries of form:
        #   github.com/rs/zerolog github.com/zenazn/goji@v0.9.0
        #   github.com/cespare/xxhash@v1.0 github.com/OneOfOne/xxhash@v1.2
        m = re.match(r'(\S+?(@\S+)?) (\S+@\S+)', line)
        if m:
            parent_module_id = m.group(1)
            child_module_id = m.group(3)
            if not parent_module_id in module_map:
                mod_name = parent_module_id.split("@")[0]
                mod_version = m.group(2)
                module_map[parent_module_id] = Module(mod_name, desired_version=mod_version, effective_version=effective_module_versions[mod_name])
            if not child_module_id in module_map:
                mod_name = child_module_id.split("@")[0]
                mod_version = child_module_id.split("@")[1]
                module_map[child_module_id] = Module(mod_name,  desired_version=mod_version, effective_version=effective_module_versions[mod_name])

            parent_module = module_map[parent_module_id]
            child_module = module_map[child_module_id]
            parent_module.child_modules[child_module_id] = child_module

    return module_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Determine a module dependency graph for a Go module.")
    parser.add_argument(
        "--module-root", dest="module_root", default=".", help="The root directory of the Go module to analyze.")
    args = parser.parse_args()


    args = parser.parse_args()
    if not os.path.isdir(args.module_root):
        raise ValueError(f"module root directory does not exist: {args.module_root_dir}")


    # <mod name> -> version map of effective versions used in build
    effective_module_versions = get_effective_module_versions(args.module_root)

    # <name>@<version> -> Module map of all encountered modules in module graph
    module_map = build_module_graph(args.module_root, effective_module_versions)
    root_module_name = get_root_module(args.module_root)

    print(json.dumps(module_map[root_module_name], cls=ModuleEncoder, indent=4))
