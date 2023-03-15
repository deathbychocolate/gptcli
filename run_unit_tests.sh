#!/bin/bash

# Run unit tests
# Usage: bash run_unit_tests.sh

pytest --tb=line src/test/test_*.py
