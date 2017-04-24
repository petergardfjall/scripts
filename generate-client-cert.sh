#!/bin/bash

#
# This script generates a self-signed client SSL certificate.
#
# The script generates the following files in the current directory:
#  - client_key.pem: the client's private key.
#  - client_certificate.pem: the client's certificate.
#
# NOTE: relies on openssl and keytool being installed.
#

scriptname=$(basename ${0})

sample_subject="/O=Domain/CN=Client"
if [ -z ${1} ]; then
  echo "error: missing argument(s)" 2>&1
  echo "usage: ${scriptname} <client-subject>" 2>&1
  echo "  <client-subject> could, for example, be '${sample_subject}'" 2>&1
  exit 1
fi

client_subject=${1}
destdir=${PWD}

# 1. Generate the client's private key:
echo "generating client's private key ..."
openssl genrsa -out ${destdir}/client_key.pem 2048
# 2. Create the client's self-signed X.509 certificate:
echo "generating client's certificate ..."
openssl req -new -x509 -key ${destdir}/client_key.pem -out ${destdir}/client_certificate.pem -days 365 -subj ${client_subject}
