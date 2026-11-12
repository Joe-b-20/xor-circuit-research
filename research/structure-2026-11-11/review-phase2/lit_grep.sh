#!/bin/bash
# Print, without saving anything to disk, the lines of two public web pages that mention the
# attribution, the depth, the referee and the matrix-multiplication argument.
for u in https://web.vu.lt/mif/s.jukna/Knizka/comment3.html https://web.vu.lt/mif/s.jukna/Knizka/problem-7.7.html; do
  echo "=== $u"
  curl -s -L --max-time 30 -A "Mozilla/5.0" "$u" | sed -e 's/<[^>]*>//g' | tr -s ' ' | grep -n -i -E 'igor|sergeev|referee|paul|depth|strassen|omega|direct sum|not hold|smaller|2015|2017|7\.7' | cut -c1-260
done
