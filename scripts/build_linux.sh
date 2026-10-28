#!/bin/sh
set -eux
apt update
DEBIAN_FRONTEND=noninteractive apt install -y build-essential
python3 -m pip install --upgrade pip
python3 -m pip install uv --only-binary uv
# Image CPython is 3.10 on glibc 2.31. A uv-managed interpreter would
# bundle a different libc into the PyInstaller binary.
export UV_PYTHON_PREFERENCE=only-system
export UV_PYTHON=3.10
uv sync --no-binary-package pyyaml --no-binary-package ijson
uv run pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1

# codecov linux binary should be just codecovcli_linux
if [ "$1" = "linux_x86_64" ]; then
    mv ./dist/codecovcli_$1 ./dist/codecovcli_linux
fi
