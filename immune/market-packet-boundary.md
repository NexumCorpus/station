# Counterfactual immunity: market-packet-boundary

Status: **KILLED**

## Declared lesion
- Suite: `station` (registered, not supplied by this trial)
- Target: `station.py`
- Reason: The buyer packet must preserve its non-claim boundary rather than turning scope prose into market evidence.
- Find: `This packet does not claim customer demand, payment, safety certification, or a discovery result.`
- Replace: `This packet claims customer demand, payment, safety certification, and a discovery result.`

## Replay receipt
- Original sha256: `c8306e602542dc5a`
- Mutant sha256: `ad47fa9b8972d230`
- Baseline exit: `0`
- Mutant exit: `1`

## Kill condition
If the suite accepts a packet that claims demand or payment, the packet is promotional surface rather than an evidence boundary.

## Boundary
KILLED means this registered suite rejected this exact single-site lesion in a disposable copy. It does not prove complete coverage, safety, or general causal adequacy.
