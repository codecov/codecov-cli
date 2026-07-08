#!/bin/sh
set -eux
apk add build-base python3 py3-pip curl
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
# Need to build with python 3.9 to support systems with libpython >= 3.9
uv python pin 3.9
uv sync --no-binary-package pyyaml --no-binary-package ijson
uv run pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1
