#!/bin/bash

curl -sSL https://services.nvd.nist.gov/rest/json/cpes/2.0 | jq -r .totalResults
