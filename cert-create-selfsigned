#!/bin/bash

#
# Generates a self-signed client or server certificate.
#
# The script generates the following files in the current directory:
#  - <name>_key.pem: the private key.
#  - <name>_certificate.pem: the certificate.
#
# NOTE: relies on openssl being installed.
#

scriptname=$(basename ${0})

if [ -z ${1} ]; then
  echo "error: missing common-name argument(s)" 2>&1
  echo "usage: ${scriptname} <common-name>" 2>&1
  echo "  <common-name> could, for example, be 'my-server'" 2>&1
  exit 1
fi

common_name="${1}"
subject="/CN=${common_name}"
destdir="${PWD}"

keypath="${destdir}/${common_name}_key.pem"
certpath="${destdir}/${common_name}_cert.pem"

# 1. create private key
echo "generating ${keypath} ..."
openssl genrsa -out ${keypath} 2048
# 2. Create the server's self-signed X.509 certificate:
echo "generating ${certpath} ..."
openssl req -new -x509 -sha256 -key ${keypath} -out ${certpath} -days 365 -subj ${subject}
