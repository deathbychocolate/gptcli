#!/bin/bash

# This script detects if the user has pipenv in his PATH.
# Usage: ./has_pipenv.sh

has_pipenv() {
    if [[ -z "$(which pipenv)" ]]; then
        echo "pipenv not found."
        return 1  # false
    else
        echo "pipenv found at '$(which pipenv)'."
        return 0  # true
    fi
}

# Capture function output
result=$(has_pipenv)
exit_code=$?

exit ${exit_code}
