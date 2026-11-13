#!/usr/bin/env bash
# Runs Salesforce Code Analyzer (all Security-tagged rules) on every scenario.
# Output: results/code_analyzer/<scenario_id>.json
# Requires: Salesforce CLI + code-analyzer plugin (sf plugins install code-analyzer), Java 11+.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results/code_analyzer
for dir in scenarios/*/; do
  id=$(basename "$dir")
  echo "== $id"
  sf code-analyzer run \
    --workspace "$dir" \
    --rule-selector Security \
    --output-file "results/code_analyzer/$id.json" \
    --view table > "results/code_analyzer/$id.log" 2>&1 || true
done
echo "Done. Results in results/code_analyzer/"
