#!/bin/bash

if [ "${1}" = "" ]; then
    echo "error: argument must be a PEM-formatted cert"
    exit 1
fi

openssl x509 -in ${1} -text
