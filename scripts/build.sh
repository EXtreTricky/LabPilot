#!/bin/sh
set -eu
python -m compileall -q src
python -m unittest discover -s tests -v
