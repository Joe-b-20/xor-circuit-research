# Compliance note 2026-11-15 18:20 UTC (coordinator): kernel repairs and the hard A/AD limits

Found by P1 (strategies/P1/NOTES.md section 6), confirmed in kernel/bfx.c lines 285-292 and 1064-1077:
- From a start that is inside ALL caps the kernel never leaves them ("a feasible state is never left for
  an infeasible one": best, neutral and uphill moves all require m.feas >= mcur.feas).
- From a start that violates a cap (typically a pull: start GD above the job's GD cap) the violation is
  the SUM of cap excesses, so a repair move may raise A above cap.a or AD above cap.ad while lowering GD.
  Intermediate kernel states can then be outside the target's hard limits, and F/fdrive.py writes
  best.circ.txt even for an infeasible circuit with lower G.
- The user's rule: A and AD limits are hard on retained search states, not only on recorded results.

Required from 18:20 UTC for every agent:
1. Every kernel call runs with `repair_keep 1` (no move raises the excess of any single cap; from a start
   inside A/AD, no state leaves them). Use strategies/P1/fdrive_p1.py (copy of F/fdrive.py with
   repair_keep 1 and best.circ.txt written only inside the A/AD caps) or set repair_keep 1 in your own
   driver's kernel config. Starts must be inside the target's A/AD limits (GD above the cap is allowed).
2. For every result you have already reported or saved: add `"path_certified": true|false|"unknown"` to
   its sidecar. true = no kernel stage in its lineage started above a cap without repair_keep (or a trace
   shows no state left A/AD). Otherwise false/unknown.
3. Re-derive every not-certified strict or tradeoff result under repair_keep 1 (same start and staged
   pipeline, any seeds) and record the reproduction (a new found/ file, sidecar `reproduces` = the old file).
   Until then the ledger lists the result as "within limits; search path not certified".

## Ruling 18:45 UTC: construction donors outside the limits
A construction that takes PART of a circuit outside the target's limits (e.g. P7: the front layers of the
48-AND aes-nist-hub-join-g151-a48-gd11-ad4 under a newly built bottom) is allowed when no complete circuit
the builder holds, retains or outputs exceeds the target's A/AD limits: the donor is material, not a search
state. Such results are labelled `donor_outside_limits: <file>` in the sidecar and the ledger shows
"construction from a donor outside the limits; all retained states within limits". The builder's agent must
state in the sidecar that its intermediate complete circuits never exceeded the limits (and how that is
known). Rule 1 ("starts inside the A/AD limits") applies to kernel and other search runs.
