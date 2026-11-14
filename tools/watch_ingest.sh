#!/bin/bash
# Wait until at least N output files changed since start (or timeout), then ingest+build.
cd "$(dirname "$0")/.."
N=${1:-6}; T=${2:-1500}
start=$(date +%s); base=$(ls -l work/out/*.jsonl | md5)
while true; do
  sleep 60
  changed=$(find work/out -name '*.jsonl' -newermt "@$start" | wc -l)
  [ "$changed" -ge "$N" ] && break
  [ $(( $(date +%s) - start )) -ge "$T" ] && break
done
tools/ingest_ready.sh | tail -3
