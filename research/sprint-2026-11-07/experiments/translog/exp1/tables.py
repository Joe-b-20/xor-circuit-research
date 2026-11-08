#!/usr/bin/env python3
"""Markdown tables from exp1/analysis.json (used by make_report_exp1.py and for a quick look)."""
import json, os

E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp1")
A = json.load(open(os.path.join(E, "analysis.json")))
W = A["workers"]


def f(x, d=2):
    return "n/a" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


def q1_table():
    out = ["| worker | steps/s | entries/h | distinct ids / entries | stay med s | exc med steps / s | exc < 30 s | exc < 2 s | share 88/89/90 | <88 |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for w in W:
        r = A["Q1"][w]
        sh = r["time_share_by_gates"]
        out.append(f"| {w} | {f(r['steps_per_s'],0)} | {f(r['entries_88_per_min']*60,0)} | {r['distinct_88_ids']} / {r['entries_88']} | "
                   f"{f(r['stay_88_seconds']['median'])} | {r['excursion_steps']['median']} / {f(r['excursion_seconds']['median'],3)} | "
                   f"{f(r['excursions_shorter_than_30s']*100,2)} % | {f(r['excursions_shorter_than_2s']*100,1)} % | "
                   f"{f(sh.get('88',0)*100,0)}/{f(sh.get('89',0)*100,0)}/{f(sh.get('90',0)*100,0)} % | {r['below_88']} |")
    return "\n".join(out)


def q2_table():
    out = ["| worker | entries | distinct v3 | v3 visits | visits/h | distinct v3/h | entries per visit (med) | revisits | v3 seen > once | hop exc med s | hops < 30 s |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in W:
        r = A["Q2"]["per_worker"][w]
        out.append(f"| {w} | {r['entries']} | {r['distinct_v3']} | {r['visits']} | {f(r['visits_per_h'],0)} | {f(r['distinct_v3_per_h'],0)} | "
                   f"{r['entries_per_visit_median']} | {r['revisits']} | {r['v3_visited_more_than_once']} | {f(r['hop_excursion_s_median'],3)} | "
                   f"{f((r['hop_excursion_lt30s'] or 0)*100,1)} % |")
    return "\n".join(out)


def q3_table():
    out = ["| pair set | pairs | P (distinct-node products) | expected P / 1.3e5 | Poisson 95 % | M (pair incidences) | M (nodes) | verdict |",
           "|---|---|---|---|---|---|---|---|"]
    for k in ("all_pairs", "cross_pairs", "same_start_pairs"):
        r = A["Q3"][k]
        out.append(f"| {k.replace('_', ' ')} | {r['pairs']} | {r['P_nodes']:,} | {r['expected_P_over_Neff']} | {r['poisson95']} | "
                   f"{r['M_pair_incidences']} | {r['M_nodes']} | {r['verdict']} |")
    return "\n".join(out)


def same_start_table():
    out = ["| pair | distinct v3 (a, b) | entries on start sig (a, b) | first left start (s) | last on start (s) | shared v3 excl. start | null expectation | re-meetings after both left |",
           "|---|---|---|---|---|---|---|---|"]
    for d in A["Q3"]["same_start_detail"]:
        fl = d["first_leave_start_s"]
        lo = d["last_on_start_s"]
        out.append(f"| {d['pair'][0]}/{d['pair'][1]} | {d['nodes'][0]}, {d['nodes'][1]} | {d['entries_on_start_sig'][0]}, {d['entries_on_start_sig'][1]} | "
                   f"{f(fl[0],0)}, {f(fl[1],0)} | {f(lo[0],0)}, {f(lo[1],0)} | {d['shared_excluding_start']} | {d['expected_null']} | {d['re_meetings_after_both_left_start']} |")
    return "\n".join(out)


def q4_table():
    out = ["| worker | sampler records | 88 samples | 89 samples | sampler hops | hops/h | hops with no 89 sample | distinct v3 sampled | distinct v3 in log | log entries | log v3 visits |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in W:
        r = A["Q4"]["per_worker"][w]
        out.append(f"| {w} | {r['records']} | {r['samples_88']} | {r['samples_89']} | {r['hops_sampler']} | {f(r['hops_sampler_per_h'],0)} | "
                   f"{r['hops_without_89_sample']} | {r['distinct_v3_sampled']} | {r['distinct_v3_log']} | {r['entries_log']} | {r['visits_log']} |")
    return "\n".join(out)


if __name__ == "__main__":
    for fn in (q1_table, q2_table, q3_table, same_start_table, q4_table):
        print(fn())
        print()
    print(json.dumps(A["Q2"]["exact_coincidences"], indent=0)[:3000])
    print(json.dumps(A["Q2"]["exact_hops"], indent=0)[:3000])
    print(json.dumps(A["Q1_pooled"], indent=0)[:2000])
    print(json.dumps(A["Q2"]["pooled"]))
    print(json.dumps({k: v for k, v in A["Q4"].items() if k != "per_worker"}))
    print(json.dumps(A["Q3"]["cross_pair_detail"][:8]))
