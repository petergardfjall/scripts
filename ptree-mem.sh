#!/bin/bash

#
# reports on the memory consumption of all processes with the given process pid
# as ancestor.
#
# The resident set size (RSS) column is the column of interest. It's the portion
# of memory occupied by a process that is held in main memory (RAM).
#

set -e

function print_usage {
    echo "$(basename ${0}) [OPTIONS] <pid>"
    echo ""
    echo "Options:"
    echo
    echo "--period=<DUR>  Seconds between updates. Default: 5s"
    echo
}

period=5s
for arg in ${@}; do
    case ${arg} in
        --period=*)
            period=${arg/*=/}
            ;;
        --help)
            print_usage
            exit 0
            ;;
        --*)
            die_with_error "unrecognized option: ${arg}"
            ;;
        *)
            # no option, assume only positional arguments left
            break
            ;;
    esac
    shift
done

[ -z "${1}" ] && echo "error: no root pid given" && exit 1
root_pid="${1}"

while ps -p ${root_pid} > /dev/null; do
    children=$(pstree -p ${root_pid} | grep -o '([0-9]\+)' | grep -o '[0-9]\+' | xargs echo | sed 's/ /,/g')

    pidstat --human -p ${children} -r -l
    sleep ${period}
done

echo "process ${root_pid} does not exist (or has terminated)"
