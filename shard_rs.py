"""shard_rs — deterministic erasure coding for SHARDs (spiral, the shard turns).

Reed-Solomon over GF(2^8) via a SYSTEMATIC CAUCHY generator matrix. This is the
trusted-code decoder the whole SHARD primitive rests on: a PIN detects loss, a
SHARD repairs it. Any k of n fragments reconstitute the crystal BYTE-EXACT; a
mis-decode is caught downstream by rehashing the result against the crystal's
own PIN (never a silent wrong estate). Deterministic — NOT an LLM — so the
verdict is reproducible, which is the property that separates a shard from a
flaky pin (the design panel's load-bearing finding, 2026-07-05).

Stdlib only (station's law). This module is a ROOTS Tier-1 trusted root: a
byte-change here expires its audit (checks/roots.py pins it).
"""
from __future__ import annotations

# --- GF(2^8), primitive poly 0x11d (x^8+x^4+x^3+x^2+1), generator 2 ----------
_EXP = [0] * 512
_LOG = [0] * 256


def _init_gf():
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11d
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_gf()


def gmul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def ginv(a: int) -> int:
    if a == 0:
        raise ZeroDivisionError("GF inverse of 0")
    return _EXP[255 - _LOG[a]]


# --- systematic Cauchy generator: rows 0..k-1 = identity, k..n-1 = Cauchy -----
def _gen_matrix(k: int, n: int):
    if n > 256:
        raise ValueError("n must be <= 256 (GF(2^8))")
    G = [[0] * k for _ in range(n)]
    for i in range(k):
        G[i][i] = 1                      # data fragments pass through (systematic)
    for i in range(k, n):
        for j in range(k):
            G[i][j] = ginv(i ^ j)        # Cauchy 1/(x_i + y_j), + is XOR in char 2
    return G


def _mat_inv(M, k):
    """Invert a k x k GF(256) matrix by Gauss-Jordan; None if singular."""
    A = [list(row) + [1 if c == r else 0 for c in range(k)]
         for r, row in enumerate(M)]
    for col in range(k):
        piv = next((r for r in range(col, k) if A[r][col] != 0), None)
        if piv is None:
            return None
        A[col], A[piv] = A[piv], A[col]
        inv = ginv(A[col][col])
        A[col] = [gmul(v, inv) for v in A[col]]
        for r in range(k):
            if r != col and A[r][col] != 0:
                f = A[r][col]
                A[r] = [a ^ gmul(f, b) for a, b in zip(A[r], A[col])]
    return [row[k:] for row in A]


def encode(data: bytes, k: int, n: int):
    """Split data into n fragments; any k reconstitute it. Returns (frags, orig_len)."""
    if not 1 <= k <= n <= 256:
        raise ValueError("need 1 <= k <= n <= 256")
    L = (len(data) + k - 1) // k
    padded = data + b"\x00" * (L * k - len(data))
    chunks = [padded[j * L:(j + 1) * L] for j in range(k)]
    G = _gen_matrix(k, n)
    frags = []
    for i in range(n):
        if i < k:
            frags.append(bytes(chunks[i]))
        else:
            out = bytearray(L)
            row = G[i]
            for b in range(L):
                acc = 0
                for j in range(k):
                    acc ^= gmul(row[j], chunks[j][b])
                out[b] = acc
            frags.append(bytes(out))
    return frags, len(data)


def decode(frags: dict, k: int, n: int, orig_len: int):
    """Reconstitute from {index: fragment_bytes}; need >=k. None if impossible."""
    idxs = sorted(frags)[:k]
    if len(idxs) < k:
        return None
    L = len(frags[idxs[0]])
    if any(len(frags[i]) != L for i in idxs):
        return None
    Minv = _mat_inv([_gen_matrix(k, n)[i] for i in idxs], k)
    if Minv is None:
        return None
    surv = [frags[i] for i in idxs]
    chunks = [bytearray(L) for _ in range(k)]
    for b in range(L):
        for r in range(k):
            acc = 0
            for c in range(k):
                acc ^= gmul(Minv[r][c], surv[c][b])
            chunks[r][b] = acc
    return b"".join(bytes(c) for c in chunks)[:orig_len]


def _selftest():
    import hashlib
    import itertools
    ok = True
    for (k, n) in [(4, 6), (3, 6), (2, 3), (8, 12), (1, 1)]:
        data = bytes((i * 37 + 11) & 0xff for i in range(1000)) + b"crystal-tail"
        frags, olen = encode(data, k, n)
        pin = hashlib.sha256(data).hexdigest()[:16]
        # exhaustively drop every (n-k)-subset for small n; sample for large
        losses = list(itertools.combinations(range(n), n - k))
        tested = 0
        for drop in losses:
            surv = {i: frags[i] for i in range(n) if i not in drop}
            rec = decode(surv, k, n, olen)
            if rec != data or hashlib.sha256(rec).hexdigest()[:16] != pin:
                print(f"FAIL k={k} n={n} drop={drop}")
                ok = False
            tested += 1
        # k==n edge (no redundancy) still round-trips with 0 losses
        print(f"  k={k} n={n}: {tested} erasure patterns reconstituted byte-exact, pin={pin}")
    print("SELFTEST-OK erasure coding reconstitutes byte-exact under all tested losses"
          if ok else "SELFTEST-FAIL")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if _selftest() else 1)
