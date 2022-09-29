#!/bin/bash

set -e

scriptname=$(basename ${0})

function print_usage() {
    echo "Delete an image from a remote docker registry."
    echo "NOTE: user must be logged in (via docker login) to the registry."
    echo ""
    echo "usage: ${scriptname} [OPTIONS] <registry> <image> <tag>"
    echo ""
    echo "For example:"
    echo "  ${scriptname} a.mydocker.com:5000 foobar/nginx 1.0.1"
    echo ""
    echo "Options:"
    echo "  --help               Prints help text."
}

function die_with_msg() {
    echo "error: ${1}"
    exit 1
}

show_tags=false
for arg in ${@}; do
    case ${arg} in
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

[ -z ${1} ] && print_usage && die_with_msg "a docker registry must be given"
[ -z ${2} ] && print_usage && die_with_msg "a docker image (repository) must be given"
[ -z ${3} ] && print_usage && die_with_msg "an image tag must be given"

registry="${1}"
image="${2}"
tag="${3}"

# try to find credentials for repo
source_creds=$(cat ~/.docker/config.json | jq -r --arg repo ${registry} '.auths | with_entries(select(.key | contains($repo))) | .[].auth')
if [ "${source_creds}" = "null" ]; then
    die_with_msg "error: no credentials found for ${registry} in ~/.docker/config.json"
fi

# base64 decode credentials
source_creds=$(echo ${source_creds} | base64 -d)

echo "[${scriptname}] checking existence of image https://${registry}/v2/${image}/manifests/${tag} ..."

# get image digest from remote registry
image_digest=$(curl --silent --head -H "Accept: application/vnd.docker.distribution.manifest.v2+json" https://${registry}/v2/${image}/manifests/${tag} | grep -i 'docker-content-digest' | awk '{print $2}' | tr -d '\r')
if [ -z ${image_digest} ]; then
    die_with_msg "failed to retrieve digest for image: https://${registry}/v2/${image}/manifests/${tag}"
fi

# delete image
echo "[${scriptname}] deleting image https://${registry}/v2/${image}/manifests/${image_digest} ..."
curl -sSL -X DELETE https://${registry}/v2/${image}/manifests/${image_digest}
echo "[${scriptname}] image deleted."
