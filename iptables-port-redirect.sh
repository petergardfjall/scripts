#!/bin/bash

#
# NOTE: if traffic from the outside towards <dest-port> still doesn't reach
# <redirect-port> factors outside of the iptables rules handled by this script
# might be at play. For example an external firewall or ufw dropping traffic to
# <dest-port>.
#

script=$(basename ${0})

function info {
    echo -e "\e[32minfo: ${1}\e[0m"
}

function warn {
    echo -e "\e[33mwarn: ${1}\e[0m"
}

function error {
    echo -e "\e[31merror: ${1}\e[0m"
}

function die {
    error "${1}"
    exit 1
}

function print_usage {
    echo "${script} {add|remove} <dest-port> <redirect-port>"
    echo ""
    echo "Add iptables rule(s) that will redirect any traffic intended"
    echo "for <dest-port> (for instance 80) to be rerouted to"
    echo "<redirect-port> (for instance 3000). The rule will not survive"
    echo "a reboot."
}

function is_root {
    [[ $(id -u) = 0 ]]
}

# Checks if a given rule exists.
# See `sudo iptables --list-rules [-t nat]`.
function iptables_rule_exists {
    iptables -C ${rule} > /dev/null 2>&1
    [[ "${?}" = "0" ]]
}

# Adds a given rule to the iptables. For example:
#   "PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3000"
function iptables_add_rule {
    rule="${1}"
    if iptables_rule_exists "${rule}"; then
        warn "rule already exists: \"${rule}\""
    else
        info "adding rule: \"${rule}\""
        iptables -A ${rule}
    fi
}

function iptables_delete_rule {
    rule="${1}"
    if ! iptables_rule_exists "${rule}"; then
        warn "rule does not exist: \"${rule}\""
    else
        info "deleting rule: \"${rule}\""
        iptables -D ${rule}
    fi
}

#
# main
#

operation="${1}"
if [ -z "${operation}" ]; then
    die "no operation given: want 'add' or 'remove'"
fi
if [[ "${operation}" != "add" ]] && [[ "${operation}" != "remove" ]]; then
    error "unknown operation: \"${operation}\" (want 'add' or 'remove')"
    print_usage
    exit 1
fi

dest_port="${2}"
redirect_port="${3}"

if [[ "${dest_port}" = "--help" ]] || [[ "${dest_port}" = "-h" ]]; then
    print_usage
    exit 0
fi

if [[ -z "${dest_port}" ]] || [[ -z "${redirect_port}" ]]; then
    error "missing port argument(s)"
    print_usage
    exit 1
fi

# TODO validate ports are positive integers

if ! is_root; then
    error "need to run with root privileges"
    exit 1
fi


#
# Allow internal access (for clients on this host going through loopback
# interface). This rule handles outgoing connections through loopback interface
# (localhost/127.0.0.1) as packets targeted for loopback interface do not pass
# through the PREROUTING chain.
#
internal_access_rule1="OUTPUT -t nat -p tcp -o lo --dport ${dest_port} -j REDIRECT --to-port ${redirect_port}"

#
# Allow external access (for clients outside this host).
#

# allow access to dest-port
ext_access_rule1="INPUT -p tcp --dport ${dest_port} -j ACCEPT"
# allow access to redirect-port
ext_access_rule2="INPUT -p tcp --dport ${redirect_port} -j ACCEPT"
# redirect packets from dest-port -> redirect-port
ext_access_rule3="PREROUTING -t nat -p tcp --dport ${dest_port} -j REDIRECT --to-port ${redirect_port}"


if [ "${operation}" = "add" ]; then
    iptables_add_rule "${internal_access_rule1}"
    iptables_add_rule "${ext_access_rule1}"
    iptables_add_rule "${ext_access_rule2}"
    iptables_add_rule "${ext_access_rule3}"
elif [ "${operation}" = "remove" ]; then
    iptables_delete_rule "${ext_access_rule3}"
    iptables_delete_rule "${ext_access_rule2}"
    iptables_delete_rule "${ext_access_rule1}"
    iptables_delete_rule "${internal_access_rule1}"
else
    die "unrecognized operation: \"${operation}\""
fi
