#!/bin/bash

set -e

telepresence_bin="${telepresence_bin:-telepresence2}"

function info {
    echo -e "\e[32minfo: ${1}\e[0m"
}

function error {
    echo -e "\e[31merror: ${1}\e[0m"
}

function die {
    error "${1}"
    exit 1
}

# Note: we limit use of this to a kind cluster.
current_ctx="$(kubectl config current-context)"
if [[ "${current_ctx}" != *kind* ]]; then
    die "current kubectl context must contain 'kind', was: ${current_ctx}"
fi


# Make sure the `traffic-manager` is installed in the cluster. Allow
# intercepting pods with long-running init containers.
info "installing traffic-manager ..."
${telepresence_bin} helm upgrade --set timeouts.agentArrival=5m

# Connect laptop to traffic-manager
info "connecting to traffic-manager ..."
${telepresence_bin} connect

${telepresence_bin} status
info "telepresence ready."
