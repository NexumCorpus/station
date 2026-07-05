"""wall.py — mapping the recombination wall.

The estate has a DETECTOR of the wall (the gate: does a candidate beat holdout
the claimant never chose?). This turns the detector into a CARTOGRAPHER: place
each candidate in the (novelty-distance x holdout-margin) plane and read the
wall's topology. find -> map -> get through.

Two axes, both already measured by the estate's own machinery:
  distance = how far the candidate is from the RECOMBINATION baseline (known /
             reference solutions). Low = a remix of the known; high = genuinely
             different-shaped. (RDE: behavioral profile distance from reference
             policies.)
  margin   = HOLDOUT margin: performance on FRESH data the claimant never chose,
             vs the baseline. >0 = genuinely better, verified; <0 = OVERFIT (it
             looked better in-run and failed fresh) = the wall catching a
             pretender.

Four regions:
  THROUGH       distance>=D, margin> +eps  -- verified genuine novelty (the goal)
  PRETENDER     distance>=D, margin< -eps  -- novel-LOOKING but overfit; the wall
                                              caught it (RDE's in-run 'winners')
  RECOMBINATION distance<  D               -- a remix of the known (works or not)
  NOISE         else                       -- near the baseline, no signal

The WALL is the boundary between "recombination suffices" and "genuine novelty
required." A CROSSING is a THROUGH point. Mapping does not cross the wall — it
tells you the COORDINATE a crossing must be searched at (the empty region), which
turns "get through" from a wish into a directed search.
"""
from __future__ import annotations

REGIONS = ("THROUGH", "PRETENDER", "RECOMBINATION", "NOISE")


def classify(distance: float, margin: float, D: float = 0.15, eps: float = 0.02):
    if distance >= D:
        if margin > eps:
            return "THROUGH"
        if margin < -eps:
            return "PRETENDER"
        return "NOISE"
    return "RECOMBINATION" if abs(margin) > eps else "NOISE"


def map_wall(records, D: float = 0.15, eps: float = 0.02):
    """records: iterable of {name, distance, margin}. Returns (rows, summary)."""
    rows = []
    counts = {r: 0 for r in REGIONS}
    for c in records:
        region = classify(c["distance"], c["margin"], D, eps)
        counts[region] += 1
        rows.append({**c, "region": region})
    crossings = [r for r in rows if r["region"] == "THROUGH"]
    pretenders = [r for r in rows if r["region"] == "PRETENDER"]
    # where a crossing must be searched: the distance band pretenders cluster in,
    # but with a POSITIVE holdout margin instead of their negative one.
    target = None
    if pretenders and not crossings:
        ds = sorted(p["distance"] for p in pretenders)
        target = (ds[0], ds[-1])
    return rows, {"counts": counts, "crossings": len(crossings),
                  "target_band": target}


def _fmt(rows, summary, D, eps):
    out = [f"WALL MAP (D={D}, eps={eps}) | " +
           " ".join(f"{k}={v}" for k, v in summary["counts"].items()) +
           f" | crossings={summary['crossings']}"]
    for r in sorted(rows, key=lambda r: (-r["distance"])):
        out.append(f"  [{r['region']:13s}] {r['name']:22s} "
                   f"dist={r['distance']:+.3f} holdout-margin={r['margin']:+.4f}")
    if summary["target_band"]:
        lo, hi = summary["target_band"]
        out.append(f"  => NO CROSSING yet. To get through: search distance "
                   f"[{lo:.3f},{hi:.3f}] (as novel as the pretenders) with a "
                   f"POSITIVE holdout margin (unlike their overfit). The wall is "
                   f"mapped; the crossing is now a coordinate, not a wish.")
    return "\n".join(out)


# The canonical demo: RDE's real cache-eviction wall, from the audited receipts
# (runs/20260610_115502_cache_eviction_deterministic/claims.json). The two in-run
# "winners" beat the benchmark but LOST on fresh holdout and were flagged
# overfit:true -> the wall caught them. Reference policies define the baseline.
RDE_CACHE = [
    {"name": "ad_thrash", "distance": 0.225, "margin": -0.1706},   # overfit:true
    {"name": "ad_guard15", "distance": 0.256, "margin": -0.1367},  # overfit:true
    {"name": "W-TinyLFU(ref)", "distance": 0.0, "margin": 0.0},    # baseline
    {"name": "ARC(ref)", "distance": 0.0, "margin": 0.0},          # baseline
]


def demo():
    rows, summary = map_wall(RDE_CACHE)
    print("# RDE cache-eviction wall (real receipts, run 20260610_115502)")
    print(_fmt(rows, summary, 0.15, 0.02))
    return summary


def _selftest():
    synth = [
        {"name": "genuine", "distance": 0.4, "margin": 0.10},   # THROUGH
        {"name": "overfit", "distance": 0.4, "margin": -0.10},  # PRETENDER
        {"name": "remix", "distance": 0.05, "margin": 0.10},    # RECOMBINATION
        {"name": "flat", "distance": 0.05, "margin": 0.0},      # NOISE
    ]
    rows, s = map_wall(synth)
    got = {r["name"]: r["region"] for r in rows}
    want = {"genuine": "THROUGH", "overfit": "PRETENDER",
            "remix": "RECOMBINATION", "flat": "NOISE"}
    ok = got == want and s["crossings"] == 1
    print("SELFTEST-OK wall classifier maps all four regions" if ok
          else f"SELFTEST-FAIL {got}")
    return ok


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(0 if _selftest() else 1)
    demo()
