#!/bin/sh
set -eux

# alpine:edge has Python 3.14.10 (CVE-2026-115557). Stable 3.24 is still on
# 3.14.8. libpython links musl 1.2.6, so the binary needs Alpine 3.24 or newer.
apk add --no-cache build-base ca-certificates curl python3 python3-dev py3-pip

python3 -m pip install --break-system-packages 'uv>=0.13.4'
uv sync --python /usr/bin/python3 --no-binary-package pyyaml --no-binary-package ijson
uv run --python /usr/bin/python3 pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1
