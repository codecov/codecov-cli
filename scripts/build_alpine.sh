#!/bin/sh
set -eux
apk add build-base python3 py3-pip curl
python3 -m pip install uv --only-binary uv
# Need to build with python 3.9 to support systems with libpython >= 3.9
uv python pin 3.9
uv sync --no-binary-package pyyaml --no-binary-package ijson
uv run pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1
