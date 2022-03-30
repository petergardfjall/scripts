#!/bin/bash

self=$(basename ${0})

set -e

function die {
    echo -e "\e[31merror: ${1}\e[0m"
    echo "usage: ${self} <basepath> <targetpath>"
    echo
    echo "Gives <targetpath> as a path relative to <basepath>, such that"
    echo "the resulting path can just be appended with a leading slash"
    echo "to <basepath>."
    exit 1
}

# deduplicate separators, clean path from leading dots, and remove trailing
# slashes or dots
function clean_path {
    path=${1}
    # deduplicate separators
    path=$(echo ${path} | tr -s /)
    # remove leading dots: ".", "./", ".//"
    path=$(echo ${path} | sed 's#^\./##')
    # remove trailing dots or slashes (e.g. on "." or "a/" as input)
    path=$(echo ${path} | sed 's#\.$##')
    path=$(echo ${path} | sed 's#/\+$##')
    echo "${path}"
}

function normalize_path {
    path=${1}

    path=$(clean_path ${path})

    # make path absolute
    if ! [[ ${path} =~ ^/ ]]; then
        path="${PWD}/${path}"
    fi

    echo ${path}
}

function relpath {
    [ -z "${1}" ] && die "no basepath given"
    [ -z "${2}" ] && die "no targetpath given"

    basepath=$(normalize_path ${1})
    targetpath=$(normalize_path ${2})

    if [ "${basepath}" = "${targetpath}" ]; then
        echo "."
        return 0
    fi

    # find common path prefix
    # move up directories until prefix is common
    diffpath=""
    while ! [[ ${targetpath} =~ ^${basepath}.* ]]; do
        basepath=$(dirname ${basepath})
        diffpath="../${diffpath}"
    done
    common_prefix="$(clean_path ${basepath})"
    # strip common prefix off targetpath and prepend with diffpath
    targetpath=${targetpath#${common_prefix}/}
    if [ -n "${diffpath}" ]; then
        targetpath="${diffpath}/${targetpath}"
    fi
    clean_path ${targetpath}
}

relpath ${1} ${2}


# Tests: paste these into a shell and there should be no output.
#
# function assert_equal {
#     [[ "${1}" != "${2}" ]] && echo "NOT EQUAL: \"${1}\" != \"${2}\""
# }
#
# assert_equal "$(relpath.sh . .)" "."
# assert_equal "$(relpath.sh ./a/b/c ./a/b/c)" "."
# assert_equal "$(relpath.sh ./a/b/c/. ./a/b/c/.)" "."
# assert_equal "$(relpath.sh /a/b/c /a/b/c)" "."
# assert_equal "$(relpath.sh a/b c/d)" "../../c/d"
# assert_equal "$(relpath.sh ./a/b ./c/d)" "../../c/d"
# assert_equal "$(relpath.sh . ./a)" "a"
# assert_equal "$(relpath.sh /tmp/a/b /tmp/a/b)" "."
# assert_equal "$(relpath.sh /tmp/a/b /tmp/a/c)" "../c"
# assert_equal "$(relpath.sh /tmp/a/b /tmp/c/d)" "../../c/d"
# assert_equal "$(relpath.sh /etc/a/b /tmp/c/d)" "../../../tmp/c/d"
# pushd /tmp > /dev/null
# assert_equal "$(relpath.sh . /etc/a/b)" "../etc/a/b"
# popd > /dev/null
