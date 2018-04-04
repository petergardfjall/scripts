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
source_creds=$(cat ~/.docker/config.json | jq -r --arg registry ${registry} '.auths | with_entries(select(.key | contains($registry))) | .[].auth' | head -1)
if [ "${source_creds}" = "null" ]; then
    die_with_msg "error: no credentials found for ${registry} in ~/.docker/config.json"
fi

# base64 decode credentials
source_creds=$(echo ${source_creds} | base64 -d)
images=$(curl --silent --user ${source_creds} https://${registry}/v2/_catalog | jq -r '.repositories[]')
for image in ${images}; do
    tags=""
    if ${show_tags}; then
	tags=$(curl --silent --user ${source_creds} https://${registry}/v2/${image}/tags/list | jq -r --sort-keys '.tags[]' | xargs echo)
    fi
    echo "${image}: ${tags}"
done

