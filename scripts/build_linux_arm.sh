#!/bin/sh
set -eux
apt update
DEBIAN_FRONTEND=noninteractive apt install -y tzdata
apt install -y python3.9 python3.9-dev python3-pip
python3.9 -m pip install uv --only-binary uv
# Need to build with python 3.9 to support systems with libpython >= 3.9
uv python pin 3.9
uv sync --no-binary-package pyyaml --no-binary-package ijson
uv run pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1
