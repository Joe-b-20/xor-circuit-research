#!/bin/bash
# Print, without saving to disk, the sentences of the ar5iv rendering of arXiv 1304.0513 around "famously".
curl -s -L --max-time 40 -A "Mozilla/5.0" https://ar5iv.labs.arxiv.org/html/1304.0513 | sed -e 's/<[^>]*>/ /g' | tr -s ' \n' ' ' | grep -o -i -E '.{0,200}famously.{0,260}'
echo ===
curl -s -L --max-time 40 -A "Mozilla/5.0" https://ar5iv.labs.arxiv.org/html/1304.0513 | sed -e 's/<[^>]*>/ /g' | tr -s ' \n' ' ' | grep -o -i -E '.{0,160}independently.{0,160}' | head -3
