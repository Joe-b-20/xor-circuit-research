#!/bin/bash
# Copy the frozen v8 engine (repo search/xorflux, untouched) into xorflux-translog/xorflux.
set -e
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
mkdir -p "$T/xorflux-translog"
rm -rf "$T/xorflux-translog/xorflux"
cp -a "$HOME/xor-circuit-research/search/xorflux" "$T/xorflux-translog/xorflux"
find "$T/xorflux-translog" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
ls "$T/xorflux-translog/xorflux"
cd "$HOME/xor-circuit-research"
echo "repo HEAD: $(git rev-parse HEAD)"
git status --short | head -3
echo ---- registry
sed -n 1,60p search/xorflux/config/registry.py
echo ---- tests runner
grep -rn "unittest\|pytest" search/xorflux/README.md 2>/dev/null | head -5
ls search/xorflux/*.md
