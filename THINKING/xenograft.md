# Xenograft — can a capability survive a foreign body?

The estate has learned to preserve itself, verify nearby broken versions, and
bind its future. A harder question remains: does a capability live in its
load-bearing artifact, or in the accumulated story around it?

The xenograft test performs a small transplant. A manifest names the exact
source bytes, their destination inside an empty temporary body, and one trusted
check file. The runner verifies every source hash, copies only those bytes, and
runs `python -E -s check.py` from the temporary body. The check must prove it
imported the transplanted module, not the original estate.

```
estate artifact ── hash-pinned manifest ──> stripped temporary body
                                            │
                                            └─> check passes / fails
```

This is neither a security sandbox nor independent scientific corroboration.
The manifest author still chose the files and check. It establishes the smaller,
useful property: *this declared capability is portable across an empty local
body without the rest of the station's state, configuration, or history.* A
failure is evidence of hidden dependence; the repair is to externalize the
missing dependency or narrow the claimed portability.

The first graft is the temporal witness's pure module. Its check will validate a
future forecast, evaluate a frozen JSONL route, and compute Brier loss while
asserting that `forecast` was imported from the transplanted directory. If it
fails, the temporal organ is still entangled with its birthplace.
