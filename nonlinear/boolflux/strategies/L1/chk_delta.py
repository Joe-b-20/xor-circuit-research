from collections import Counter
from l1_lib import Data
D = Data()
print(sorted(Counter(x["delta"] for x in D.val.values()).items()))
print("A<=31:", sorted(Counter(x["delta"] for (c, i), x in D.val.items() if D.m[i][0] <= 31).items()))
