# Search time and hardware

How long the search ran before each circuit in this folder was found, on what machine, and
how much compute each run used. Numbers marked EXACT are read from the run logs; the others
are estimates, and the table says how each was made. The search's whole development since
June 2026, including runs that found nothing, is in
[search/linear/HISTORY.md](../search/linear/HISTORY.md). The AES S-box circuits found by
BoolFlux have [their own section](#aes-s-box-circuits); BoolFlux's development is in
[search/nonlinear/HISTORY.md](../search/nonlinear/HISTORY.md).

## Hardware

Every run that produced a circuit here ran on one laptop:

| | |
|---|---|
| CPU | Intel Core i7-13700H: 14 cores (6 performance cores with 2 threads each, 8 efficiency cores), 20 hardware threads |
| Memory | 64 GB (31 GB visible to WSL2); not recorded by the runs |
| OS | Windows 11 with WSL2, Ubuntu 24.04 (kernel 6.6.114.1-microsoft-standard-WSL2) |
| Python | 3.10.18 for v1–v4, 3.12.3 for v5–v8 and BoolFlux; every worker is one single-threaded process |
| C compiler | gcc 13.3.0, for BoolFlux's kernels |
| GPU, cloud | none used for these runs |

"20 workers" therefore means 20 processes on 20 hardware threads (14 physical cores), not
20 physical cores. The run logs of v2–v8 record the CPU model, the 20 logical CPUs and the
kernel; v1 records only the CPU count.

## How the numbers are measured

- **Found after**: time from the start of the run to the circuit, on the run's wall clock
  (sessions of a resumed run added up).
- **Finder CPU**: CPU time the worker that found it had used by then (measured from v5 on;
  for v1–v4, assumed one busy thread).
- **Run worker-h**: workers × wall time of the whole run, also when the run covered several
  maps; **CPU-h**: measured process CPU of all workers (v5 on).
- **Clock**: under load the WSL2 clock runs fast and is stepped back to the Windows clock
  every 30–60 s. A run budget of "1 h" on the monotonic clock was 0.91–1.00 h of real time;
  the times here use the wall clock, the better estimate of real time. Measured CPU may be
  inflated by up to the same 9%.
- **Oversubscribed**: more workers than the 20 hardware threads, counting other runs active
  on the machine at the same time.

## Runs

| Run | Version | Start (UTC) | Wall time | Workers | Worker-h | CPU-h | Oversubscribed | Circuits |
|---|---|---|---:|---:|---:|---:|---|---:|
| three-targets20 | v2 | 2026-10-24 16:25 | 69.9 h | 20 | 1,398.7 | — | no | 1 |
| joltik-depth-foxmu8-15 | v3 | 2026-10-27 15:03 | 22.2 h | 15 | 332.4 | — | no | 2 |
| rerun-invmixcolumns | v6 | 2026-10-29 09:45 | 1.9 h | 20 | 38.1 | 37.8 | no | 4 |
| rerun-aes_sbox_bottom | v6 | 2026-10-29 11:39 | 57 min | 20 | 18.9 | 18.8 | no | 2 |
| rerun-fox_mu4 | v6 | 2026-10-29 12:36 | 57 min | 20 | 18.9 | 18.6 | no | 4 |
| rerun-joltik | v6 | 2026-10-29 13:33 | 56 min | 20 | 18.8 | 18.6 | no | 4 |
| rerun-fox_mu8 | v6 | 2026-10-29 14:29 | 56 min | 20 | 18.8 | 18.4 | no | 2 |
| bench-mixcolumns | v7 | 2026-10-29 20:01 | 55 min | 20 | 18.4 | 17.4 | yes (27 workers) | 2 |
| bench-invmixcolumns | v7 | 2026-10-29 20:57 | 55 min | 20 | 18.4 | 17.5 | yes (27 workers) | 2 |
| gap-2026-10-30 | v7 | 2026-10-29 23:31 | 55 min | 12 | 10.9 | 10.9 | no | 6 |
| nist-aria | v8 | 2026-10-30 03:36 | 1.0 h | 20 | 20.0 | 19.7 | no | 4 |
| nist-twofish | v8 | 2026-10-30 04:36 | 1.0 h | 20 | 20.0 | 19.7 | no | 6 |
| nist-grostl | v8 | 2026-10-30 05:36 | 59 min | 20 | 19.8 | 19.2 | no | 9 |
| nist-clefia-m1 | v8 | 2026-10-30 06:36 | 59 min | 20 | 19.6 | 19.3 | no | 7 |
| nist-batch-64 | v8 | 2026-10-30 07:34 | 59 min | 20 | 19.5 | 18.9 | no | 38 |
| nist-batch-32a | v8 | 2026-10-30 08:33 | 58 min | 22 | 21.4 | 19.1 | yes (22 workers) | 28 |
| nist-batch-32b | v8 | 2026-10-30 09:31 | 58 min | 22 | 21.3 | 19.0 | yes (22 workers) | 40 |
| nist-batch-16a | v8 | 2026-10-30 10:29 | 29 min | 18 | 8.67 | 8.65 | no | 16 |
| nist-batch-16b | v8 | 2026-10-30 10:58 | 29 min | 16 | 7.69 | 7.68 | no | 10 |
| aes-lowdepth | v8 | 2026-10-31 01:24 | 7.6 h | 13 | 98.4 | 98.1 | no | 1 |
| gaps16 | v8 | 2026-10-31 01:24 | 2.9 h | 6 | 17.2 | 17.2 | no | 3 |
| wide64 | v8 | 2026-10-31 04:16 | 4.7 h | 6 | 28.2 | 28.1 | no | 8 |
| control | v8 | 2026-10-31 15:00 | 45.5 h | 10 | 454.8 | 449.2 | no | 1 |
| adopt | v9 prototype | 2026-10-31 15:00 | 45.5 h | 10 | 454.8 | 449.3 | no | 1 |
| x1a-fresh-vs-nist | v8 | 2026-11-07 06:16 | 1.0 h | 8 | 8.0 | 8.6 | yes (shared machine) | 11 |
| x1b-fresh-vs-nist | v8 | 2026-11-07 07:22 | 1.0 h | 8 | 8.0 | 8.7 | yes (shared machine) | 4 |
| predtest-pt1 | v8 | 2026-11-07 08:28 | 2.0 h | 6 | 12.0 | 13.0 | yes (shared machine) | 5 |
| predtest-pt2 | v8 | 2026-11-07 10:39 | 2.0 h | 8 | 16.0 | 17.6 | yes (shared machine) | 6 |
| sweep-sw1 | v8 | 2026-11-07 12:52 | 1.0 h | 6 | 6.0 | 6.7 | yes (shared machine) | 6 |
| sweep-sw2 | v8 | 2026-11-07 13:58 | 1.0 h | 6 | 6.0 | 6.7 | yes (shared machine) | 12 |

Together: 30 runs, about 3,150 worker-hours, for 208 circuits. v2–v3 used about 1,730 of those worker-hours for 3 circuits; v6–v8 used about 980 for 204, and the v9 prototype about 455 for 1. The v1 run long20 (about 796 worker-hours) and the v4 run invmixcolumns-13 (18.5), whose 89@4 and 168@5 were replaced on 2026-10-31 and 2026-11-02, and another 21 logged runs of 2026-10-28 to 10-30 (310 worker-hours) produced no circuit kept here; they are not in the
totals. Compute before v1 is in [search/linear/HISTORY.md](../search/linear/HISTORY.md#compute).

## Circuits

| Circuit | Version | Run | Found after | Finder CPU | Run worker-h | Status | Note |
| [anubis-clefia-m0 92@6](anubis-clefia-m0/anubis-clefia-m0-xor92-depth6.circ.txt) | v8 | predtest-pt2 | 18 min | 19 min | 16.0 | exact | from our 92@8 |
| [anubis-clefia-m0 91@8](anubis-clefia-m0/anubis-clefia-m0-xor91-depth8.circ.txt) | v8 | predtest-pt2 | 10 min | 11 min | 16.0 | exact | from our 92@8 |
| [bkl16-8x8-gf256 439@9](bkl16-8x8-gf256/bkl16-8x8-gf256-xor439-depth9.circ.txt) | v8 | sweep-sw1 | 9 min | 9 min | 6.0 | exact | from our 442@10 |
| [fox-mu8 502@10](fox-mu8/fox-mu8-xor502-depth10.circ.txt) | v8 | sweep-sw1 | 34 min | 38 min | 6.0 | exact | from our 505@11 |
| [fox-mu8 500@11](fox-mu8/fox-mu8-xor500-depth11.circ.txt) | v8 | predtest-pt2 | 1.6 h | 1.8 h | 16.0 | exact | from our 505@11 |
| [grostl 404@10](grostl/grostl-xor404-depth10.circ.txt) | v8 | x1a-fresh-vs-nist | 15 s | < 1 min | 8.0 | exact | from NIST 410@12 |
| [grostl 364@11](grostl/grostl-xor364-depth11.circ.txt) | v8 | x1a-fresh-vs-nist | 55 min | 58 min | 8.0 | exact | from NIST 410@12, restarted from the worker's best |
| [grostl 349@15](grostl/grostl-xor349-depth15.circ.txt) | v8 | sweep-sw1 | 14 min | 16 min | 6.0 | exact | from our 350@16 |
| [jpst17-4x4-gf256 80@5](jpst17-4x4-gf256/jpst17-4x4-gf256-xor80-depth5.circ.txt) | v8 | x1b-fresh-vs-nist | 9 min | 9 min | 8.0 | exact | from NIST 82@7 |
| [jpst17-8x8-gf256-inv 494@10](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor494-depth10.circ.txt) | v8 | sweep-sw1 | 26 min | 28 min | 6.0 | exact | from our 493@11, restarted from the worker's best |
| [khazad 344@14](khazad/khazad-xor344-depth14.circ.txt) | v8 | predtest-pt2 | 45 min | 48 min | 16.0 | exact | from our 345@15 |
| [khazad 340@15](khazad/khazad-xor340-depth15.circ.txt) | v8 | predtest-pt2 | 50 min | 55 min | 16.0 | exact | from NIST 366@18 |
| [klsw17-m-8x8-gf16-0x13-inv 164@10](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor164-depth10.circ.txt) | v8 | sweep-sw2 | 19 min | 21 min | 6.0 | exact | from our 163@12, restarted from the worker's best |
| [klsw17-m-8x8-gf16-0x13-inv 163@11](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor163-depth11.circ.txt) | v8 | sweep-sw2 | 13 min | 15 min | 6.0 | exact | from our 163@12, restarted from the worker's best |
| [klsw17-m-8x8-gf256 346@8](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor346-depth8.circ.txt) | v8 | sweep-sw2 | 4 s | < 1 min | 6.0 | exact | from our 347@6 |
| [klsw17-m-8x8-gf256 327@9](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor327-depth9.circ.txt) | v8 | sweep-sw2 | 22 min | 25 min | 6.0 | exact | from our 347@6, restarted from the worker's best |
| [klsw17-m-8x8-gf256 321@10](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor321-depth10.circ.txt) | v8 | sweep-sw2 | 58 min | 1.1 h | 6.0 | exact | from our 347@6, restarted from the worker's best |
| [klsw17-m-8x8-gf256-inv 868@5](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor868-depth5.circ.txt) | v8 | x1a-fresh-vs-nist | 23 s | < 1 min | 8.0 | exact | fresh roots |
| [klsw17-m-8x8-gf256-inv 338@11](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor338-depth11.circ.txt) | v8 | predtest-pt1 | 34 min | 36 min | 12.0 | exact | from NIST 368@12, restarted from the worker's best |
| [klsw17-m-8x8-gf256-inv 327@12](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor327-depth12.circ.txt) | v8 | x1a-fresh-vs-nist | 37 min | 39 min | 8.0 | exact | from NIST 368@12, restarted from the worker's best |
| [klsw17-m-8x8-gf256-inv 326@13](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor326-depth13.circ.txt) | v8 | x1a-fresh-vs-nist | 50 min | 53 min | 8.0 | exact | from NIST 368@12, restarted from the worker's best |
| [ls16-8x8-gf256 403@8](ls16-8x8-gf256/ls16-8x8-gf256-xor403-depth8.circ.txt) | v8 | sweep-sw2 | 42 min | 46 min | 6.0 | exact | from our 404@8 |
| [lw16-4x4-gf256-inv-circ 126@3](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor126-depth3.circ.txt) | v8 | x1a-fresh-vs-nist | 0 s | < 1 min | 8.0 | exact | fresh roots |
| [skop15-4x4-gf256-inv 89@5](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor89-depth5.circ.txt) | v8 | predtest-pt2 | 1.8 h | 2.0 h | 16.0 | exact | from our 88@6 |
| [skop15-8x8-gf16 196@7](skop15-8x8-gf16/skop15-8x8-gf16-xor196-depth7.circ.txt) | v8 | x1a-fresh-vs-nist | 7 s | < 1 min | 8.0 | exact | fresh roots |
| [skop15-8x8-gf16 174@8](skop15-8x8-gf16/skop15-8x8-gf16-xor174-depth8.circ.txt) | v8 | x1a-fresh-vs-nist | 52 s | < 1 min | 8.0 | exact | fresh roots |
| [skop15-8x8-gf16 166@9](skop15-8x8-gf16/skop15-8x8-gf16-xor166-depth9.circ.txt) | v8 | x1a-fresh-vs-nist | 7 min | 8 min | 8.0 | exact | fresh roots |
| [skop15-8x8-gf16 158@10](skop15-8x8-gf16/skop15-8x8-gf16-xor158-depth10.circ.txt) | v8 | x1a-fresh-vs-nist | 42 min | 46 min | 8.0 | exact | fresh roots |
| [skop15-8x8-gf16 157@11](skop15-8x8-gf16/skop15-8x8-gf16-xor157-depth11.circ.txt) | v8 | x1a-fresh-vs-nist | 32 min | 34 min | 8.0 | exact | fresh roots |
| [skop15-8x8-gf256 417@8](skop15-8x8-gf256/skop15-8x8-gf256-xor417-depth8.circ.txt) | v8 | sweep-sw2 | 19 min | 22 min | 6.0 | exact | from our 418@8 |
| [skop15-8x8-gf256 416@9](skop15-8x8-gf256/skop15-8x8-gf256-xor416-depth9.circ.txt) | v8 | sweep-sw2 | 35 min | 38 min | 6.0 | exact | from our 418@8 |
| [skop15-8x8-gf256-inv 323@12](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor323-depth12.circ.txt) | v8 | sweep-sw2 | 59 min | 1.1 h | 6.0 | exact | from our 331@13, restarted from the worker's best |
| [skop15-8x8-gf256-inv 322@13](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor322-depth13.circ.txt) | v8 | sweep-sw2 | 44 min | 49 min | 6.0 | exact | from our 331@13, restarted from the worker's best |
| [small-scale-aes 63@3](small-scale-aes/small-scale-aes-xor63-depth3.circ.txt) | v8 | x1b-fresh-vs-nist | 0 s | < 1 min | 8.0 | exact | fresh roots |
| [ss16-4x4-gf256 103@3](ss16-4x4-gf256/ss16-4x4-gf256-xor103-depth3.circ.txt) | v8 | x1b-fresh-vs-nist | 13 s | < 1 min | 8.0 | exact | fresh roots |
| [ss16-4x4-gf256 96@5](ss16-4x4-gf256/ss16-4x4-gf256-xor96-depth5.circ.txt) | v8 | x1b-fresh-vs-nist | 3 min | 3 min | 8.0 | exact | fresh roots |
| [ss17-8x8-gf16 174@8](ss17-8x8-gf16/ss17-8x8-gf16-xor174-depth8.circ.txt) | v8 | predtest-pt1 | 56 s | < 1 min | 12.0 | exact | from NIST 178@10 |
| [ss17-8x8-gf16 164@9](ss17-8x8-gf16/ss17-8x8-gf16-xor164-depth9.circ.txt) | v8 | predtest-pt1 | 12 min | 13 min | 12.0 | exact | from NIST 178@10 |
| [ss17-8x8-gf16 161@10](ss17-8x8-gf16/ss17-8x8-gf16-xor161-depth10.circ.txt) | v8 | predtest-pt1 | 1.2 h | 1.3 h | 12.0 | exact | from NIST 178@10, restarted from the worker's best |
| [ss17-8x8-gf16 160@11](ss17-8x8-gf16/ss17-8x8-gf16-xor160-depth11.circ.txt) | v8 | predtest-pt1 | 1.5 h | 1.6 h | 12.0 | exact | from NIST 178@10, restarted from the worker's best |
| [ss17-8x8-gf256 390@8](ss17-8x8-gf256/ss17-8x8-gf256-xor390-depth8.circ.txt) | v8 | sweep-sw2 | 27 min | 31 min | 6.0 | exact | from our 392@8 |
| [ss17-8x8-gf256 389@10](ss17-8x8-gf256/ss17-8x8-gf256-xor389-depth10.circ.txt) | v8 | sweep-sw2 | 47 min | 53 min | 6.0 | exact | from our 392@8 |
| [whirlpool-maelstrom 391@9](whirlpool-maelstrom/whirlpool-maelstrom-xor391-depth9.circ.txt) | v8 | sweep-sw1 | 51 min | 56 min | 6.0 | exact | from our 394@9 |
| [whirlpool-maelstrom 390@10](whirlpool-maelstrom/whirlpool-maelstrom-xor390-depth10.circ.txt) | v8 | sweep-sw1 | 44 min | 48 min | 6.0 | exact | from our 394@9 |
|---|---|---|---:|---:|---:|---|---|
| [aes-invmixcolumns 118@5](aes-invmixcolumns/aes-invmixcolumns-xor118-depth5.circ.txt) | v9 prototype | adopt | 42.3 h | 41.8 h | 454.8 | exact | from our 168@5; adopted another worker's 119@5 4.5 s before |
| [aes-invmixcolumns 104@6](aes-invmixcolumns/aes-invmixcolumns-xor104-depth6.circ.txt) | v8 | aes-lowdepth | 1.3 h | 1.3 h | 98.4 | exact | from NIST 107@6, restarted from another worker's 105@6 (from NIST 106@6) |
| [aes-invmixcolumns 101@7](aes-invmixcolumns/aes-invmixcolumns-xor101-depth7.circ.txt) | v7 | gap-2026-10-30 | 39 min | 39 min | 10.9 | exact |  |
| [aes-invmixcolumns 96@8](aes-invmixcolumns/aes-invmixcolumns-xor96-depth8.circ.txt) | v6 | rerun-invmixcolumns | 15 min | 15 min | 38.1 | exact |  |
| [aes-invmixcolumns 94@9](aes-invmixcolumns/aes-invmixcolumns-xor94-depth9.circ.txt) | v7 | bench-invmixcolumns | 8 min | 8 min | 18.4 | exact |  |
| [aes-invmixcolumns 93@10](aes-invmixcolumns/aes-invmixcolumns-xor93-depth10.circ.txt) | v7 | bench-invmixcolumns | 31 min | 30 min | 18.4 | exact |  |
| [aes-invmixcolumns 92@11](aes-invmixcolumns/aes-invmixcolumns-xor92-depth11.circ.txt) | v7 | gap-2026-10-30 | 3 min | 3 min | 10.9 | exact |  |
| [aes-invmixcolumns 90@12](aes-invmixcolumns/aes-invmixcolumns-xor90-depth12.circ.txt) | v6 | rerun-invmixcolumns | 1.8 h | 1.8 h | 38.1 | exact |  |
| [aes-invmixcolumns 89@15](aes-invmixcolumns/aes-invmixcolumns-xor89-depth15.circ.txt) | v6 | rerun-invmixcolumns | 40 min | 39 min | 38.1 | exact |  |
| [aes-invmixcolumns 88@17](aes-invmixcolumns/aes-invmixcolumns-xor88-depth17.circ.txt) | v6 | rerun-invmixcolumns | 1.2 h | 1.2 h | 38.1 | exact |  |
| [aes-mixcolumns 97@3](aes-mixcolumns/aes-mixcolumns-xor97-depth3.circ.txt) | v7 | bench-mixcolumns | 10 s | 10 s | 18.4 | exact | built by the `anneal3` constructor; no search move |
| [aes-mixcolumns 89@4](aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt) | v8 | control | 15 min | 14 min | 454.8 | exact | from our July 91@4; one remove-one move, replayable from its dossier |
| [aes-mixcolumns 88@5](aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt) | v7 | bench-mixcolumns | 35 min | 33 min | 18.4 | exact |  |
| [aes-sbox-bottom 29@4](aes-sbox-bottom/aes-sbox-bottom-xor29-depth4.circ.txt) | v6 | rerun-aes_sbox_bottom | 4 s | 4 s | 18.9 | exact |  |
| [aes-sbox-bottom 28@5](aes-sbox-bottom/aes-sbox-bottom-xor28-depth5.circ.txt) | v6 | rerun-aes_sbox_bottom | 29 min | 28 min | 18.9 | exact |  |
| [anubis-clefia-m0 95@5](anubis-clefia-m0/anubis-clefia-m0-xor95-depth5.circ.txt) | v8 | nist-batch-32a | 25 min | 22 min | 21.4 | exact |  |
| [aria 416@3](aria/aria-xor416-depth3.circ.txt) | v8 | nist-aria | 1 min | 1 min | 20.0 | exact | built by the `anneal3` constructor; no search move |
| [aria 384@4](aria/aria-xor384-depth4.circ.txt) | v8 | nist-aria | 3 min | 3 min | 20.0 | exact |  |
| [aria 383@8](aria/aria-xor383-depth8.circ.txt) | v8 | nist-aria | 15 min | 14 min | 20.0 | exact |  |
| [aria 382@10](aria/aria-xor382-depth10.circ.txt) | v8 | nist-aria | 35 min | 34 min | 20.0 | exact |  |
| [bkl16-4x4-gf16 40@4](bkl16-4x4-gf16/bkl16-4x4-gf16-xor40-depth4.circ.txt) | v8 | nist-batch-16a | 43 s | 42 s | 8.67 | exact |  |
| [bkl16-4x4-gf256 102@4](bkl16-4x4-gf256/bkl16-4x4-gf256-xor102-depth4.circ.txt) | v8 | nist-batch-32a | 3 min | 3 min | 21.4 | exact |  |
| [bkl16-4x4-gf256 101@5](bkl16-4x4-gf256/bkl16-4x4-gf256-xor101-depth5.circ.txt) | v8 | nist-batch-32a | 50 min | 45 min | 21.4 | exact |  |
| [bkl16-8x8-gf256 725@4](bkl16-8x8-gf256/bkl16-8x8-gf256-xor725-depth4.circ.txt) | v8 | nist-batch-64 | 3 s | 3 s | 19.5 | exact | built by the `naive` constructor; no search move |
| [bkl16-8x8-gf256 494@5](bkl16-8x8-gf256/bkl16-8x8-gf256-xor494-depth5.circ.txt) | v8 | nist-batch-64 | 58 min | 55 min | 19.5 | exact |  |
| [bkl16-8x8-gf256 456@8](bkl16-8x8-gf256/bkl16-8x8-gf256-xor456-depth8.circ.txt) | v8 | nist-batch-64 | 8 min | 8 min | 19.5 | exact |  |
| [clefia-m1 113@4](clefia-m1/clefia-m1-xor113-depth4.circ.txt) | v8 | nist-clefia-m1 | 20 min | 20 min | 19.6 | exact |  |
| [clefia-m1 105@5](clefia-m1/clefia-m1-xor105-depth5.circ.txt) | v8 | nist-clefia-m1 | 6 min | 6 min | 19.6 | exact |  |
| [clefia-m1 103@6](clefia-m1/clefia-m1-xor103-depth6.circ.txt) | v8 | nist-clefia-m1 | 1 min | 1 min | 19.6 | exact |  |
| [clefia-m1 102@7](clefia-m1/clefia-m1-xor102-depth7.circ.txt) | v8 | nist-clefia-m1 | 5 min | 5 min | 19.6 | exact |  |
| [clefia-m1 101@8](clefia-m1/clefia-m1-xor101-depth8.circ.txt) | v8 | nist-clefia-m1 | 9 min | 9 min | 19.6 | exact |  |
| [clefia-m1 100@9](clefia-m1/clefia-m1-xor100-depth9.circ.txt) | v8 | nist-clefia-m1 | 23 min | 23 min | 19.6 | exact |  |
| [clefia-m1 99@10](clefia-m1/clefia-m1-xor99-depth10.circ.txt) | v8 | nist-clefia-m1 | 23 min | 22 min | 19.6 | exact |  |
| [fides-midori-mantis 24@2](fides-midori-mantis/fides-midori-mantis-xor24-depth2.circ.txt) | v8 | nist-batch-16a | 0.2 s | 0.1 s | 8.67 | exact |  |
| [fox-mu4 141@4](fox-mu4/fox-mu4-xor141-depth4.circ.txt) | v2 | three-targets20 | 40.0 h | ~40.0 h | 1,398.7 | exact time, CPU estimated |  |
| [fox-mu4 128@5](fox-mu4/fox-mu4-xor128-depth5.circ.txt) | v7 | gap-2026-10-30 | 54 min | 54 min | 10.9 | exact |  |
| [fox-mu4 122@6](fox-mu4/fox-mu4-xor122-depth6.circ.txt) | v6 | rerun-fox_mu4 | 42 min | 41 min | 18.9 | exact |  |
| [fox-mu4 121@7](fox-mu4/fox-mu4-xor121-depth7.circ.txt) | v6 | rerun-fox_mu4 | 9 min | 9 min | 18.9 | exact |  |
| [fox-mu4 120@8](fox-mu4/fox-mu4-xor120-depth8.circ.txt) | v6 | rerun-fox_mu4 | 7 min | 7 min | 18.9 | exact |  |
| [fox-mu4 119@9](fox-mu4/fox-mu4-xor119-depth9.circ.txt) | v6 | rerun-fox_mu4 | 8 min | 8 min | 18.9 | exact |  |
| [fox-mu8 1078@5](fox-mu8/fox-mu8-xor1078-depth5.circ.txt) | v7 | gap-2026-10-30 | 51 min | 51 min | 10.9 | exact | + polish of 1080@5 |
| [fox-mu8 605@6](fox-mu8/fox-mu8-xor605-depth6.circ.txt) | v7 | gap-2026-10-30 | 6 min | 6 min | 10.9 | exact |  |
| [fox-mu8 599@7](fox-mu8/fox-mu8-xor599-depth7.circ.txt) | v3 | joltik-depth-foxmu8-15 | 4.2 h | ~4.2 h | 332.4 | exact time, CPU estimated | + polish of 601@7 |
| [fox-mu8 539@8](fox-mu8/fox-mu8-xor539-depth8.circ.txt) | v3 | joltik-depth-foxmu8-15 | 21.9 h | ~21.9 h | 332.4 | exact time, CPU estimated | + polish of 540@8 |
| [fox-mu8 512@9](fox-mu8/fox-mu8-xor512-depth9.circ.txt) | v7 | gap-2026-10-30 | 10 min | 10 min | 10.9 | exact |  |
| [grostl 502@5](grostl/grostl-xor502-depth5.circ.txt) | v8 | nist-grostl | 58 min | 56 min | 19.8 | exact |  |
| [grostl 455@8](grostl/grostl-xor455-depth8.circ.txt) | v8 | nist-grostl | 4 min | 4 min | 19.8 | exact |  |
| [grostl 362@13](grostl/grostl-xor362-depth13.circ.txt) | v8 | nist-grostl | 59 min | 57 min | 19.8 | exact |  |
| [grostl 360@14](grostl/grostl-xor360-depth14.circ.txt) | v8 | nist-grostl | 59 min | 57 min | 19.8 | exact |  |
| [joltik 46@3](joltik/joltik-xor46-depth3.circ.txt) | v6 | rerun-joltik | 44 min | 44 min | 18.8 | exact | built by the `anneal3` constructor; no search move; from a checkpoint |
| [joltik 44@4](joltik/joltik-xor44-depth4.circ.txt) | v6 | rerun-joltik | 41 min | 41 min | 18.8 | exact |  |
| [joltik 43@6](joltik/joltik-xor43-depth6.circ.txt) | v6 | rerun-joltik | 12 s | 11 s | 18.8 | exact |  |
| [joltik 42@9](joltik/joltik-xor42-depth9.circ.txt) | v6 | rerun-joltik | 4 min | 4 min | 18.8 | exact |  |
| [jpst17-4x4-gf16 41@4](jpst17-4x4-gf16/jpst17-4x4-gf16-xor41-depth4.circ.txt) | v8 | nist-batch-16a | 2 s | 2 s | 8.67 | exact |  |
| [jpst17-4x4-gf16 40@5](jpst17-4x4-gf16/jpst17-4x4-gf16-xor40-depth5.circ.txt) | v8 | nist-batch-16a | 4 s | 4 s | 8.67 | exact |  |
| [jpst17-4x4-gf16 39@6](jpst17-4x4-gf16/jpst17-4x4-gf16-xor39-depth6.circ.txt) | v8 | nist-batch-16a | 6 s | 6 s | 8.67 | exact |  |
| [jpst17-4x4-gf16-inv 43@4](jpst17-4x4-gf16-inv/jpst17-4x4-gf16-inv-xor43-depth4.circ.txt) | v8 | nist-batch-16a | 11 s | 10 s | 8.67 | exact |  |
| [jpst17-4x4-gf16-inv 41@5](jpst17-4x4-gf16-inv/jpst17-4x4-gf16-inv-xor41-depth5.circ.txt) | v8 | nist-batch-16a | 47 s | 45 s | 8.67 | exact |  |
| [jpst17-4x4-gf16-inv 40@6](jpst17-4x4-gf16-inv/jpst17-4x4-gf16-inv-xor40-depth6.circ.txt) | v8 | nist-batch-16a | 39 s | 37 s | 8.67 | exact |  |
| [jpst17-4x4-gf256 82@4](jpst17-4x4-gf256/jpst17-4x4-gf256-xor82-depth4.circ.txt) | v8 | nist-batch-32a | 47 s | 35 s | 21.4 | exact |  |
| [jpst17-4x4-gf256 78@6](jpst17-4x4-gf256/jpst17-4x4-gf256-xor78-depth6.circ.txt) | v8 | nist-batch-32a | 6 min | 5 min | 21.4 | exact |  |
| [jpst17-4x4-gf256-inv 94@3](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor94-depth3.circ.txt) | v8 | nist-batch-32a | 35 min | 31 min | 21.4 | exact | searched from an `anneal3` start |
| [jpst17-4x4-gf256-inv 84@4](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor84-depth4.circ.txt) | v8 | nist-batch-32a | 45 min | 40 min | 21.4 | exact | searched from an `anneal3` start |
| [jpst17-4x4-gf256-inv 82@5](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor82-depth5.circ.txt) | v8 | gaps16 | 34 s | < 1 min | 17.2 | exact | searched from our 84@4 |
| [jpst17-4x4-gf256-inv 80@6](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor80-depth6.circ.txt) | v8 | gaps16 | 9 min | 9 min | 17.2 | exact |  |
| [jpst17-8x8-gf256-inv 1027@5](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor1027-depth5.circ.txt) | v8 | nist-batch-64 | 10 s | 9 s | 19.5 | exact | built by the `naive` constructor; no search move |
| [jpst17-8x8-gf256-inv 641@6](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor641-depth6.circ.txt) | v8 | nist-batch-64 | 57 min | 53 min | 19.5 | exact |  |
| [jpst17-8x8-gf256-inv 493@11](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor493-depth11.circ.txt) | v8 | nist-batch-64 | 54 min | 52 min | 19.5 | exact |  |
| [jpst17-8x8-gf256-inv 492@12](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor492-depth12.circ.txt) | v8 | nist-batch-64 | 58 min | 56 min | 19.5 | exact |  |
| [khazad 1055@5](khazad/khazad-xor1055-depth5.circ.txt) | v8 | wide64 | 22 min | 22 min | 28.2 | exact | built by the `naive` constructor; no search move |
| [khazad 478@6](khazad/khazad-xor478-depth6.circ.txt) | v8 | nist-batch-64 | 54 min | 52 min | 19.5 | exact |  |
| [khazad 477@8](khazad/khazad-xor477-depth8.circ.txt) | v8 | wide64 | 30 s | < 1 min | 28.2 | exact | searched from our 478@6 |
| [khazad 460@9](khazad/khazad-xor460-depth9.circ.txt) | v8 | wide64 | 15 min | 14 min | 28.2 | exact |  |
| [khazad 433@10](khazad/khazad-xor433-depth10.circ.txt) | v8 | wide64 | 4.2 h | 4.2 h | 28.2 | exact |  |
| [khazad 432@11](khazad/khazad-xor432-depth11.circ.txt) | v8 | wide64 | 4.5 h | 4.4 h | 28.2 | exact |  |
| [klsw17-m-4x4-gf16 36@4](klsw17-m-4x4-gf16/klsw17-m-4x4-gf16-xor36-depth4.circ.txt) | v8 | nist-batch-16a | 4 s | 3 s | 8.67 | exact |  |
| [klsw17-m-4x4-gf16 32@6](klsw17-m-4x4-gf16/klsw17-m-4x4-gf16-xor32-depth6.circ.txt) | v8 | nist-batch-16a | 2 s | 1 s | 8.67 | exact |  |
| [klsw17-m-4x4-gf256 72@4](klsw17-m-4x4-gf256/klsw17-m-4x4-gf256-xor72-depth4.circ.txt) | v8 | nist-batch-32a | 8 s | 7 s | 21.4 | exact |  |
| [klsw17-m-4x4-gf256 64@6](klsw17-m-4x4-gf256/klsw17-m-4x4-gf256-xor64-depth6.circ.txt) | v8 | nist-batch-32a | 4 s | 4 s | 21.4 | exact |  |
| [klsw17-m-4x4-gf256-inv 76@4](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor76-depth4.circ.txt) | v8 | nist-batch-32a | 12 s | 10 s | 21.4 | exact |  |
| [klsw17-m-4x4-gf256-inv 75@5](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor75-depth5.circ.txt) | v8 | nist-batch-32a | 14 min | 13 min | 21.4 | exact |  |
| [klsw17-m-4x4-gf256-inv 74@6](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor74-depth6.circ.txt) | v8 | nist-batch-32a | 3 min | 3 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13 178@6](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor178-depth6.circ.txt) | v8 | nist-batch-32a | 26 min | 23 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13 171@9](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor171-depth9.circ.txt) | v8 | nist-batch-32a | 10 s | 8 s | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13 161@10](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor161-depth10.circ.txt) | v8 | nist-batch-32a | 19 min | 17 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13-inv 191@6](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor191-depth6.circ.txt) | v8 | nist-batch-32a | 56 min | 50 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13-inv 162@13](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor162-depth13.circ.txt) | v8 | nist-batch-32a | 54 min | 49 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf256 347@6](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor347-depth6.circ.txt) | v8 | nist-batch-64 | 56 min | 54 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 490@6](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor490-depth6.circ.txt) | v8 | nist-batch-64 | 52 min | 50 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 325@16](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor325-depth16.circ.txt) | v8 | nist-batch-64 | 56 min | 55 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 324@21](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor324-depth21.circ.txt) | v8 | nist-batch-64 | 55 min | 54 min | 19.5 | exact |  |
| [ls16-4x4-gf16 43@3](ls16-4x4-gf16/ls16-4x4-gf16-xor43-depth3.circ.txt) | v8 | nist-batch-16a | 4 s | 3 s | 8.67 | exact |  |
| [ls16-4x4-gf256 103@4](ls16-4x4-gf256/ls16-4x4-gf256-xor103-depth4.circ.txt) | v8 | nist-batch-32a | 16 min | 14 min | 21.4 | exact |  |
| [ls16-8x8-gf256 411@5](ls16-8x8-gf256/ls16-8x8-gf256-xor411-depth5.circ.txt) | v8 | nist-batch-64 | 46 min | 45 min | 19.5 | exact |  |
| [lw16-4x4-gf16 43@3](lw16-4x4-gf16/lw16-4x4-gf16-xor43-depth3.circ.txt) | v8 | nist-batch-16a | 7 s | 7 s | 8.67 | exact |  |
| [lw16-4x4-gf16-inv 44@4](lw16-4x4-gf16-inv/lw16-4x4-gf16-inv-xor44-depth4.circ.txt) | v8 | nist-batch-16a | 3 min | 3 min | 8.67 | exact |  |
| [lw16-4x4-gf16-inv 43@7](lw16-4x4-gf16-inv/lw16-4x4-gf16-inv-xor43-depth7.circ.txt) | v8 | nist-batch-16a | 7 min | 7 min | 8.67 | exact |  |
| [lw16-4x4-gf16-inv 42@9](lw16-4x4-gf16-inv/lw16-4x4-gf16-inv-xor42-depth9.circ.txt) | v8 | nist-batch-16a | 21 min | 21 min | 8.67 | exact |  |
| [lw16-4x4-gf256 102@3](lw16-4x4-gf256/lw16-4x4-gf256-xor102-depth3.circ.txt) | v8 | nist-batch-32a | 33 min | 30 min | 21.4 | exact |  |
| [lw16-4x4-gf256 96@4](lw16-4x4-gf256/lw16-4x4-gf256-xor96-depth4.circ.txt) | v8 | nist-batch-32a | 4 min | 4 min | 21.4 | exact |  |
| [lw16-4x4-gf256-inv-circ 86@4](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor86-depth4.circ.txt) | v8 | nist-batch-32a | 9 min | 8 min | 21.4 | exact |  |
| [lw16-4x4-gf256-inv-circ 82@5](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor82-depth5.circ.txt) | v8 | nist-batch-32a | 40 min | 36 min | 21.4 | exact |  |
| [lw16-4x4-gf256-inv-circ 81@10](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor81-depth10.circ.txt) | v8 | nist-batch-32a | 52 min | 47 min | 21.4 | exact |  |
| [lw16-4x4-gf256-inv-had 85@4](lw16-4x4-gf256-inv-had/lw16-4x4-gf256-inv-had-xor85-depth4.circ.txt) | v8 | nist-batch-32b | 54 s | 42 s | 21.3 | exact |  |
| [lw16-4x4-gf256-inv-had 84@5](lw16-4x4-gf256-inv-had/lw16-4x4-gf256-inv-had-xor84-depth5.circ.txt) | v8 | nist-batch-32b | 1 s | 0.7 s | 21.3 | exact |  |
| [pride-l0 24@2](pride-l0/pride-l0-xor24-depth2.circ.txt) | v8 | nist-batch-16a | 0.2 s | 0.1 s | 8.67 | exact | the fides-midori-mantis circuit (same matrix) |
| [prince-m0 24@2](prince-m0/prince-m0-xor24-depth2.circ.txt) | v8 | nist-batch-16b | 0.3 s | 0.2 s | 7.69 | exact |  |
| [skop15-4x4-gf16 45@4](skop15-4x4-gf16/skop15-4x4-gf16-xor45-depth4.circ.txt) | v8 | nist-batch-16b | 33 s | 31 s | 7.69 | exact |  |
| [skop15-4x4-gf16 43@5](skop15-4x4-gf16/skop15-4x4-gf16-xor43-depth5.circ.txt) | v8 | nist-batch-16b | 15 s | 15 s | 7.69 | exact |  |
| [skop15-4x4-gf16-inv 44@4](skop15-4x4-gf16-inv/skop15-4x4-gf16-inv-xor44-depth4.circ.txt) | v8 | nist-batch-16b | 47 s | 46 s | 7.69 | exact |  |
| [skop15-4x4-gf16-inv 43@7](skop15-4x4-gf16-inv/skop15-4x4-gf16-inv-xor43-depth7.circ.txt) | v8 | nist-batch-16b | 8 min | 8 min | 7.69 | exact |  |
| [skop15-4x4-gf16-inv 42@9](skop15-4x4-gf16-inv/skop15-4x4-gf16-inv-xor42-depth9.circ.txt) | v8 | nist-batch-16b | 11 min | 11 min | 7.69 | exact |  |
| [skop15-4x4-gf256 89@4](skop15-4x4-gf256/skop15-4x4-gf256-xor89-depth4.circ.txt) | v8 | nist-batch-32b | 15 min | 14 min | 21.3 | exact |  |
| [skop15-4x4-gf256 88@6](skop15-4x4-gf256/skop15-4x4-gf256-xor88-depth6.circ.txt) | v8 | nist-batch-32b | 4 min | 3 min | 21.3 | exact |  |
| [skop15-4x4-gf256 87@7](skop15-4x4-gf256/skop15-4x4-gf256-xor87-depth7.circ.txt) | v8 | nist-batch-32b | 48 min | 43 min | 21.3 | exact |  |
| [skop15-4x4-gf256-inv 90@4](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor90-depth4.circ.txt) | v8 | nist-batch-32b | 12 min | 10 min | 21.3 | exact |  |
| [skop15-4x4-gf256-inv 88@6](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor88-depth6.circ.txt) | v8 | nist-batch-32b | 33 min | 29 min | 21.3 | exact |  |
| [skop15-4x4-gf256-inv 86@7](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor86-depth7.circ.txt) | v8 | nist-batch-32b | 36 min | 32 min | 21.3 | exact |  |
| [skop15-4x4-gf256-inv 85@9](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor85-depth9.circ.txt) | v8 | nist-batch-32b | 3 min | 3 min | 21.3 | exact |  |
| [skop15-8x8-gf16 361@4](skop15-8x8-gf16/skop15-8x8-gf16-xor361-depth4.circ.txt) | v8 | nist-batch-32b | 7 s | 5 s | 21.3 | exact | built by the `naive` constructor; no search move |
| [skop15-8x8-gf16 203@5](skop15-8x8-gf16/skop15-8x8-gf16-xor203-depth5.circ.txt) | v8 | nist-batch-32b | 40 min | 35 min | 21.3 | exact |  |
| [skop15-8x8-gf16 149@12](skop15-8x8-gf16/skop15-8x8-gf16-xor149-depth12.circ.txt) | v8 | nist-batch-32b | 37 min | 33 min | 21.3 | exact |  |
| [skop15-8x8-gf16 147@13](skop15-8x8-gf16/skop15-8x8-gf16-xor147-depth13.circ.txt) | v8 | nist-batch-32b | 42 min | 38 min | 21.3 | exact |  |
| [skop15-8x8-gf16 146@14](skop15-8x8-gf16/skop15-8x8-gf16-xor146-depth14.circ.txt) | v8 | nist-batch-32b | 41 min | 37 min | 21.3 | exact |  |
| [skop15-8x8-gf16-inv 192@6](skop15-8x8-gf16-inv/skop15-8x8-gf16-inv-xor192-depth6.circ.txt) | v8 | nist-batch-32b | 43 min | 37 min | 21.3 | exact |  |
| [skop15-8x8-gf16-inv 163@10](skop15-8x8-gf16-inv/skop15-8x8-gf16-inv-xor163-depth10.circ.txt) | v8 | nist-batch-32b | 52 min | 47 min | 21.3 | exact |  |
| [skop15-8x8-gf256 712@5](skop15-8x8-gf256/skop15-8x8-gf256-xor712-depth5.circ.txt) | v8 | nist-batch-64 | 26 s | 24 s | 19.5 | exact |  |
| [skop15-8x8-gf256 447@6](skop15-8x8-gf256/skop15-8x8-gf256-xor447-depth6.circ.txt) | v8 | nist-batch-64 | 58 min | 55 min | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 726@5](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor726-depth5.circ.txt) | v8 | nist-batch-64 | 9 s | 8 s | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 408@6](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor408-depth6.circ.txt) | v8 | nist-batch-64 | 49 min | 46 min | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 318@14](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor318-depth14.circ.txt) | v8 | nist-batch-64 | 48 min | 47 min | 19.5 | exact |  |
| [small-scale-aes 44@4](small-scale-aes/small-scale-aes-xor44-depth4.circ.txt) | v8 | nist-batch-16b | 28 s | 27 s | 7.69 | exact |  |
| [small-scale-aes 42@5](small-scale-aes/small-scale-aes-xor42-depth5.circ.txt) | v8 | gaps16 | 15 min | 15 min | 17.2 | exact |  |
| [ss16-4x4-gf16 40@4](ss16-4x4-gf16/ss16-4x4-gf16-xor40-depth4.circ.txt) | v8 | nist-batch-16b | 10 s | 9 s | 7.69 | exact |  |
| [ss16-4x4-gf16-inv 38@4](ss16-4x4-gf16-inv/ss16-4x4-gf16-inv-xor38-depth4.circ.txt) | v8 | nist-batch-16b | 0.5 s | 0.3 s | 7.69 | exact |  |
| [ss16-4x4-gf16-inv 37@5](ss16-4x4-gf16-inv/ss16-4x4-gf16-inv-xor37-depth5.circ.txt) | v8 | nist-batch-16b | 24 s | 24 s | 7.69 | exact |  |
| [ss16-4x4-gf256 98@4](ss16-4x4-gf256/ss16-4x4-gf256-xor98-depth4.circ.txt) | v8 | nist-batch-32b | 14 min | 12 min | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 92@5](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor92-depth5.circ.txt) | v8 | nist-batch-32b | 2 min | 1 min | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 91@8](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor91-depth8.circ.txt) | v8 | nist-batch-32b | 55 s | 51 s | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 90@9](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor90-depth9.circ.txt) | v8 | nist-batch-32b | 3 min | 3 min | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 88@10](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor88-depth10.circ.txt) | v8 | nist-batch-32b | 40 min | 36 min | 21.3 | exact |  |
| [ss17-8x8-gf16 335@4](ss17-8x8-gf16/ss17-8x8-gf16-xor335-depth4.circ.txt) | v8 | nist-batch-32b | 16 s | 12 s | 21.3 | exact |  |
| [ss17-8x8-gf16 194@5](ss17-8x8-gf16/ss17-8x8-gf16-xor194-depth5.circ.txt) | v8 | nist-batch-32b | 40 min | 35 min | 21.3 | exact |  |
| [ss17-8x8-gf256 418@5](ss17-8x8-gf256/ss17-8x8-gf256-xor418-depth5.circ.txt) | v8 | nist-batch-64 | 41 min | 39 min | 19.5 | exact |  |
| [twofish 141@4](twofish/twofish-xor141-depth4.circ.txt) | v8 | nist-twofish | 11 min | 10 min | 20.0 | exact |  |
| [twofish 119@5](twofish/twofish-xor119-depth5.circ.txt) | v8 | nist-twofish | 23 min | 23 min | 20.0 | exact |  |
| [twofish 109@7](twofish/twofish-xor109-depth7.circ.txt) | v8 | nist-twofish | 27 s | 26 s | 20.0 | exact |  |
| [twofish 108@8](twofish/twofish-xor108-depth8.circ.txt) | v8 | nist-twofish | 41 s | 40 s | 20.0 | exact |  |
| [twofish 107@10](twofish/twofish-xor107-depth10.circ.txt) | v8 | nist-twofish | 19 min | 19 min | 20.0 | exact |  |
| [twofish 106@11](twofish/twofish-xor106-depth11.circ.txt) | v8 | nist-twofish | 51 min | 50 min | 20.0 | exact |  |
| [whirlpool-maelstrom 759@5](whirlpool-maelstrom/whirlpool-maelstrom-xor759-depth5.circ.txt) | v8 | wide64 | 17 s | < 1 min | 28.2 | exact | built by the `naive` constructor; no search move |
| [whirlpool-maelstrom 416@6](whirlpool-maelstrom/whirlpool-maelstrom-xor416-depth6.circ.txt) | v8 | nist-batch-64 | 48 min | 46 min | 19.5 | exact |  |
| [whirlpool-maelstrom 395@8](whirlpool-maelstrom/whirlpool-maelstrom-xor395-depth8.circ.txt) | v8 | wide64 | 3.8 h | 3.8 h | 28.2 | exact | searched from our 416@6 |
| [whirlwind-m0 187@6](whirlwind-m0/whirlwind-m0-xor187-depth6.circ.txt) | v8 | nist-batch-32b | 55 min | 48 min | 21.3 | exact |  |
| [whirlwind-m0 170@14](whirlwind-m0/whirlwind-m0-xor170-depth14.circ.txt) | v8 | nist-batch-32b | 3 min | 2 min | 21.3 | exact |  |
| [whirlwind-m0 165@15](whirlwind-m0/whirlwind-m0-xor165-depth15.circ.txt) | v8 | nist-batch-32b | 31 min | 28 min | 21.3 | exact |  |
| [whirlwind-m0 164@16](whirlwind-m0/whirlwind-m0-xor164-depth16.circ.txt) | v8 | nist-batch-32b | 40 min | 36 min | 21.3 | exact |  |
| [whirlwind-m0 163@19](whirlwind-m0/whirlwind-m0-xor163-depth19.circ.txt) | v8 | nist-batch-32b | 51 min | 46 min | 21.3 | exact |  |
| [whirlwind-m1 200@6](whirlwind-m1/whirlwind-m1-xor200-depth6.circ.txt) | v8 | nist-batch-32b | 35 min | 31 min | 21.3 | exact |  |
| [whirlwind-m1 185@13](whirlwind-m1/whirlwind-m1-xor185-depth13.circ.txt) | v8 | nist-batch-32b | 28 s | 24 s | 21.3 | exact |  |
| [whirlwind-m1 175@14](whirlwind-m1/whirlwind-m1-xor175-depth14.circ.txt) | v8 | nist-batch-32b | 6 min | 6 min | 21.3 | exact |  |
| [whirlwind-m1 172@15](whirlwind-m1/whirlwind-m1-xor172-depth15.circ.txt) | v8 | nist-batch-32b | 19 min | 17 min | 21.3 | exact |  |
| [whirlwind-m1 171@18](whirlwind-m1/whirlwind-m1-xor171-depth18.circ.txt) | v8 | nist-batch-32b | 39 min | 35 min | 21.3 | exact |  |
| [whirlwind-m1 170@19](whirlwind-m1/whirlwind-m1-xor170-depth19.circ.txt) | v8 | nist-batch-32b | 55 min | 49 min | 21.3 | exact |  |

## AES S-box circuits

The 73 circuits in [aes-sbox/](aes-sbox/), found by BoolFlux from 2026-11-13 to 2026-11-17 on
the laptop above. Most were found by a short job (a few seconds to half an hour, one process)
that started from an earlier circuit, ours or NIST's, so a job's time is not the time from
scratch: each circuit grew through a chain of such jobs, and the chain is not timed as a whole.
Read from each `logs/<name>/found.json`:

- **Found after**: time from the start of the job (or of the run, where the job ran inside a
  longer run) to the circuit. For a hub job it is the time of the kernel's last improvement in
  that job, where the job logged it, otherwise the whole job. "not logged": the run did not
  record it.
- **Job**: the job's time budget (or the run's, marked "run"); for hub jobs, the measured wall
  and CPU time of the whole job.
- **Found (UTC)**: when the run recorded the circuit; ¹ where the time is the file time of the
  run's copy of the circuit.
- How many other jobs shared the 20 hardware threads at the time was not recorded per job.

| Circuit (A/AD/G/GD) | Method | Found (UTC) | Found after | Measured from | Job | Note |
|---|---|---|---:|---|---|---|
| [aes-sbox 28/4/174/14](aes-sbox/aes-sbox-a28-ad4-g174-gd14-xx146-80.circ.txt) | staged pull | 2026-11-16 10:13 | 6 min | job start | job 15 min | from our 28/4/175/14 |
| [aes-sbox 28/4/138/17](aes-sbox/aes-sbox-a28-ad4-g138-gd17-xx110-61.circ.txt) | gate kernel | 2026-11-14 16:02 ¹ | 32 min | run start | job 2 min | from our 28/4/139/17; 67 s into its job |
| [aes-sbox 28/4/135/18](aes-sbox/aes-sbox-a28-ad4-g135-gd18-xx107-55.circ.txt) | gate kernel | 2026-11-14 16:35 ¹ | 1.1 h | run start | job 2 min | from our 28/4/136/18; < 1 s into its job |
| [aes-sbox 28/4/133/19](aes-sbox/aes-sbox-a28-ad4-g133-gd19-xx105-55.circ.txt) | gate kernel | 2026-11-15 05:14 ¹ | not logged | — | — | from our 28/4/134/19 |
| [aes-sbox 28/4/132/20](aes-sbox/aes-sbox-a28-ad4-g132-gd20-xx104-56.circ.txt) | gate kernel | 2026-11-15 02:26 | not logged | — | — | start not kept |
| [aes-sbox 28/4/131/22](aes-sbox/aes-sbox-a28-ad4-g131-gd22-xx103-52.circ.txt) | gate kernel | 2026-11-15 02:57 ¹ | not logged | — | — | from our 28/4/132/24 |
| [aes-sbox 28/4/130/24](aes-sbox/aes-sbox-a28-ad4-g130-gd24-xx102-45.circ.txt) | gate kernel | 2026-11-15 15:18 | not logged | — | — | start not kept |
| [aes-sbox 28/5/136/17](aes-sbox/aes-sbox-a28-ad5-g136-gd17-xx108-60.circ.txt) | depth pull | 2026-11-15 06:03 ¹ | not logged | — | — | start not kept |
| [aes-sbox 28/5/133/18](aes-sbox/aes-sbox-a28-ad5-g133-gd18-xx105-51.circ.txt) | depth pull (hub) | 2026-11-15 00:06 | 48 s | kernel start in the hub job | wall 100 s, CPU 99 s | from our 28/5/130/19 |
| [aes-sbox 28/5/129/19](aes-sbox/aes-sbox-a28-ad5-g129-gd19-xx101-56.circ.txt) | SAT LNS | 2026-11-15 17:28 | not logged | — | job 15 min | from our 28/5/130/19; time not logged per step by this version (run total 900 s; step 337 of 480) |
| [aes-sbox 28/5/127/22](aes-sbox/aes-sbox-a28-ad5-g127-gd22-xx99-48.circ.txt) | skeleton kick (hub) | 2026-11-14 22:05 | 53 s | hub job start (whole job) | wall 53 s, CPU 55 s | from our 28/5/130/19 |
| [aes-sbox 28/5/126/23](aes-sbox/aes-sbox-a28-ad5-g126-gd23-xx98-58.circ.txt) | staged pull | 2026-11-16 03:51 | 17 min | job start | job 28 min | from NIST 28/5/124/27 |
| [aes-sbox 28/5/125/24](aes-sbox/aes-sbox-a28-ad5-g125-gd24-xx97-50.circ.txt) | staged pull | 2026-11-16 04:07 | 6 min | job start | job 28 min | from our 28/5/125/25 |
| [aes-sbox 29/4/141/15](aes-sbox/aes-sbox-a29-ad4-g141-gd15-xx112-58.circ.txt) | gate kernel (hub) | 2026-11-15 07:07 | 16 s | kernel start in the hub job | wall 95 s, CPU 94 s | from our 29/4/145/15 |
| [aes-sbox 29/4/135/16](aes-sbox/aes-sbox-a29-ad4-g135-gd16-xx106-51.circ.txt) | gate kernel (hub) | 2026-11-15 13:10 | 73 s | kernel start in the hub job | wall 95 s, CPU 94 s | from our 29/4/136/16 |
| [aes-sbox 29/4/131/17](aes-sbox/aes-sbox-a29-ad4-g131-gd17-xx102-64.circ.txt) | depth pull (hub) | 2026-11-15 13:31 | 46 s | kernel start in the hub job | wall 93 s, CPU 94 s | from our 29/4/129/19 |
| [aes-sbox 29/4/129/19](aes-sbox/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt) | depth pull (hub) | 2026-11-15 08:15 | 73 s | kernel start in the hub job | wall 98 s, CPU 97 s | from our 29/4/129/20 |
| [aes-sbox 29/4/128/22](aes-sbox/aes-sbox-a29-ad4-g128-gd22-xx99-44.circ.txt) | gate kernel | 2026-11-17 04:16 ¹ | 12 s | job start (CPU) | job 60 CPU-s | from our 29/4/128/23 (replaced) |
| [aes-sbox 29/4/127/23](aes-sbox/aes-sbox-a29-ad4-g127-gd23-xx98-52.circ.txt) | gate kernel | 2026-11-17 03:49 ¹ | 5 s | job start (CPU) | job 60 CPU-s | from our 29/4/128/23 (replaced) |
| [aes-sbox 29/5/130/18](aes-sbox/aes-sbox-a29-ad5-g130-gd18-xx101-53.circ.txt) | gate kernel (hub) | 2026-11-15 07:01 | 68 s | kernel start in the hub job | wall 98 s, CPU 94 s | from our 29/5/132/18 |
| [aes-sbox 30/4/138/15](aes-sbox/aes-sbox-a30-ad4-g138-gd15-xx108-64.circ.txt) | depth pull (hub) | 2026-11-15 07:12 | 5 s | kernel start in the hub job | wall 98 s, CPU 92 s | from our 30/4/139/15 |
| [aes-sbox 31/5/123/17](aes-sbox/aes-sbox-a31-ad5-g123-gd17-xx92-41.circ.txt) | staged pull | 2026-11-17 09:00 | 7 min | job start | — | from our 31/5/119/18 |
| [aes-sbox 31/5/119/18](aes-sbox/aes-sbox-a31-ad5-g119-gd18-xx88-41.circ.txt) | depth pull (hub) | 2026-11-17 07:15 | not logged | — | wall 90 s, CPU 87 s | from our 31/5/115/20 |
| [aes-sbox 31/5/116/19](aes-sbox/aes-sbox-a31-ad5-g116-gd19-xx85-29.circ.txt) | depth pull (hub) | 2026-11-17 07:12 | not logged | — | wall 90 s, CPU 88 s | from our 31/5/114/21 |
| [aes-sbox 31/5/115/20](aes-sbox/aes-sbox-a31-ad5-g115-gd20-xx84-32.circ.txt) | depth pull (hub) | 2026-11-17 07:12 | not logged | — | wall 90 s, CPU 88 s | from our 31/5/114/21 |
| [aes-sbox 31/5/114/21](aes-sbox/aes-sbox-a31-ad5-g114-gd21-xxn83-32-1.circ.txt) | join (hub) | 2026-11-17 07:05 | not logged | — | wall 8 s, CPU 8 s | join: front of our 32/4/114/19, back of our 31/5/112/24 |
| [aes-sbox 31/5/113/22](aes-sbox/aes-sbox-a31-ad5-g113-gd22-xx82-46.circ.txt) | depth pull (hub) | 2026-11-17 07:06 | not logged | — | wall 90 s, CPU 90 s | from our 31/5/112/24 |
| [aes-sbox 31/5/112/23](aes-sbox/aes-sbox-a31-ad5-g112-gd23-xx81-31.circ.txt) | depth pull (hub) | 2026-11-17 07:06 | not logged | — | wall 90 s, CPU 90 s | from our 31/5/112/24 |
| [aes-sbox 31/5/111/24](aes-sbox/aes-sbox-a31-ad5-g111-gd24-xx80-34.circ.txt) | AND removal | 2026-11-17 09:25 | 5 min | job start | — | from our 32/4/111/25 |
| [aes-sbox 32/4/125/15](aes-sbox/aes-sbox-a32-ad4-g125-gd15-xx93-37.circ.txt) | gate kernel | 2026-11-14 16:09 ¹ | 1.0 h | run start | job 2 min | from our 32/4/126/15 |
| [aes-sbox 32/4/119/16](aes-sbox/aes-sbox-a32-ad4-g119-gd16-xx87-37.circ.txt) | staged pull | 2026-11-16 08:12 | 6 min | job start | job 21 min | from our 32/4/117/17 |
| [aes-sbox 32/4/117/17](aes-sbox/aes-sbox-a32-ad4-g117-gd17-xx85-35.circ.txt) | staged pull | 2026-11-16 07:57 | 11 min | job start | job 21 min | from our 32/4/114/19 |
| [aes-sbox 32/4/115/18](aes-sbox/aes-sbox-a32-ad4-g115-gd18-xx83-35.circ.txt) | staged pull | 2026-11-16 07:48 | 2 min | job start | job 21 min | from our 32/4/114/19 |
| [aes-sbox 32/4/114/19](aes-sbox/aes-sbox-a32-ad4-g114-gd19-xx82-45.circ.txt) | conjugation | 2026-11-16 07:58 | 13 min | job start | job 17 min | from our 32/4/119/18 |
| [aes-sbox 32/4/113/20](aes-sbox/aes-sbox-a32-ad4-g113-gd20-xx81-36.circ.txt) | staged pull | 2026-11-16 08:22 | 4 min | job start | job 17 min | from our 32/4/112/22 |
| [aes-sbox 32/4/112/21](aes-sbox/aes-sbox-a32-ad4-g112-gd21-xx80-33.circ.txt) | SAT LNS | 2026-11-16 07:57 | 12 min | job start | job 20 min | from our 32/4/113/20 |
| [aes-sbox 32/4/111/25](aes-sbox/aes-sbox-a32-ad4-g111-gd25-xx79-30.circ.txt) | conjugation | 2026-11-16 02:10 | 6 min | job start | job 25 min | from NIST 32/4/117/19 |
| [aes-sbox 32/5/112/17](aes-sbox/aes-sbox-a32-ad5-g112-gd17-xx80-36.circ.txt) | staged pull | 2026-11-17 10:13 | 7 min | job start | — | from our 32/5/110/18 |
| [aes-sbox 32/5/110/18](aes-sbox/aes-sbox-a32-ad5-g110-gd18-xx78-33.circ.txt) | join (hub) | 2026-11-17 07:37 | not logged | — | wall 6 s, CPU 5 s | join: front of our 33/5/113/17, back of our 32/5/108/19 |
| [aes-sbox 32/5/108/19](aes-sbox/aes-sbox-a32-ad5-g108-gd19-xx76-28.circ.txt) | re-basing | 2026-11-17 03:37 | 81 s | job start | job 6 min | from our 32/5/108/20 (replaced) |
| [aes-sbox 32/5/106/21](aes-sbox/aes-sbox-a32-ad5-g106-gd21-xx74-28.circ.txt) | staged pull | 2026-11-16 02:36 | 100 s | job start | job 18 min | from our 32/5/106/22 |
| [aes-sbox 32/5/105/24](aes-sbox/aes-sbox-a32-ad5-g105-gd24-xx73-24.circ.txt) | conjugation | 2026-11-16 02:11 | 7 min | job start | job 18 min | from our 32/5/104/29 |
| [aes-sbox 32/5/104/28](aes-sbox/aes-sbox-a32-ad5-g104-gd28-xx72-37.circ.txt) | staged pull | 2026-11-17 11:01 | 80 s | job start | — | from our 32/5/106/28 |
| [aes-sbox 32/7/104/26](aes-sbox/aes-sbox-a32-ad7-g104-gd26-xx72-31.circ.txt) | staged pull | 2026-11-16 02:10 | 6 min | job start | job 17 min | from our 32/7/104/27 |
| [aes-sbox 32/7/103/29](aes-sbox/aes-sbox-a32-ad7-g103-gd29-xx71-25.circ.txt) | conjugation | 2026-11-16 03:03 | 10 min | job start | job 17 min | from NIST 32/7/103/32 |
| [aes-sbox 33/4/123/14](aes-sbox/aes-sbox-a33-ad4-g123-gd14-xx90-36.circ.txt) | gate kernel (hub) | 2026-11-17 07:42 | not logged | — | wall 90 s, CPU 89 s | from our 33/4/124/14 |
| [aes-sbox 33/4/115/15](aes-sbox/aes-sbox-a33-ad4-g115-gd15-xx82-19.circ.txt) | join | 2026-11-14 15:48 ¹ | 19 min | run start | — | join: front of NIST 32/4/127/15, back of our 37/4/121/14 |
| [aes-sbox 33/4/112/16](aes-sbox/aes-sbox-a33-ad4-g112-gd16-xx79-28.circ.txt) | gate kernel (hub) | 2026-11-14 18:30 | 17 s | kernel start in the hub job | wall 101 s, CPU 100 s | from our 33/4/113/16 |
| [aes-sbox 33/4/109/17](aes-sbox/aes-sbox-a33-ad4-g109-gd17-xx76-30.circ.txt) | gate kernel (hub) | 2026-11-17 07:42 | not logged | — | wall 90 s, CPU 89 s | from our 33/4/110/17 |
| [aes-sbox 33/4/108/18](aes-sbox/aes-sbox-a33-ad4-g108-gd18-xx75-30.circ.txt) | staged pull | 2026-11-17 09:09 | 84 s | job start | — | from our 33/4/109/17 |
| [aes-sbox 33/4/107/20](aes-sbox/aes-sbox-a33-ad4-g107-gd20-xx74-26.circ.txt) | depth pull (hub) | 2026-11-14 18:14 | 79 s | kernel start in the hub job | wall 101 s, CPU 100 s | from NIST 33/4/106/22 |
| [aes-sbox 34/4/134/13](aes-sbox/aes-sbox-a34-ad4-g134-gd13-xx100-51.circ.txt) | gate kernel (hub) | 2026-11-14 19:42 | 45 s | kernel start in the hub job | wall 101 s, CPU 100 s | from NIST 35/4/133/13 |
| [aes-sbox 34/4/122/14](aes-sbox/aes-sbox-a34-ad4-g122-gd14-xx88-38.circ.txt) | staged pull | 2026-11-16 12:16 | 39 s | job start | job 15 min | from our 34/4/123/14 |
| [aes-sbox 35/3/181/12](aes-sbox/aes-sbox-a35-ad3-g181-gd12-xx146-80.circ.txt) | re-basing | 2026-11-16 01:10 | 8 min | job start | job 20 min | from our 35/3/177/13 |
| [aes-sbox 35/3/165/13](aes-sbox/aes-sbox-a35-ad3-g165-gd13-xx130-60.circ.txt) | re-basing | 2026-11-16 09:10 | 3 min | job start | job 15 min | from our 35/3/166/13 |
| [aes-sbox 35/3/160/14](aes-sbox/aes-sbox-a35-ad3-g160-gd14-xx125-64.circ.txt) | re-basing | 2026-11-17 03:48 | 81 s | job start | job 6 min | from our 35/3/155/15 |
| [aes-sbox 35/3/153/15](aes-sbox/aes-sbox-a35-ad3-g153-gd15-xx118-55.circ.txt) | gate kernel (hub) | 2026-11-17 09:33 | not logged | — | wall 90 s, CPU 90 s | from our 35/3/154/15 |
| [aes-sbox 35/3/145/16](aes-sbox/aes-sbox-a35-ad3-g145-gd16-xx110-50.circ.txt) | gate kernel (hub) | 2026-11-17 08:02 | not logged | — | wall 90 s, CPU 90 s | from our 35/3/147/16 |
| [aes-sbox 35/3/143/17](aes-sbox/aes-sbox-a35-ad3-g143-gd17-xx108-51.circ.txt) | staged pull | 2026-11-17 10:42 | 92 s | job start | — | from our 35/3/153/15 |
| [aes-sbox 35/3/141/19](aes-sbox/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt) | product exchange | 2026-11-15 11:40 ¹ | not logged | — | — | from our 35/3/142/19 |
| [aes-sbox 35/3/139/21](aes-sbox/aes-sbox-a35-ad3-g139-gd21-xx104-50.circ.txt) | staged pull | 2026-11-16 12:09 | 4 min | job start | job 5 min | from our 35/3/139/22 |
| [aes-sbox 35/3/138/23](aes-sbox/aes-sbox-a35-ad3-g138-gd23-xx103-46.circ.txt) | staged pull | 2026-11-16 07:05 | 4 min | job start | job 5 min | from our 35/3/138/24 |
| [aes-sbox 35/3/137/27](aes-sbox/aes-sbox-a35-ad3-g137-gd27-xx102-40.circ.txt) | gate kernel | 2026-11-17 03:20 ¹ | 5 s | job start (CPU) | job 20 CPU-s | from our 35/3/137/28 (replaced) |
| [aes-sbox 36/4/128/13](aes-sbox/aes-sbox-a36-ad4-g128-gd13-xx92-47.circ.txt) | depth pull | 2026-11-17 03:44 | 100 s | job start | job 90 CPU-s | from our 36/4/128/14, an AND removal of our 37/4/127/13 |
| [aes-sbox 37/4/127/13](aes-sbox/aes-sbox-a37-ad4-g127-gd13-xx90-41.circ.txt) | staged pull | 2026-11-16 09:34 | 5 min | job start | job 8 min | from our 36/4/129/13 |
| [aes-sbox 37/4/121/14](aes-sbox/aes-sbox-a37-ad4-g121-gd14-xx84-36.circ.txt) | gate kernel | 2026-11-14 14:56 ¹ | 4 min | job start | run 16 min | from our 38/4/124/14 |
| [aes-sbox 38/4/135/12](aes-sbox/aes-sbox-a38-ad4-g135-gd12-xx97-25.circ.txt) | shared-bottom rebuild | 2026-11-16 09:46 | 9 min | job start | job 15 min | from our 39/4/138/12 |
| [aes-sbox 42/4/284/11](aes-sbox/aes-sbox-a42-ad4-g284-gd11-xx242-114.circ.txt) | gate kernel | 2026-11-15 06:35 ¹ | not logged | — | — | from our 42/4/301/11 |
| [aes-sbox 43/4/278/11](aes-sbox/aes-sbox-a43-ad4-g278-gd11-xx235-123.circ.txt) | gate kernel | 2026-11-15 03:29 ¹ | not logged | — | — | start not kept |
| [aes-sbox 44/4/254/11](aes-sbox/aes-sbox-a44-ad4-g254-gd11-xx210-122.circ.txt) | gate kernel | 2026-11-15 03:12 ¹ | not logged | — | — | start not kept |
| [aes-sbox 46/4/200/11](aes-sbox/aes-sbox-a46-ad4-g200-gd11-xx154-73.circ.txt) | gate kernel (hub) | 2026-11-15 07:32 | 79 s | kernel start in the hub job | wall 97 s, CPU 97 s | from our 46/4/203/11 |
| [aes-sbox 47/4/186/11](aes-sbox/aes-sbox-a47-ad4-g186-gd11-xx139-70.circ.txt) | gate kernel | 2026-11-15 02:50 ¹ | not logged | — | job 30 min | start not kept |
| [aes-sbox 48/4/151/11](aes-sbox/aes-sbox-a48-ad4-g151-gd11-xx103-47.circ.txt) | gate kernel | 2026-11-14 18:04 ¹ | 3 s | job start | job 2 min | from our 48/4/162/11 |

## Notes

- **Constructors.** A circuit marked "built by the … constructor" is a chain's starting
  circuit, kept because it already beat everything else at its point. `naive` builds
  balanced XOR trees; `anneal3` is the depth-3 partition annealer (`moves/depth3.py`), a
  constructor made for depth 3. For these, "found after" is the time at which the
  constructor ran, and its own run time is seconds.
- **Polish.** "+ polish" circuits are older circuits shrunk by v8's exact own-depth polish
  in well under a second; the times are those of the original circuit.
- **aes-mixcolumns 89@4** was found by the control side of an A/B test of proposed v9
  changes. That side ran a copy of v8 holding the proposed code with every change switched
  off, so its search is v8's; the frozen source is part of the run. It replaced the v1 89@4
  (run long20, after about 14.5 h, with no record of the move that found it). Both grew
  from the July 91@4. The run had three sessions (7.7, 19.6 and 18.2 h of wall time).
- **aes-invmixcolumns 118@5** was found by the adopt side of the same A/B test as the
  MixColumns 89@4, 42.3 h of wall time into the run (three sessions; 44.7 h on the run's
  fast clock). The run had the same three sessions as the control side. It replaced our v4
  168@5 (run invmixcolumns-13).
