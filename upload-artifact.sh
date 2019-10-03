#!/bin/bash
set -e
set -u

# BEOORDELINGSTOOL_ARTIFACTS_KEY should be set as env variable in your shell.
# Reinout can give you the value to use.
# (Ideally, we would be uploaded automatically by travis-ci.com)
PROJECT=Beoordelingstool

# You must call this script with the (versioned!) name of the zipfile as
# its first parameter.
curl -X POST \
     --retry 3 \
     -H "Content-Type: multipart/form-data" \
     -F key=${BEOORDELINGSTOOL_ARTIFACTS_KEY} \
     -F artifact=@$1 \
     https://artifacts.lizard.net/upload/${PROJECT}/
