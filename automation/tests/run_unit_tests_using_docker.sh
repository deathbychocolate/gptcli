#!/bin/bash

# Run unit tests from a Docker container
# Usage: bash run_unit_tests.sh

set -e

docker image build -t gptcli:latest .
docker run gptcli:latest
