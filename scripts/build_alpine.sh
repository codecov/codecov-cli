#!/bin/sh
set -eux

root=$(pwd)

# Keep Alpine 3.14 so the binary stays on musl 1.2.2. Its python3 package is
# 3.9, which has no CVE-2026-115557 patch, so build 3.11.18 against this musl.
apk add --no-cache \
    build-base \
    ca-certificates \
    curl \
    libffi-dev \
    linux-headers \
    openssl-dev \
    bzip2-dev \
    zlib-dev \
    readline-dev \
    sqlite-dev \
    xz-dev

ver=3.11.18
curl -fsSL -o /tmp/Python.tgz "https://www.python.org/ftp/python/${ver}/Python-${ver}.tgz"
echo "5f62711b12470fd435f83f1451c1b1ef4a179aebc715c716874b0967567d814e  /tmp/Python.tgz" | sha256sum -c
rm -rf "/tmp/Python-${ver}"
tar -xzf /tmp/Python.tgz -C /tmp
cd "/tmp/Python-${ver}"
./configure --prefix=/usr/local --enable-shared --with-ensurepip=install
make -j"$(nproc)"
make altinstall

export PATH="/usr/local/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$root"

python3.11 -m pip install 'uv>=0.13.4'
uv sync --python /usr/local/bin/python3.11 --no-binary-package pyyaml --no-binary-package ijson
uv run --python /usr/local/bin/python3.11 pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1
