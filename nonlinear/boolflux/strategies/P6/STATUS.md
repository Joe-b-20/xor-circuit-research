# P6 status (T07, T08), updated 23:15 UTC (final)

All P6 jobs stopped 23:14 UTC.  Overnight proposals: QUEUE.md entries P6-q12, P6-q13, P6-c3, P6-t07p.

T08 (ref 35/3/183/13; hard A<=35, AD<=3) - ~/xs-campaigns/2026-11-15-targets/P6/found/, aes_check OK,
path_certified true:
- best strict, primary (GD<=12, G<=183): **35/3/181/12** (aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b) - new.
- best strict at GD13 (secondary, G lower): **35/3/168/13** (aes-sbox-a35-ad3-g168-gd13-94a02642b2d6) - new
  (archive had 177@13); also 169, 170, 171, 172, 175 @13.
- tradeoffs: none needed (181@12 dominates the reference).
- frontier A35 AD3 (ours + archive): 181@12, 168@13, 162@14, 155@15, 147@16, 144@17, 143@18, 141@19, 140@22, 139@23, 138@24, 137@28.

T07 (ref 35/3/139/27): best strict = primary met: **35/3/138/24** (aes-sbox-a35-ad3-g138-gd24-d6946cbba230) - new;
also 139@23, 139@25 (strict), 140@22 and 137@28 (frontier; 137@28 is not a permitted tradeoff: -2 gates, GD 28).
Route: GF(2^8) conjugates (P3 conj3/mkconj) of 140@25 / 139@25 + kernel stages (GD31 -> GD27), repair_keep 1.
Negative: T3 gf4loop at caps 27/29, class re-basing gate price (+3..+7), low-GD basins (153@24, 148@22).
