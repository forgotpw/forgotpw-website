#!/bin/bash

set -e

# This script intended to be run inside Docker with AWS credentials passed
# in from iam-docker-run.  See README.md for example deployment usage.

if [ -z "$AWS_ENV" ]; then
    echo "Must provide AWS_ENV environment variable"
    exit 1
fi

if [ "$AWS_ENV" == "prod" ]; then
  export SUBDOMAIN="www"
else
  export SUBDOMAIN="www-dev"
fi

# empty the bucket first
aws s3 rm s3://$SUBDOMAIN.rosa.bot --recursive

aws s3 cp \
  ./src/ \
  s3://$SUBDOMAIN.rosa.bot/ \
  --recursive
