#!/bin/bash

set -e

scriptname=$(basename ${0})

function log() {
    level=${1}
    msg=${2}
    case ${level} in
        debug|DEBUG)
            # bold
            echo -en "\e[1m"
            ;;
        info|INFO)
            # green
            echo -en "\e[32m"
            ;;
        warn|WARN)
            # yellow
            echo -en "\e[33m"
            ;;
        error|ERROR)
            # red
            echo -en "\e[31m"
            ;;
    esac

    echo -en "[${scriptname}] ${msg}"
    echo -e "\e[0m"
}

function print_usage() {
    echo "Copies docker images from a source registry to a destination"
    echo "registry."
    echo
    echo "NOTE: you must be logged in (via docker login) to both source and "
    echo "destination registry. The images (and tags) to copy are given "
    echo "on stdin (see below)."
    echo ""
    echo "usage: ${scriptname} [OPTIONS] <source-registry> <dest-registry>"
    echo ""
    echo "For example:"
    echo "  cat images.txt | ${scriptname} a.mydocker.com:5000 123456789012.dkr.ecr.eu-west-2.amazonaws.com"
    echo ""
    echo "where images.txt may contain content similar to:"
    echo "  myorg/gateway:  latest v1.0.0"
    echo "  myorg/kafka:    latest v2.0.0"
    echo "  myorg/frontend: v1.1.0"
    echo "  ..."
    echo ""
    echo "Each row is a docker image followed by a colon and a list of tags"
    echo "to copy from the source registry to the destination registry. An"
    echo "image will be pulled from the source registry before pushing to the"
    echo "destination registry IF an image is found in the source registry that"
    echo "is more recent than the local image (or if no local image exists)."
    echo ""
    echo "Options:"
    echo "  --help               Prints help text."
}

function die_with_msg() {
    log error "error: ${1}"
    exit 1
}

for arg in ${@}; do
    case ${arg} in
        --loglevel=*)
            log_level=${arg#*=}
            exit 0
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

if [[ $# -lt 2 ]]; then
    die_with_msg "both a source registry and a destination registry must be given"
fi
source_registry=${1}
dest_registry=${2}

# try to find credentials for registry
source_creds=$(cat ~/.docker/config.json | jq -r --arg reg ${source_registry} '.auths | with_entries(select(.key | contains($reg))) | .[].auth')
if [ "${source_creds}" = "null" ]; then
    die_with_msg "error: no credentials found for ${source_registry} in ~/.docker/config.json"
fi
# base64 decode credentials
source_creds=$(echo ${source_creds} | base64 -d)

# hold skipped images
skipped=""
log debug "reading images to transfer from stdin ..."
while read image_and_tags; do
    if echo ${image_and_tags} | egrep -q '^\s*#' ; then
        # ignore lines starting with #
        continue
    fi
    image=$(echo ${image_and_tags} | awk -F: '{ print $1 }')
    tags=$(echo ${image_and_tags} | awk -F: '{ print $2 }')
    for tag in ${tags}; do
        log info "about to transfer docker image ${image}:${tag} ..."

        # find out if a local image exists and, if so, how old it is
        qualified_image=${source_registry}/${image}:${tag}
        if docker inspect ${qualified_image} > /dev/null 2>&1; then
            log debug "local image found: ${qualified_image}"
            local_created_at=$(docker inspect ${qualified_image} | jq -r '.[0].Created')
            log debug "local created at: ${local_created_at}"
        else
            log debug "no local image found: ${qualified_image}"
        fi

        # find out if a remote image exists and, if so, how old it is
        remote_image_url=https://${source_registry}/v2/${image}/manifests/${tag}
        if curl -f -s -u ${source_creds} ${remote_image_url} > /dev/null; then
            log debug "remote image found: ${qualified_image}"
            remote_created_at=$(curl -sf -u ${source_creds} ${remote_image_url} | jq -r '.history[].v1Compatibility' | jq -r '.created' | sort | tail -n1)
            log debug "remote created at: ${remote_created_at}"
        else
            log debug "no remote image found: ${qualified_image}"
        fi

        if [ -z ${local_created_at} ] && [ -z ${remote_created_at} ]; then
            die_with_message "${qualified_image} neither found locally nor in ${source_registry}"
        fi

        if [ -n ${remote_created_at} ]; then
            # determine if we need to pull image: if the local image either
            # does not exist or is older than the remote
            if [ -z ${local_created_at} ] ||
                   [ "${local_created_at}" \< "${remote_created_at}" ]; then
                log debug "remote image is more recent, downloading ..."
                docker pull ${qualified_image}
            else
                log debug "local image is more recent, skipping download ..."
            fi
        fi
        log info "pushing ${qualified_image} to destination registry ..."
        docker tag ${qualified_image} ${dest_registry}/${image}:${tag}
        docker push ${dest_registry}/${image}:${tag}
    done
done < /dev/stdin
