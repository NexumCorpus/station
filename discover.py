"""discover.py — the map-filler + the trojan horse for the recombination wall.

The wall (wall.py) is the (novelty-distance x holdout-margin) plane; the empty
THROUGH quadrant (novel AND verified) is what we want to reach. This is the
RUTHLESS search that fills the map and the TROJAN HORSE that crosses it, built on
a fully-deterministic toy domain we control — so the demo is an HONEST unit test
of the ENGINE (does it fill the map and, when a crossing EXISTS, find+certify it
while culling pretenders?), NOT a claim about any real domain. Whether a real
domain contains a crossing is the open empirical question (RDE: none in
cache-eviction yet).

THE TOY DOMAIN (a faithful minimal model of the overfit wall):
  candidate  = a point in a small integer grid (the search space).
  BASELINE   = the origin region = "recombination" (the known). novelty = L1
               distance from it, normalized.
  G(c)       = the GENERALIZABLE value: a Gaussian basin around a hidden TRUE
               point far from baseline. High G far from baseline = a real crossing.
  score(c,s) = G(c) + noise(c,s), noise deterministic per (candidate, seed),
               zero-mean over seeds. On FEW seeds noise can make a low-G candidate
               look great (OVERFIT); over MANY seeds it averages out (truth).
  splits     = TRAIN (few, the decoy) / SEL (the selection holdout, the trojan's
               hidden fitness) / CERT (disjoint meta-holdout, the ruthless judge).
The wall is real: far-from-baseline candidates that win on TRAIN are usually
noise-lucky pretenders; only the TRUE basin survives CERT.
"""
from __future__ import annotations

import hashlib
import math
import random

DIM = 3
GRID = 40                         # candidates in [0, GRID)^DIM = 64000 (budget << space)
BASELINE = (20, 20, 20)          # the "recombination" region = CENTER, so the
                                 # high-novelty shell spreads in ALL directions
TRUE = (5, 35, 35)               # a SPECIFIC high-novelty optimum (one direction);
                                 # other directions of the shell = pretenders far from it
_MAXR = ((GRID / 2) ** 2 * DIM) ** 0.5   # max radial distance from center
_SIGMA = 6.0                     # G basin width (climbable, but random rarely peaks)
# Overfitting modeled HONESTLY: a candidate "memorizes" a given seed's instance
# with prob OVERFIT_P, earning a bonus that does NOT generalize (present only on
# the seeds it memorized). Because a memorizer can grab the bonus on the FEW
# train seeds but almost never on the MANY holdout seeds, the holdout is far
# harder to game — that asymmetry IS the trojan.
OVERFIT_P = 0.15
OVERFIT_B = 2.0                  # > G_max=1, so a memorizer can win the tiny decoy

TRAIN_SEEDS = (1,)                           # the decoy: a single visible example =
                                             # maximally overfittable (1-shot fit)
SEL_SEEDS = tuple(range(10, 18))             # selection holdout (the trojan fitness)
CERT_SEEDS = tuple(range(100, 150))          # meta-holdout: the ruthless judge


def novelty(c) -> float:
    return (sum((a - b) ** 2 for a, b in zip(c, BASELINE)) ** 0.5) / _MAXR


def G(c) -> float:
    d2 = sum((a - b) ** 2 for a, b in zip(c, TRUE))
    return math.exp(-d2 / (2 * (_SIGMA ** 2)))     # generalizable basin around TRUE


def _overfits(c, seed) -> bool:
    h = hashlib.sha256(f"{c}|{seed}|of".encode()).digest()
    return (int.from_bytes(h[:4], "big") / 2**32) < OVERFIT_P


def score(c, seed) -> float:
    """Generalizable value + a non-generalizing memorization bonus on seeds this
    candidate happens to overfit."""
    return G(c) + (OVERFIT_B if _overfits(c, seed) else 0.0)


def mean_score(c, seeds) -> float:
    return sum(score(c, s) for s in seeds) / len(seeds)


# ---- MAP-Elites: fill an elite into every novelty cell -----------------------
NCELLS = 10


def _cell(c) -> int:
    return min(NCELLS - 1, int(novelty(c) * NCELLS))


def _rand_candidate(rng):
    return tuple(rng.randrange(GRID) for _ in range(DIM))


def _mutate(c, rng):
    return tuple(min(GRID - 1, max(0, x + rng.choice((-1, 0, 1)))) for x in c)


def map_elites(budget, fitness_seeds, seed=0):
    """Fill each novelty cell with the candidate of best fitness (mean over
    fitness_seeds). Returns {cell: (candidate, fit)}."""
    rng = random.Random(seed)
    archive = {}
    for _ in range(budget):
        if archive and rng.random() < 0.7:
            parent = rng.choice(list(archive.values()))[0]
            c = _mutate(parent, rng)
        else:
            c = _rand_candidate(rng)
        f = mean_score(c, fitness_seeds)
        cell = _cell(c)
        if cell not in archive or f > archive[cell][1]:
            archive[cell] = (c, f)
    return archive


def random_search(budget, fitness_seeds, seed=0):
    """Same budget, but no evolutionary reuse — pure random candidates."""
    rng = random.Random(seed + 999)
    archive = {}
    for _ in range(budget):
        c = _rand_candidate(rng)
        f = mean_score(c, fitness_seeds)
        cell = _cell(c)
        if cell not in archive or f > archive[cell][1]:
            archive[cell] = (c, f)
    return archive


def _report_fill(name, archive):
    hi = [(cell, cand, fit) for cell, (cand, fit) in archive.items() if cell >= 7]
    best_hi = max(hi, key=lambda x: G(x[1]), default=None)
    print(f"{name:12s} cells={len(archive)}/{NCELLS} | "
          f"high-novelty(>=0.7) cells filled={len(hi)} | "
          f"best high-novelty elite G(cert-truth)="
          f"{(G(best_hi[1]) if best_hi else 0):.3f} "
          f"at {best_hi[1] if best_hi else '-'}")
    return best_hi


# ---- the TROJAN HORSE: select on the holdout the proposer cannot see ---------
def trojan(n_pretend=5000, n_genuine=30, K=20, seed=0):
    """The pretender trap + its cure. A realistic pool: MOSTLY recombination-
    pretenders (random high-novelty, G~0) with a RARE sprinkle of genuine (near
    TRUE, high G) — exactly what a recombination proposer emits. The DECOY ranks
    by TRAIN (a single visible example — maximally overfittable). The TROJAN ranks
    by SEL holdout (8 hidden seeds — far harder to game). Certify both top-K on
    CERT truth. generator!=grader: the decoy crowns memorizing PRETENDERS; the
    holdout, which they cannot see, crowns the rare genuine."""
    rng = random.Random(seed)
    pool = []
    while len(pool) < n_pretend:                 # the recombination majority
        c = _rand_candidate(rng)
        if novelty(c) >= 0.6 and G(c) < 0.1:     # high-novelty AND far from TRUE
            pool.append(c)                       # = an actual pretender
    for _ in range(n_genuine):                   # the rare genuine (near TRUE)
        pool.append(tuple(min(GRID - 1, max(0, t + rng.choice((-2, -1, 0, 1, 2))))
                          for t in TRUE))
    scored = [(c, mean_score(c, TRAIN_SEEDS), mean_score(c, SEL_SEEDS), G(c))
              for c in pool]
    decoy = sorted(scored, key=lambda x: -x[1])[:K]     # ranked by the decoy
    troj = sorted(scored, key=lambda x: -x[2])[:K]      # ranked by the hidden holdout
    cert = lambda top: sum(x[3] for x in top) / len(top)  # mean CERT-truth G
    return {"decoy_cert": cert(decoy), "trojan_cert": cert(troj),
            "decoy_1": decoy[0], "trojan_1": troj[0]}


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "fill"
    if mode == "fill":
        print("# MAP-FILLER: fill the novelty axis with elites (selection-holdout fitness)")
        qd = map_elites(4000, SEL_SEEDS)
        rs = random_search(4000, SEL_SEEDS)
        bq = _report_fill("MAP-Elites", qd)
        br = _report_fill("random", rs)
        ok = len(qd) >= len(rs) and bq and br and G(bq[1]) >= G(br[1])
        print("SELFTEST-OK" if ok else "SELFTEST-FAIL",
              "MAP-Elites fills the map + reaches higher-G high-novelty elites than random")
        sys.exit(0 if ok else 1)
    else:  # trojan
        r = trojan()
        print("# TROJAN HORSE: select on the holdout the proposer cannot see")
        print(f"  DECOY  (rank by TRAIN, the visible decoy): top-20 mean CERT-truth "
              f"G = {r['decoy_cert']:.3f}  | #1 {r['decoy_1'][0]} train={r['decoy_1'][1]:.2f} certG={r['decoy_1'][3]:.3f} = PRETENDER")
        print(f"  TROJAN (rank by SEL holdout, hidden):      top-20 mean CERT-truth "
              f"G = {r['trojan_cert']:.3f}  | #1 {r['trojan_1'][0]} sel={r['trojan_1'][2]:.2f} certG={r['trojan_1'][3]:.3f} = genuine")
        lift = r['trojan_cert'] - r['decoy_cert']
        ok = lift > 0.2
        print(f"SELFTEST-{'OK' if ok else 'FAIL'} the hidden holdout culls the pretenders "
              f"the decoy crowns (+{lift:.3f} CERT-truth) — a recombination-only proposer, "
              f"steered by what it cannot see, yields genuine novelty")
        sys.exit(0 if ok else 1)
