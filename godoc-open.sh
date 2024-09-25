#!/bin/bash

set -e

port=5544
if [ -n "${1}" ]; then
    port="${1}"
fi

echo "opening godoc server on localhost:${port} ..."
pkgsite -http :${port} &
sleep 0.5
xdg-open http://localhost:${port}
