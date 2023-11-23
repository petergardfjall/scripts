#!/bin/bash

#
# Compares the number of changed files between versions of a git repo.
#
# Note that changed files include added and removed files. This is the reason
# why sometimes more changes are reported than the total number of files in
# either version.
#
# For large repos you may see a warning like 'warning: exhaustive rename
# detection was skipped due to too many files' unless your git diff.renameLimit
# is set high enough.
#
#   git config --global diff.renameLimit 100000
#

set -e
set -o pipefail

function die {
    echo -e "\e[31m[error] ${1}\e[0m"
    exit 1
}

[ -z "${1}" ] && die "no git directory repo directory given"
repo_dir="${1}"
shift
[ $# -lt 2 ] && die "at least two versions (commits, tags) are needed"
versions=( "$@" )

if ! [ -d "${repo_dir}/.git" ]; then
    die "${repo_dir} does not appear to be a git repository"
fi

pushd "${repo_dir}" > /dev/null
{
    num_versions="${#versions[@]}"
    max_index=$(( ${num_versions} - 1 ))

    #
    # Output total number of files for each version.
    #
    echo "| Version | Total Files |"
    echo "| ------- | ----------- |"
    for i in $(seq 0 ${max_index}); do
        version_controlled_files=$(git ls-tree -r --name-only ${versions[i]} | wc -l)
        echo "| ${versions[i]} | ${version_controlled_files} |"
    done
    echo


    #
    # Output a matrix of changed files between every pair of versions.
    #
    echo -n "|             "
    for i in $(seq 0 ${max_index}); do
        echo -n "| ${versions[i]} "
    done
    echo "|"
    echo -n "| ----------- "
    for i in $(seq 0 ${max_index}); do
        echo -n "| ----------- "
    done
    echo " |"

    for i in $(seq 0 ${max_index}); do
        echo -n "| ${versions[i]} "
        for j in $(seq 0 ${max_index}); do
            v_i="${versions[i]}"
            v_j="${versions[j]}"

            if [ "${i}" -le "${j}" ]; then
                changed_files=$(git diff --name-only ${v_i} ${v_j} | wc -l)
                echo -n "| ${changed_files} "
            else
                  echo -n "| - "
            fi
        done
        echo " |"
    done
}
popd > /dev/null
