# Independent review: column cloning and retained-coordinate projection

2026-11-14. Independent machine review of the complete
[COLUMN_CLONING.md](../COLUMN_CLONING.md). I reconstructed the deletion lemma,
exact compression theorem, and arbitrary retained-set bound. No circuit search,
enumeration, or computer-driven case elimination was used. This is not formal
verification, human certification, or a literature-novelty assessment.

## Projection deletes a current gate

A required value containing both z and another retained coordinate cannot
already be a coordinate input. Therefore some current gate has coefficient
one in z. Choosing the first such value, rather than the first syntactic read,
handles cancellation correctly: its parents must be the coordinate z itself
and a coefficient-zero value. Projection z=0 replaces the gate by that other
operand. Zero operands and copies can be simplified without adding gates.

Successive projections apply to the surviving circuit, so the deleted gates
are distinct. The argument does not require a private input, a single read,
or an intermediate-support restriction. It also does not infer preservation
of gate parity or any finer resource count.

## Exact identical-column compression

Within a nonzero column class, every target using one member uses all of them.
Keeping one representative guarantees a non-input witness for every other
member until it is projected. The n-t projections therefore delete at least
n-t gates and leave precisely the reduced target map. Computing one group
sum per class and then the reduced map attains the same cost. Singleton
classes require no projection or preliminary gate. Repeated target rows
cause no exception.

Zero input columns may be projected away without changing any target. A
circuit on the remaining coordinates is also a circuit in the original
input domain, so this preserves size exactly. The note explicitly defines
its matrix complexity through nonzero target rows and omits zero rows;
under that convention the zero map costs zero. It does not silently charge
or claim a separately available physical zero output in a different model.

The replacement-by-input-block corollary is the direct repeated application
of the same theorem to positive-size blocks. Its exact overhead concerns
ordinary gate count, not unchanged even rank or unchanged gate populations.

## General retained-coordinate lower bound

The input co-occurrence graph places every target's support within one graph
component. In each component meeting X, growing a forest from all retained
vertices gives each nonretained vertex a parent that remains until that
vertex is deleted. A component missing X gets one temporary root. Decreasing
distance order therefore permits n-|X|-kappa_0 distinct deletions.

For each deletion, an original row containing the chosen graph edge still
contains both current endpoints: projecting other coordinates does not cancel
either coefficient. This supplies the needed non-input target witness.
Afterward, components meeting X give exactly M|X, while a component missing X
has only zero or singleton targets on its temporary root. Such singleton
outputs are free, and no other target contains that root. Projecting those
independent roots away shows that the remaining complexity is exactly that
of M|X under the stated zero-row convention.

This proves the retained-set inequality for arbitrary X, including the
empty set and isolated active coordinates. It does not assume circuits
compute graph components separately. The note correctly does not promote
this general inequality to an equality without a matching construction.

The complete note passes review. Its unrestricted scope, zero/singleton
handling, and distinction between total size and parity resources are clear.
