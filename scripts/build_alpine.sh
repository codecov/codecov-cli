#!/bin/sh
set -eux
apk add build-base python3 python3-dev py3-pip curl
python3 -m pip install --upgrade pip
python3 -m pip install uv --only-binary uv
# Alpine 3.16 python3 is 3.10 on musl 1.2.3. A uv-managed interpreter
# would bundle a different libc into the PyInstaller binary.
export UV_PYTHON_PREFERENCE=only-system
export UV_PYTHON=3.10
uv sync --no-binary-package pyyaml --no-binary-package ijson
uv run pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1
