#!/usr/bin/env bash
python3 "$(dirname "$0")/scripts/resize-photos.py"
hugo server -D --buildFuture
