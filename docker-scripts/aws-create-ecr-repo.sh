#!/bin/bash

set -e

scriptname=$(basename ${0})

function print_usage() {
    echo "Creates AWS ECR repositories in a given destination ECR."
    echo "NOTE: the user must be logged in (via docker login) to"
    echo "the ECR registry. The images for which to create ECR repositories"
    echo "are given on stdin."
    echo ""
    echo "usage: ${scriptname} [OPTIONS] <dest-registry>"
    echo ""
    echo "For example:"
    echo "  cat images.txt | ${scriptname} 123456789012.dkr.ecr.eu-west-2.amazonaws.com"
    echo ""
    echo "where images.txt may contain content similar to:"
    echo "  myorg/gateway:  latest v1.0.0"
    echo "  myorg/kafka:    latest v2.0.0"
    echo "  myorg/frontend: v1.1.0"
    echo "  ..."
    echo ""
    echo "Each row is a docker image followed by a colon and a list of tags."
    echo "A repository is created in ECR for every image (the tags are ignored)"
    echo "unless it already exists."
    echo ""
    echo "Options:"
    echo "  --help               Prints help text."
}

function die_with_error() {
    echo "error: ${1}"
    exit 1
}

for arg in ${@}; do
    case ${arg} in
	--help)
	    print_usage
	    exit 0
	    ;;
	--*)
	    die_with_error "unrecognized option: ${arg}"
	    ;;
	*)
	    # assume only positional args left
	    break
	    ;;
    esac
    shift
done

if [[ $# -lt 1 ]]; then
    die_with_error "a destination registry must be given"
fi
dest_registry=${1}

existing_repos=$(aws ecr describe-repositories | jq -r '.[][].repositoryName')
echo "reading images for which to create repos from stdin ..."
while read image_and_tags; do
    if echo ${image_and_tags} | egrep -q '^\s*#' ; then
        # ignore lines starting with #
        continue
    fi

    image=$(echo ${image_and_tags} | awk -F: '{ print $1 }')
    tags=$(echo ${image_and_tags} | awk -F: '{ print $2 }')
    if echo ${existing_repos} | grep --silent ${image}; then
	echo "repo already exists for ${image}"
    else
	echo "creating a repo for image ${image} ..."
	aws ecr create-repository --repository-name ${image}
    fi
done < /dev/stdin
