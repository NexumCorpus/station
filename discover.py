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
BASELINE = (0, 0, 0)             # the "recombination" region
TRUE = (37, 37, 37)              # the hidden generalizable optimum (a crossing)
_MAXL1 = GRID * DIM              # max novelty distance for normalization
_SIGMA = 6.0                     # G basin width (climbable, but random rarely peaks)
NOISE_A = 0.3

TRAIN_SEEDS = (1, 2)                         # the decoy: few seeds -> overfittable
SEL_SEEDS = tuple(range(10, 18))             # selection holdout (the trojan fitness)
CERT_SEEDS = tuple(range(100, 150))          # meta-holdout: the ruthless judge


def novelty(c) -> float:
    return sum(abs(a - b) for a, b in zip(c, BASELINE)) / _MAXL1


def G(c) -> float:
    d2 = sum((a - b) ** 2 for a, b in zip(c, TRUE))
    return math.exp(-d2 / (2 * (_SIGMA ** 2)))     # generalizable basin around TRUE


def _noise(c, seed) -> float:
    h = hashlib.sha256(f"{c}|{seed}".encode()).digest()
    return (int.from_bytes(h[:4], "big") / 2**32 - 0.5) * 2 * NOISE_A


def score(c, seed) -> float:
    return G(c) + _noise(c, seed)


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


if __name__ == "__main__":
    import sys
    BUDGET = 4000
    print("# MAP-FILLER: fill the novelty axis with elites (selection-holdout fitness)")
    qd = map_elites(BUDGET, SEL_SEEDS)
    rs = random_search(BUDGET, SEL_SEEDS)
    bq = _report_fill("MAP-Elites", qd)
    br = _report_fill("random", rs)
    ok = (len(qd) >= len(rs) and bq and br and G(bq[1]) >= G(br[1]))
    print("SELFTEST-OK" if ok else "SELFTEST-FAIL",
          "MAP-Elites fills the map and reaches higher-G high-novelty elites than random"
          if ok else "(QD did not beat random — retune)")
    sys.exit(0 if ok else 1)
