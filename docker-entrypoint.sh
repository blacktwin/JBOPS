#!/usr/bin/env bash

exec \
    /usr/local/bin/python \
        "/app/${JBOPS_SCRIPT_PATH}" \
        "$@"
