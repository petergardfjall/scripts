#!/bin/bash

if [ "${2}" = "" ]; then
    echo "error: missing argument(s)"
    echo "  usage: ${0} <interval> <header> [body]"
    exit 1
fi

# every <interval> seconds, the notification will appear
interval=$1
# the header of the notification area
header=$2
# the text to appear in the box under the notification header
body=""
if [ "${3}" != "" ]; then
   body=${3}
fi


# time notification will appear (in ms)
time_to_appear=5000

while [ 1 ]; do
    sleep ${interval}
    echo "reminding ..."
    notify-send -t ${time_to_appear} -u normal ${header} ${body}
done

