# Counterfactual immunity: market-paid-receipt

Status: **KILLED**

## Declared lesion
- Suite: `station` (registered, not supplied by this trial)
- Target: `station.py`
- Reason: PAID must be an externally grounded event, not a string the model can type into a ledger.
- Find: `if not receipts or any(not receipt.is_file() for receipt in receipts):`
- Replace: `if False:`

## Replay receipt
- Original sha256: `5ebb3f6d1657b2ae`
- Mutant sha256: `db81ce3f0d9cfd23`
- Baseline exit: `0`
- Mutant exit: `1`

## Kill condition
If the station suite exits zero after receipt existence is bypassed, payment integrity is decorative and the market organ must be narrowed.

## Boundary
KILLED means this registered suite rejected this exact single-site lesion in a disposable copy. It does not prove complete coverage, safety, or general causal adequacy.
