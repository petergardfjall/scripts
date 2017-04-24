#!/bin/bash

#
# Generates a self-signed server certificate that can be used by servers
# wishing to serve HTTPS requests.
#
# 
# The script generates the following files in the current directory:
#  - server_key.pem: the server's private key.
#  - server_certificate.pem: the server's certificate.
#
# NOTE: relies on openssl being installed.
#

scriptname=$(basename ${0})

sample_subject="/O=Domain/CN=Server"
if [ -z ${1} ]; then
  echo "error: missing argument(s)" 2>&1
  echo "usage: ${scriptname} <server-subject>" 2>&1
  echo "  <server-subject> could, for example, be '${sample_subject}'" 2>&1
  exit 1
fi

server_subject=${1}
destdir=${PWD}

# 1. Create a private key for the server:
echo "generating server's private key ..."
openssl genrsa -out ${destdir}/server_key.pem 2048
# 2. Create the server's self-signed X.509 certificate:
echo "generating server's certificate ..."
openssl req -new -x509 -sha256 -key ${destdir}/server_key.pem \
   -out ${destdir}/server_certificate.pem -days 365 -subj ${server_subject}
