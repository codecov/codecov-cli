#!/bin/sh
set -eux

apt update
DEBIAN_FRONTEND=noninteractive apt install -y tzdata ca-certificates curl build-essential

# Distro Python on ubuntu:20.04 is 3.8/3.9 and will not get CVE-2026-115557.
# This standalone build needs glibc 2.17, so it still runs on this image.
arch=${1#*_}
case "$arch" in
  x86_64) triple=x86_64-unknown-linux-gnu ;;
  arm64) triple=aarch64-unknown-linux-gnu ;;
  *) echo "unsupported arch: $arch" >&2; exit 1 ;;
esac

ver=3.11.18
tag=20261026
url="https://github.com/astral-sh/python-build-standalone/releases/download/${tag}/cpython-${ver}+${tag}-${triple}-install_only.tar.gz"
curl -fsSL -o /tmp/python.tar.gz "$url"
rm -rf /opt/python
mkdir -p /opt/python
tar -xzf /tmp/python.tar.gz -C /opt/python --strip-components=1

export PATH="/opt/python/bin:${PATH}"
export LD_LIBRARY_PATH="/opt/python/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

python3 -m pip install 'uv>=0.13.4'
uv sync --python /opt/python/bin/python3 --no-binary-package pyyaml --no-binary-package ijson
uv run --python /opt/python/bin/python3 pyinstaller -F codecov_cli/main.py
mv ./dist/main ./dist/codecovcli_$1

# codecov linux binary should be just codecovcli_linux
if [ "$1" = "linux_x86_64" ]; then
    mv ./dist/codecovcli_$1 ./dist/codecovcli_linux
fi
