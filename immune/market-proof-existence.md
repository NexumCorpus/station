# Counterfactual immunity: market-proof-existence

Status: **KILLED**

## Declared lesion
- Suite: `station` (registered, not supplied by this trial)
- Target: `station.py`
- Reason: A market thesis must not cite evidence that does not exist on the local body.
- Find: `if not isinstance(proof, str) or not Path(proof).is_file():`
- Replace: `if False:`

## Replay receipt
- Original sha256: `39b640a4c6064d2e`
- Mutant sha256: `00c2b23cdc161d09`
- Baseline exit: `0`
- Mutant exit: `1`

## Kill condition
If the station suite exits zero after the proof-existence check is removed, add a direct regression test before treating local proof as a market boundary.

## Boundary
KILLED means this registered suite rejected this exact single-site lesion in a disposable copy. It does not prove complete coverage, safety, or general causal adequacy.
