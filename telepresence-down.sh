#!/bin/bash

set -e

telepresence_bin="${telepresence_bin:-telepresence}"

function info {
    echo -e "\e[32minfo: ${1}\e[0m"
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

info "uninstalling all intercepts ..."
${telepresence_bin} uninstall --all-agents

info "uninstalling traffic-manager ..."
${telepresence_bin} helm uninstall || true

info "stopping local daemons ..."
${telepresence_bin} quit --stop-daemons

info "telepresence is now disabled."
