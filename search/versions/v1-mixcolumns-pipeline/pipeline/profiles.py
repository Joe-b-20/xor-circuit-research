"""Explicit, reproducible worker portfolios. No network or hidden seeds."""
from copy import deepcopy

from ladder_parallel import LNS_KNOBS, WALK_KNOBS, ANNEAL_KNOBS


SEEDS = {
    "own97": ("seeds/mixcolumns_97gates_depth3.json", "own-lineage"),
    "own91": ("seeds/mixcolumns_91gates_depth4.json", "own-lineage"),
    "own88": ("seeds/mixcolumns_88gates_depth5_fromscratch.json", "own-lineage"),
    "own88d7": ("seeds/seed_88_at_depth7_ours.json", "own-lineage"),
    "nist90": ("seeds/mixcolumns_90gates_depth4_nist.json", "imported-nist-public90"),
    "derived88": ("seeds/mixcolumns_88gates_depth5.json", "derived-from-published-work"),
    "jean88": ("seeds/seed_88_at_depth7_jean_imported.json", "imported-jeremy-jean"),
    "third88": ("seeds/seed_88_at_depth8_thirdfamily.json", "derived-from-published-work"),
}


def engine_knobs(lane=0, cap=None):
    knobs = {"lns": deepcopy(LNS_KNOBS), "walk": deepcopy(WALK_KNOBS),
             "anneal3": deepcopy(ANNEAL_KNOBS)}
    common = dict(
        persist_state=True, checkpoint_seconds=10.0,
        harvest=False, cross_pollinate=False,
        pool_limit=6000, hot_limit=1000,
        deadline_rebuild_p=(0.12, 0.25, 0.40)[lane % 3],
        deadline_seconds=(0.012, 0.025, 0.05)[lane % 3],
        beam_width=(4, 6, 8)[lane % 3],
        structured_every=(80, 45, 25)[lane % 3],
        structured_seconds=0.15,
        core_every=(160, 100, 60)[lane % 3],
        joint_every=40, joint_seconds=0.06,
        expansion_p=(0.04, 0.08, 0.12)[lane % 3],
        expansion_seconds=0.05, expansion_candidates=8,
        cap_aware_repair=True, reschedule_every=200,
    )
    for cfg in knobs.values():
        cfg.update(common)
    if cap is not None:
        knobs["lns"].update(accept="threshold", up_prob=0.12,
                            up_slack=2, snapback=4)
    else:
        knobs["lns"].update(accept="sa", snapback=8)
    knobs["anneal3"].update(anneal_iters=12000, ils_rounds=200,
                             sa_T0=(0.30, 0.55, 1.4, 0.25)[lane % 4], sa_T1=0.05,
                             restart_patience=(6000, 10000, 18000, 5000)[lane % 4])
    return knobs


def make_workers(count, profile="balanced", seed_policy="mixed", seed=20261020,
                 chunk_seconds=30.0, handoff="diverse"):
    if not 1 <= count <= 256:
        raise ValueError("workers must be between 1 and 256")
    # The 20-worker default allocates 4 depth3, 6 depth4, 4 depth5 and 6 free.
    balanced = [3, 4, 5, None, 4, None, 3, 4, 5, None,
                3, 4, 5, None, 4, None, 3, 4, 5, None]
    slots = []
    for i in range(count):
        if profile == "balanced":
            cap = balanced[i % len(balanced)]
        elif profile == "hunt87":
            cap = 5 if i % 3 == 0 else None
        elif profile in ("depth4", "calibrate90"):
            cap = 4
        elif profile == "depth3":
            cap = 3
        else:
            raise ValueError("unknown profile")
        lane = sum(w["cap"] == cap for w in slots)
        if cap == 3:
            key = "own97"
        elif cap == 4:
            key = "own91"
            if seed_policy == "mixed" and profile != "calibrate90" and lane % 2:
                key = "nist90"
        elif cap == 5:
            key = "derived88" if seed_policy == "mixed" and lane % 2 else "own88"
        else:
            choices = ["own88", "own88d7"]
            if seed_policy == "mixed":
                choices += ["jean88", "third88", "derived88", "own88"]
            key = choices[lane % len(choices)]
        path, provenance = SEEDS[key]
        group = "own" if provenance == "own-lineage" else "published"
        if seed_policy == "scratch":
            path, provenance, group, key = "scratch", "from-scratch", "scratch", "scratch"
        # The calibration profile never reads a public-90 candidate bank.
        if profile == "calibrate90" and seed_policy != "scratch":
            path, provenance = SEEDS["own91"]
            key, group = "own91", "calibration91"
        depth_name = "free" if cap is None else "d%s" % cap
        slots.append({
            "label": "%02d_%s_%s" % (i, depth_name, key),
            "cap": cap, "seed_path": path, "seed_key": key,
            "seed_provenance": provenance, "share_group": group,
            "byte_rotation": lane % 4,
            "random_seed": seed + 100003 * (i + 1),
            "cycle": ["anneal3", "lns"] if cap == 3 else ["walk", "lns", "lns"],
            "chunk_seconds": chunk_seconds,
            "handoff": handoff,
            "knobs": engine_knobs(lane, cap),
        })
    return slots
