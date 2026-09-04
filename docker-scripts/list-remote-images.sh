#!/bin/bash

set -e

scriptname=$(basename ${0})

function print_usage() {
    echo "Lists all docker images in a remote registry."
    echo "NOTE: user must be logged in (via docker login) to the registry."
    echo ""
    echo "usage: ${scriptname} [OPTIONS] <registry>"
    echo ""
    echo "For example:"
    echo "  ${scriptname} a.mydocker.com:5000"
    echo ""
    echo "Options:"
    echo "  --show-tags          Show available tags for each image."
    echo "  --auth-token         A basic auth token to access the remote registry."
    echo "  --help               Prints help text."
}

function die_with_msg() {
    echo "error: ${1}"
    exit 1
}

show_tags=false
for arg in ${@}; do
    case ${arg} in
        --show-tags)
            show_tags=true
            ;;
        --auth-token=*)
            auth_token=${arg/*=/}
            ;;
        --help)
            print_usage
            exit 0
            ;;
        --*)
            die_with_msg "unrecognized option: ${arg}"
            ;;
        *)
            # assume only positional args left
            break
            ;;
    esac
    shift
done

if [[ $# -lt 1 ]]; then
    die_with_msg "a docker registry must be given"
fi
registry="${1}"

# try to find credentials for registry
if [ -z "${auth_token}" ]; then
    auth_token=$(cat ~/.docker/config.json | jq -r --arg registry ${registry} '.auths | with_entries(select(.key | contains($registry))) | .[].auth' | head -1)
    if [ -z "${auth_token}" ] || [ "${auth_token}" = "null" ]; then
        die_with_msg "no credentials found for ${registry} in ~/.docker/config.json (can also be supplied with --token)"
    fi
    # base64 decode credentials
    auth_token=$(echo ${auth_token} | base64 -d)
fi

images=$(curl --silent --user ${auth_token} https://${registry}/v2/_catalog | jq -r '.repositories[]')
for image in ${images}; do
    tags=""
    if ${show_tags}; then
        tags=$(curl --silent --user ${auth_token} https://${registry}/v2/${image}/tags/list | jq -r --sort-keys '.tags[]' | xargs echo)
    fi
    echo "${image}: ${tags}"
done
