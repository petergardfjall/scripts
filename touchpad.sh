#!/bin/bash

TOUCHPAD_ID=${TOUCHPAD_ID}

#
# Script to turn touchpad/trackpad on/off.
# NOTE: needs t
#

# note: may change depending on host! See: 'xinput list'
if [ -z "${TOUCHPAD_ID}" ]; then
    # do a best effort attempt to find input device id for touchpad
    TOUCHPAD_ID=$(xinput list | grep -i touchpad | egrep --only-matching 'id=[0-9]+' | cut -d'=' -f 2)
    if [ -z "${TOUCHPAD_ID}" ]; then
        echo "best-effort detection of touchpad failed. Use 'xinput list' and set TOUCHPAD_ID accordingly."
        exit 1
    fi
fi

function die_with_error {
    echo "error: usage: $(basename ${0}) on|off"
    exit 1
}

if [ -z ${1} ]; then
    die_with_error
fi

if [ "${1}" = "on" ]; then
    xinput set-prop ${TOUCHPAD_ID} "Device Enabled" 1
elif [ "${1}" = "off" ]; then
    xinput set-prop ${TOUCHPAD_ID} "Device Enabled" 0
else
    die_with_error
fi
