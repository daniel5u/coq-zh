#!/usr/bin/env bash
# Validate and package the committed mod; a game installation is not required.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 tools/package.py "$@"
