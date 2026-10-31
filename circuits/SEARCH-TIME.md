# Search time and hardware

How long the search ran before each circuit in this folder was found, on what machine, and
how much compute each run used. Numbers marked EXACT are read from the run logs; the others
are estimates, and the table says how each was made. The search's whole development since
June 2026, including runs that found nothing, is in
[search/HISTORY.md](../search/HISTORY.md).

## Hardware

Every run that produced a circuit here ran on one laptop:

| | |
|---|---|
| CPU | Intel Core i7-13700H: 14 cores (6 performance cores with 2 threads each, 8 efficiency cores), 20 hardware threads |
| Memory | 64 GB (31 GB visible to WSL2); not recorded by the runs |
| OS | Windows 11 with WSL2, Ubuntu 24.04 (kernel 6.6.114.1-microsoft-standard-WSL2) |
| Python | 3.10.18 for v1–v4, 3.12.3 for v5–v8; every worker is one single-threaded process |
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
| long20 | v1 | 2026-10-21 01:23 | ~39.8 h | 20 | ~796.3 | — | last 5.5 h on 10 threads | 1 |
| three-targets20 | v2 | 2026-10-24 16:25 | 69.9 h | 20 | 1,398.7 | — | no | 1 |
| joltik-depth-foxmu8-15 | v3 | 2026-10-27 15:03 | 22.2 h | 15 | 332.4 | — | no | 2 |
| invmixcolumns-13 | v4 | 2026-10-28 13:28 | 1.4 h | 13 | 18.5 | — | no | 1 |
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

Together: 24 runs, about 3,010 worker-hours, for 201 circuits. v1–v4 used about 2,550 of those worker-hours for 5 circuits; v6–v8 used about 465 for 196. Another 21 logged runs of 2026-10-28 to 10-30 (310 worker-hours) produced no circuit kept here; they are not in the
totals. Compute before v1 is in [search/HISTORY.md](../search/HISTORY.md#compute).

## Circuits

| Circuit | Version | Run | Found after | Finder CPU | Run worker-h | Status | Note |
|---|---|---|---:|---:|---:|---|---|
| [aes-invmixcolumns 168@5](aes-invmixcolumns/aes-invmixcolumns-xor168-depth5.circ.txt) | v4 | invmixcolumns-13 | unknown (≤ 1.4 h) | ? | ~18.5 | upper bound | + polish of 170@5; from a checkpoint |
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
| [aes-mixcolumns 89@4](aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt) | v1 | long20 | ~14.5 h (13.9 h–16.1 h) | ~14.5 h | ~796.3 | estimate |  |
| [aes-mixcolumns 88@5](aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt) | v7 | bench-mixcolumns | 35 min | 33 min | 18.4 | exact |  |
| [aes-sbox-bottom 29@4](aes-sbox-bottom/aes-sbox-bottom-xor29-depth4.circ.txt) | v6 | rerun-aes_sbox_bottom | 4 s | 4 s | 18.9 | exact |  |
| [aes-sbox-bottom 28@5](aes-sbox-bottom/aes-sbox-bottom-xor28-depth5.circ.txt) | v6 | rerun-aes_sbox_bottom | 29 min | 28 min | 18.9 | exact |  |
| [anubis-clefia-m0 95@5](anubis-clefia-m0/anubis-clefia-m0-xor95-depth5.circ.txt) | v8 | nist-batch-32a | 25 min | 22 min | 21.4 | exact |  |
| [anubis-clefia-m0 94@6](anubis-clefia-m0/anubis-clefia-m0-xor94-depth6.circ.txt) | v8 | nist-batch-32a | 32 min | 29 min | 21.4 | exact |  |
| [anubis-clefia-m0 93@7](anubis-clefia-m0/anubis-clefia-m0-xor93-depth7.circ.txt) | v8 | nist-batch-32a | 32 min | 29 min | 21.4 | exact |  |
| [anubis-clefia-m0 92@8](anubis-clefia-m0/anubis-clefia-m0-xor92-depth8.circ.txt) | v8 | nist-batch-32a | 41 min | 37 min | 21.4 | exact |  |
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
| [bkl16-8x8-gf256 443@9](bkl16-8x8-gf256/bkl16-8x8-gf256-xor443-depth9.circ.txt) | v8 | nist-batch-64 | 56 min | 55 min | 19.5 | exact |  |
| [bkl16-8x8-gf256 442@10](bkl16-8x8-gf256/bkl16-8x8-gf256-xor442-depth10.circ.txt) | v8 | nist-batch-64 | 57 min | 56 min | 19.5 | exact |  |
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
| [fox-mu8 506@10](fox-mu8/fox-mu8-xor506-depth10.circ.txt) | v6 | rerun-fox_mu8 | 54 min | 53 min | 18.8 | exact |  |
| [fox-mu8 505@11](fox-mu8/fox-mu8-xor505-depth11.circ.txt) | v6 | rerun-fox_mu8 | 44 min | 43 min | 18.8 | exact |  |
| [grostl 502@5](grostl/grostl-xor502-depth5.circ.txt) | v8 | nist-grostl | 58 min | 56 min | 19.8 | exact |  |
| [grostl 455@8](grostl/grostl-xor455-depth8.circ.txt) | v8 | nist-grostl | 4 min | 4 min | 19.8 | exact |  |
| [grostl 405@10](grostl/grostl-xor405-depth10.circ.txt) | v8 | nist-grostl | 38 s | 36 s | 19.8 | exact |  |
| [grostl 368@11](grostl/grostl-xor368-depth11.circ.txt) | v8 | nist-grostl | 46 min | 45 min | 19.8 | exact |  |
| [grostl 366@12](grostl/grostl-xor366-depth12.circ.txt) | v8 | nist-grostl | 47 min | 45 min | 19.8 | exact |  |
| [grostl 362@13](grostl/grostl-xor362-depth13.circ.txt) | v8 | nist-grostl | 59 min | 57 min | 19.8 | exact |  |
| [grostl 360@14](grostl/grostl-xor360-depth14.circ.txt) | v8 | nist-grostl | 59 min | 57 min | 19.8 | exact |  |
| [grostl 358@15](grostl/grostl-xor358-depth15.circ.txt) | v8 | nist-grostl | 47 min | 46 min | 19.8 | exact |  |
| [grostl 350@16](grostl/grostl-xor350-depth16.circ.txt) | v8 | nist-grostl | 51 min | 50 min | 19.8 | exact |  |
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
| [jpst17-8x8-gf256-inv 496@10](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor496-depth10.circ.txt) | v8 | nist-batch-64 | 50 min | 49 min | 19.5 | exact |  |
| [jpst17-8x8-gf256-inv 493@11](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor493-depth11.circ.txt) | v8 | nist-batch-64 | 54 min | 52 min | 19.5 | exact |  |
| [jpst17-8x8-gf256-inv 492@12](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor492-depth12.circ.txt) | v8 | nist-batch-64 | 58 min | 56 min | 19.5 | exact |  |
| [khazad 1055@5](khazad/khazad-xor1055-depth5.circ.txt) | v8 | wide64 | 22 min | 22 min | 28.2 | exact | built by the `naive` constructor; no search move |
| [khazad 478@6](khazad/khazad-xor478-depth6.circ.txt) | v8 | nist-batch-64 | 54 min | 52 min | 19.5 | exact |  |
| [khazad 477@8](khazad/khazad-xor477-depth8.circ.txt) | v8 | wide64 | 30 s | < 1 min | 28.2 | exact | searched from our 478@6 |
| [khazad 460@9](khazad/khazad-xor460-depth9.circ.txt) | v8 | wide64 | 15 min | 14 min | 28.2 | exact |  |
| [khazad 433@10](khazad/khazad-xor433-depth10.circ.txt) | v8 | wide64 | 4.2 h | 4.2 h | 28.2 | exact |  |
| [khazad 432@11](khazad/khazad-xor432-depth11.circ.txt) | v8 | wide64 | 4.5 h | 4.4 h | 28.2 | exact |  |
| [khazad 345@15](khazad/khazad-xor345-depth15.circ.txt) | v8 | nist-batch-64 | 30 min | 29 min | 19.5 | exact |  |
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
| [klsw17-m-8x8-gf16-0x13-inv 176@11](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor176-depth11.circ.txt) | v8 | nist-batch-32a | 2 s | 2 s | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13-inv 163@12](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor163-depth12.circ.txt) | v8 | nist-batch-32a | 58 min | 52 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf16-0x13-inv 162@13](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor162-depth13.circ.txt) | v8 | nist-batch-32a | 54 min | 49 min | 21.4 | exact |  |
| [klsw17-m-8x8-gf256 347@6](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor347-depth6.circ.txt) | v8 | nist-batch-64 | 56 min | 54 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256 336@12](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor336-depth12.circ.txt) | v8 | nist-batch-64 | 12 min | 11 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256 329@13](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor329-depth13.circ.txt) | v8 | nist-batch-64 | 23 min | 23 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256 327@14](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor327-depth14.circ.txt) | v8 | nist-batch-64 | 47 min | 46 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256 326@15](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor326-depth15.circ.txt) | v8 | nist-batch-64 | 56 min | 55 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 490@6](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor490-depth6.circ.txt) | v8 | nist-batch-64 | 52 min | 50 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 361@11](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor361-depth11.circ.txt) | v8 | nist-batch-64 | 2 min | 1 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 346@12](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor346-depth12.circ.txt) | v8 | nist-batch-64 | 7 min | 6 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 345@13](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor345-depth13.circ.txt) | v8 | nist-batch-64 | 6 min | 6 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 331@14](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor331-depth14.circ.txt) | v8 | nist-batch-64 | 28 min | 27 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 329@15](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor329-depth15.circ.txt) | v8 | nist-batch-64 | 32 min | 31 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 325@16](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor325-depth16.circ.txt) | v8 | nist-batch-64 | 56 min | 55 min | 19.5 | exact |  |
| [klsw17-m-8x8-gf256-inv 324@21](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor324-depth21.circ.txt) | v8 | nist-batch-64 | 55 min | 54 min | 19.5 | exact |  |
| [ls16-4x4-gf16 43@3](ls16-4x4-gf16/ls16-4x4-gf16-xor43-depth3.circ.txt) | v8 | nist-batch-16a | 4 s | 3 s | 8.67 | exact |  |
| [ls16-4x4-gf256 103@4](ls16-4x4-gf256/ls16-4x4-gf256-xor103-depth4.circ.txt) | v8 | nist-batch-32a | 16 min | 14 min | 21.4 | exact |  |
| [ls16-8x8-gf256 411@5](ls16-8x8-gf256/ls16-8x8-gf256-xor411-depth5.circ.txt) | v8 | nist-batch-64 | 46 min | 45 min | 19.5 | exact |  |
| [ls16-8x8-gf256 404@8](ls16-8x8-gf256/ls16-8x8-gf256-xor404-depth8.circ.txt) | v8 | nist-batch-64 | 30 min | 29 min | 19.5 | exact |  |
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
| [skop15-8x8-gf256 418@8](skop15-8x8-gf256/skop15-8x8-gf256-xor418-depth8.circ.txt) | v8 | nist-batch-64 | 49 min | 48 min | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 726@5](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor726-depth5.circ.txt) | v8 | nist-batch-64 | 9 s | 8 s | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 408@6](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor408-depth6.circ.txt) | v8 | nist-batch-64 | 49 min | 46 min | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 333@12](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor333-depth12.circ.txt) | v8 | nist-batch-64 | 3 min | 3 min | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 331@13](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor331-depth13.circ.txt) | v8 | nist-batch-64 | 5 min | 5 min | 19.5 | exact |  |
| [skop15-8x8-gf256-inv 318@14](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor318-depth14.circ.txt) | v8 | nist-batch-64 | 48 min | 47 min | 19.5 | exact |  |
| [small-scale-aes 44@4](small-scale-aes/small-scale-aes-xor44-depth4.circ.txt) | v8 | nist-batch-16b | 28 s | 27 s | 7.69 | exact |  |
| [small-scale-aes 42@5](small-scale-aes/small-scale-aes-xor42-depth5.circ.txt) | v8 | gaps16 | 15 min | 15 min | 17.2 | exact |  |
| [ss16-4x4-gf16 40@4](ss16-4x4-gf16/ss16-4x4-gf16-xor40-depth4.circ.txt) | v8 | nist-batch-16b | 10 s | 9 s | 7.69 | exact |  |
| [ss16-4x4-gf16-inv 38@4](ss16-4x4-gf16-inv/ss16-4x4-gf16-inv-xor38-depth4.circ.txt) | v8 | nist-batch-16b | 0.5 s | 0.3 s | 7.69 | exact |  |
| [ss16-4x4-gf16-inv 37@5](ss16-4x4-gf16-inv/ss16-4x4-gf16-inv-xor37-depth5.circ.txt) | v8 | nist-batch-16b | 24 s | 24 s | 7.69 | exact |  |
| [ss16-4x4-gf256 98@4](ss16-4x4-gf256/ss16-4x4-gf256-xor98-depth4.circ.txt) | v8 | nist-batch-32b | 14 min | 12 min | 21.3 | exact |  |
| [ss16-4x4-gf256 97@6](ss16-4x4-gf256/ss16-4x4-gf256-xor97-depth6.circ.txt) | v8 | nist-batch-32b | 8 min | 7 min | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 92@5](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor92-depth5.circ.txt) | v8 | nist-batch-32b | 2 min | 1 min | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 91@8](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor91-depth8.circ.txt) | v8 | nist-batch-32b | 55 s | 51 s | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 90@9](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor90-depth9.circ.txt) | v8 | nist-batch-32b | 3 min | 3 min | 21.3 | exact |  |
| [ss16-4x4-gf256-inv 88@10](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor88-depth10.circ.txt) | v8 | nist-batch-32b | 40 min | 36 min | 21.3 | exact |  |
| [ss17-8x8-gf16 335@4](ss17-8x8-gf16/ss17-8x8-gf16-xor335-depth4.circ.txt) | v8 | nist-batch-32b | 16 s | 12 s | 21.3 | exact |  |
| [ss17-8x8-gf16 194@5](ss17-8x8-gf16/ss17-8x8-gf16-xor194-depth5.circ.txt) | v8 | nist-batch-32b | 40 min | 35 min | 21.3 | exact |  |
| [ss17-8x8-gf16 175@8](ss17-8x8-gf16/ss17-8x8-gf16-xor175-depth8.circ.txt) | v8 | nist-batch-32b | 4 min | 4 min | 21.3 | exact |  |
| [ss17-8x8-gf16 174@9](ss17-8x8-gf16/ss17-8x8-gf16-xor174-depth9.circ.txt) | v8 | nist-batch-32b | 4 min | 3 min | 21.3 | exact |  |
| [ss17-8x8-gf16 167@10](ss17-8x8-gf16/ss17-8x8-gf16-xor167-depth10.circ.txt) | v8 | nist-batch-32b | 50 min | 45 min | 21.3 | exact |  |
| [ss17-8x8-gf16 166@11](ss17-8x8-gf16/ss17-8x8-gf16-xor166-depth11.circ.txt) | v8 | nist-batch-32b | 22 min | 20 min | 21.3 | exact |  |
| [ss17-8x8-gf16 165@13](ss17-8x8-gf16/ss17-8x8-gf16-xor165-depth13.circ.txt) | v8 | nist-batch-32b | 37 min | 33 min | 21.3 | exact |  |
| [ss17-8x8-gf256 418@5](ss17-8x8-gf256/ss17-8x8-gf256-xor418-depth5.circ.txt) | v8 | nist-batch-64 | 41 min | 39 min | 19.5 | exact |  |
| [ss17-8x8-gf256 392@8](ss17-8x8-gf256/ss17-8x8-gf256-xor392-depth8.circ.txt) | v8 | nist-batch-64 | 29 min | 28 min | 19.5 | exact |  |
| [twofish 141@4](twofish/twofish-xor141-depth4.circ.txt) | v8 | nist-twofish | 11 min | 10 min | 20.0 | exact |  |
| [twofish 119@5](twofish/twofish-xor119-depth5.circ.txt) | v8 | nist-twofish | 23 min | 23 min | 20.0 | exact |  |
| [twofish 109@7](twofish/twofish-xor109-depth7.circ.txt) | v8 | nist-twofish | 27 s | 26 s | 20.0 | exact |  |
| [twofish 108@8](twofish/twofish-xor108-depth8.circ.txt) | v8 | nist-twofish | 41 s | 40 s | 20.0 | exact |  |
| [twofish 107@10](twofish/twofish-xor107-depth10.circ.txt) | v8 | nist-twofish | 19 min | 19 min | 20.0 | exact |  |
| [twofish 106@11](twofish/twofish-xor106-depth11.circ.txt) | v8 | nist-twofish | 51 min | 50 min | 20.0 | exact |  |
| [whirlpool-maelstrom 759@5](whirlpool-maelstrom/whirlpool-maelstrom-xor759-depth5.circ.txt) | v8 | wide64 | 17 s | < 1 min | 28.2 | exact | built by the `naive` constructor; no search move |
| [whirlpool-maelstrom 416@6](whirlpool-maelstrom/whirlpool-maelstrom-xor416-depth6.circ.txt) | v8 | nist-batch-64 | 48 min | 46 min | 19.5 | exact |  |
| [whirlpool-maelstrom 395@8](whirlpool-maelstrom/whirlpool-maelstrom-xor395-depth8.circ.txt) | v8 | wide64 | 3.8 h | 3.8 h | 28.2 | exact | searched from our 416@6 |
| [whirlpool-maelstrom 394@9](whirlpool-maelstrom/whirlpool-maelstrom-xor394-depth9.circ.txt) | v8 | wide64 | 3.9 h | 3.9 h | 28.2 | exact |  |
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

## Notes

- **Constructors.** A circuit marked "built by the … constructor" is a chain's starting
  circuit, kept because it already beat everything else at its point. `naive` builds
  balanced XOR trees; `anneal3` is the depth-3 partition annealer (`moves/depth3.py`), a
  constructor made for depth 3. For these, "found after" is the time at which the
  constructor ran, and its own run time is seconds.
- **Polish.** "+ polish" circuits are older circuits shrunk by v8's exact own-depth polish
  in well under a second; the times are those of the original circuit.
- **v1 (aes-mixcolumns 89@4).** The first session's stop time was overwritten when the run
  was resumed. The time is reconstructed from a worker log line and the worker's chunk
  count; the run did not start from scratch (its seeds include a 91@4 found in July 2026).
- **v4 (aes-invmixcolumns 168@5)** was recovered from a worker's final checkpoint, so only
  the run length bounds when it was found.
