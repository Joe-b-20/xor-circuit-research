# Independent review: the two final five-entry tail profiles

2026-11-14. Independent machine review of [TWO_NONCLEAN_TAIL_CLOSED.md](../TWO_NONCLEAN_TAIL_CLOSED.md) and [THREE_NONCLEAN_FOUR_TERM_TAIL_CLOSED.md](../THREE_NONCLEAN_FOUR_TERM_TAIL_CLOSED.md). This is an argument audit, not formal verification or human certification. No circuit search or enumeration was used.

**Verdict:** both closures pass. Each uses actual fibre geometry to handle the two remaining useful returns with at most one extra source XOR beyond two specified group completions. The resulting four-diagonal supplier contradiction is valid, including the chronology of the reused return and of a clean sum whose individual clean summands have not yet been read.

## Shared prerequisites and the affine-tree reduction

The global saturated-tail result gives a unique outside entry `v=u+h`, at least two distinct useful returns, and an outside label independent of the core entry span. The five-entry target core has six non-entry gates, so its ordinary projection is the six-gate minimum and each ordinary-mask fibre is one entry tree. Distinct useful values give distinct partners different from `u`; a return to `u` would merely reproduce the previously supplied `h`.

For a connecting subtree with `s` edges and `r` useful partners, the vertices other than `u` and its partners number `s-r`. Affine-tree transfer therefore closes every case with `s-r<=1`. Once the geometric arguments bound a relevant fibre by four edges, the only surviving possibility is `s=4,r=2`. No liveness assumption about the outside entry is being silently substituted for global target-cone membership.

## Two nonclean entries

The full-diagonal bound permits at most two distinct physical clean values. Three nonzero clean entry occurrences must span at least two dimensions because the entire core span has rank four and there are only two nonclean occurrences. Thus their values are exactly `c,c,d`, with `c,d` independent. The distinct labels `c,d,n,m` are a basis; `e=n+m` is clean and independent of `c,d`. Adding the outside label gives the independent full basis `c,d,n,m,h`.

The repeated `c` relation is precisely the odd-trace support. Thus the two `c` traces are odd, while `d,n,m` are even; only the two nonclean traces coincide. Even-wire separation places `d` in a different ordinary-mask fibre from `n,m`. A four-edge fibre must therefore contain exactly `c,c,n,m`.

Adjacent `c` edges would give equal full physical endpoint values. A path `c,n,c` would give a second physical pair of difference `n`, and a path `c,m,c` would do the same for `m`. Saturated collision and unique-pair rigidity exclude these. The two `c` edges must consequently lie at the ends of the full four-edge path `c-n-m-c`, up to exchanging `n,m` and reversing the path. The path endpoints differ by `e`.

Two-group completion of `P=<c,d>` and `Q=<n,m>` needs at most the two missing values `c+d` and `e`. Every return between core nodes is a sum of one value from each group. Because the distinct full labels form a basis, its support uses only values already read before that exit; repeated occurrences of `c` do not change this value-level uniqueness. The completion is chronological.

If `u` is a path endpoint, one useful return is `h+e`, costing one XOR, while the other costs at most two. If `u` is internal, its two partners must be the path endpoints. Compute the first return with at most two XORs, then the second by adding `e`. The supports of the two return values differ in both `n` and `m`, so both have been read by the second exit, even if `e` could not have been supplied at the first. This establishes the one-extra-XOR tail budget without an ordering assumption.

## Three nonclean entries and a four-term relation

Here `a+b+c+d=0`, with `a,b,k` nonclean and `c,d` clean. The four odd traces are those of `a,b,c,d`; the even trace of `k` is the sum of the `a,b` traces, and no other odd pair has that sum. In the fibre containing `k`, any adjacent odd pair other than `a,b` would expose a second even helper with the same ordinary derivative as the marked `k` wire. This is forbidden.

Deleting the `k` edge consequently leaves components of at most one odd edge, except for one possible `a,b` two-edge path. A four-edge fibre is therefore exactly that two-edge path joined by `k` to a clean one-edge path. The proof does not restrict or enumerate the bridge attachment. Other fibres have only distinct odd traces, hence are stars by the odd-run theorem and are already handled by affine-tree transfer.

The replay split `P=<c,d>`, `Q=<a,k>` needs a chronology check because `b` is not a basis label. Naming `a` to be read before `b` supplies it. The labels `c,d` are pure `P`, and `a,k` are pure `Q`. At the later `b` entry, `b=a+t` with `t=a+b=c+d`; both `a` and `b` are then physically available, so `t` can be generated without waiting for `c,d`. Every entry-prefix span splits under this direct sum. Credited group completion therefore charges only the potentially missing values `t,e=a+k`; any early production of an original label is credited to its later original producer.

Partition the five vertices of the four-edge tree into the three vertices of its `a,b` path and the two vertices of its clean edge. Within the first part, pair differences are `a,b,t`; within the second, the pair difference is the actual clean edge label. Among `u,w_1,w_2`, two lie in the same part. This is the stated cheap difference, not an assumed virtual source credit.

If the pair contains `u`, one return is `h` plus that available difference and costs one XOR; the other costs at most two. If the pair consists of the two partners, compute the first return with at most two XORs and the second by adding the cheap difference. An edge label is available by the later endpoint's production. For `t`, both `a,b` edges on their path have been read by the time both endpoints have appeared; `t=a+b` is then available from the group completion. This validates the shortcut even if `c,d` remain unread at that time.

## Supplier contradiction and limits

In either note, ordinary source gates and other exits remain chronological, all original source values are preserved, and the completed groups supply a clean triangle plus an independent fourth diagonal. The total source-only cost is at most `G_0+3<=12`, contradicting the thirteen-gate four-diagonal supplier bound. The clean parts of consumer nodes are never treated as separately free source operands.

These are closures of the stated outside-tail profiles. They do not alone establish the completeness of all other profile reductions, eliminate a target-live six-entry consumer, or change the unrestricted MixColumns bounds.
