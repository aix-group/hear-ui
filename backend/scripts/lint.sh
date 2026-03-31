#!/usr/bin/env bash

set -e
set -x

mypy app
ruff check app
# --check returns non-zero if files would be reformatted (fails CI correctly)
ruff format app --check
