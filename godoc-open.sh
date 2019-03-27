#!/bin/bash

set -e

port=5544
if [ -n "${1}" ]; then
    port="${1}"
fi

echo "opening godoc server on localhost:${port} ..."
godoc -http localhost:${port} &
sleep 0.5
xdg-open http://localhost:${port}
