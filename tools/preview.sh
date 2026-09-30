#!/bin/sh
# Render the README through GitHub's markdown API, then screenshot it (needs `gh auth login`).
cd "$(dirname "$0")/.." || exit 1
mkdir -p preview
gh api -X POST /markdown -F mode=gfm -F text=@README.md > preview/body.html || exit 1
node tools/preview.mjs
