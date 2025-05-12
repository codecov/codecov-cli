#!/bin/sh
apt install build-essential
pip install -r requirements.txt
pip install .
python setup.py build
pip install pyinstaller
pyinstaller --copy-metadata codecov-cli -F codecov_cli/main.py
cp ./dist/main ./dist/codecovcli_$1
