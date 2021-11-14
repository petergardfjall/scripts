#!/bin/bash

#
# Lists all xfce4 configuration values
#

set -e

# list all channels
channels=$(xfconf-query -l | tail --lines=+2)
for channel in ${channels}; do
    echo "*** channel: ${channel} ***"
    properties=$(xfconf-query -c ${channel} -l)
    for prop in ${properties}; do
        val=$(xfconf-query -c ${channel} -p ${prop})
        echo "  ${prop}: ${val}"
    done
done
