"""Drift check (turn 71): §15's vital sign, made falsifiable at last — the final
open probe of THINKING/vital-sign-metric.md, unblocked by era 1 closing (>=2
closed eras now exist).

The metric the ledger converged on: metered burn per certification-era, trending
DOWN, is health; rising as certs accumulate is the §15 'decoration' signature.
Two anti-theater rules the ledger paid for, both honored here:
  1. EXCLUDE the era-0 backfill lump (a 28-day weighted floor, not a real
     cert-era; comparing an open era to it passes trivially).
  2. Don't punish BUILD eras — a cert-era legitimately spikes; only a SUSTAINED
     >1.5x rise in per-day burn from one real cert-era to the next counts.
Dormant (born-passing) until >=2 REAL cert-eras exist; then it fires the warning
if efficiency regressed across a cert boundary."""
import sys

sys.path.insert(0, "E:/station")
import station  # noqa: E402

eras, _cur = station._fold_eras()
real = [e for e in eras if e["days"] <= 7]   # drop the era-0 backfill lump (28d)

if len(real) < 2:
    print(f"CHECK-OK vital sign armed, DORMANT: {len(real)} real cert-era "
          f"(era-0 backfill lump excluded); fires when >=2 exist")
    sys.exit(0)

rates = [e["burn"] / max(e["days"], 1) for e in real]
rising = [(i, rates[i - 1], rates[i]) for i in range(1, len(rates))
          if rates[i] > rates[i - 1] * 1.5]
if rising:
    i, a, b = rising[-1]
    print(f"VITALSIGN-RISING: cert-era {real[i]['start']} per-day burn "
          f"{b:,.0f} > 1.5x prior {a:,.0f} — the §15 decoration signature "
          f"(burn/cert rose while certs accumulated). Re-aim at cheaper certs.")
    sys.exit(1)
print(f"CHECK-OK vital sign flat/falling across {len(real)} real cert-eras "
      f"(per-day burn {['{:,.0f}'.format(r) for r in rates]}) — §15 alive")
