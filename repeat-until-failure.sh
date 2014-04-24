#!/bin/bash

#
# Repeats a command until it fails (non-zero exit code).
#

if [ "${1}" = "" ]; then
  echo "error: expected command"
  exit 1
fi
command=$@

counter=0
status_code=0
while [  $status_code -eq 0 ]; do
  let counter=counter+1 
  echo "  >>>> Attempt ${counter} ..."
  eval ${command}
  status_code=$?
  echo "  >>>> Attempt ${counter} status code: ${status_code}"
done