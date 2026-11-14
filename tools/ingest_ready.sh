#!/bin/bash
# Ingest every work/out batch that passes check_batch and is new or changed since last ingest.
cd "$(dirname "$0")/.."
touch work/ingested_mtime.txt
ready=()
for f in work/out/*.jsonl; do
  n=$(basename "$f" .jsonl)
  m=$(stat -f %m "$f")
  grep -qx "$n $m" work/ingested_mtime.txt && continue
  if python3 tools/check_batch.py "work/batches/$n.jsonl" "$f" >/dev/null 2>&1; then ready+=("$n"); fi
done
if [ ${#ready[@]} -gt 0 ]; then
  if python3 tools/ingest.py "${ready[@]}"; then
    for n in "${ready[@]}"; do
      grep -v "^$n " work/ingested_mtime.txt > work/.im; mv work/.im work/ingested_mtime.txt
      echo "$n $(stat -f %m work/out/$n.jsonl)" >> work/ingested_mtime.txt
    done
  fi
fi
python3 tools/build.py
