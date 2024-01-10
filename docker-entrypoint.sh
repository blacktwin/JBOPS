#!/usr/bin/env bash

exec \
    /usr/bin/python3 \
        "/app/${JBOPS_SCRIPT_PATH}" \
        "$@"
