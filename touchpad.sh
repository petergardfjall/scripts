#!/bin/bash

#
# Script to turn touchpad/trackpad on/off.
# NOTE: needs t
#

# note: may change depending on host! See: 'xinput list'
trackpad_id=12

function die_with_error {
    echo "error: usage: $(basename ${0}) on|off"
    exit 1
}

if [ -z ${1} ]; then
    die_with_error
fi

if [ "${1}" = "on" ]; then
    xinput set-prop ${trackpad_id} "Device Enabled" 1
elif [ "${1}" = "off" ]; then
    xinput set-prop ${trackpad_id} "Device Enabled" 0
else
    die_with_error
fi

