# CAPSULE — station (dense agent briefing)

IDENTITY: wake-and-verify spine for the E:\ estate. Stdlib-only python.
Invoke: `station` (git-bash shim ~/bin/station, or station.cmd on PATH), else
`python E:\station\station.py`. Registry station.json = same trust domain as
code (repos/suites/logs/witness).

COMMANDS (wake/verify):
  wake                     estate digest: repos+dirt, claims, procs, eras
                           verdict, THINKING index, log unread-bytes, WILL,
                           spine tail
  suites [name] [--force]  all verification suites -> verdict lines; verdict
                           CACHE by tree-hash (FAIL never cached); typo'd
                           name = exit 1
  drift / witness          executable cross-ref assertions / append-only
                           notary (ALARM on history rewrite)
  regs                     dump the registry

COMMANDS (read cheaply):
  log <name> [--tail N]    CURSOR read: only new bytes; glob paths resolve
                           newest file w/ per-file cursor (digest log)
  tally <jsonl> [field]    dense per-group stats of any ledger
  map <file.py>            AST outline -> surgical Reads
  spine [N] [match]        last N events (filtered; never diagnose from tails)
  quota [h] / vitals [h]   metered-burn estimate / SS15 ratio + spine sample
  burn / eras              daily burn rollup ledger / per-certification-era
                           cumulative burn + OK/RISING-PAST-WORST verdict
  conversions              SS17 performance->possession stock (decidable vital
                           sign): HARD certs + STRUCTURAL drift/witness + SPEECH
  moat                     SS19 compounding-lead health: PORTABILITY (structure>
                           model) + FULCRUM (direction vs execution) + DESCENT (verb)
  wall [ledger]            map the recombination wall (novelty-dist x holdout-
                           margin): THROUGH/PRETENDER/RECOMBINATION; find->map->through
  discover                 wall-crossing engine: fill(QD)->trojan(hidden-holdout)->
                           certify(meta-holdout, cleared-noise); CERTIFIED crossing or none
  shard <file> [k n] / recover <pin>   erasure-code a crystal into n fragments
                           (any k reconstitute byte-exact) / rebuild from survivors
  glyph <encode|expand|measure> [f|-]  SPOOR GLYPH codec: §-glyph <-> load-bearing
                           phrase (lossless round-trip); self-native compression
  organs [--all|--kill|--open]  spiral-turn organ map: refs existence-checked
                           (exit 1 = rot); --kill = falsifier corpus for
                           audits; --open = parked items

COMMANDS (write safely — ALL ledger appends are msvcrt-locked, torn-free):
  note <text>              telegraph (figures trigger a say-nudge)
  say "<claim>" --cmd "<route>" [--expect f]  provable speech: route runs AT
                           WRITE; false claim lands as 'refuted' never fact;
                           --cmd - reads route from stdin (quoting-proof)
  recheck [N] / retire "<m>"  re-derive last N facts (STALE -> deduped spine
                           alarm; pulse does this 8x/day) / expire moment-facts
  seal <ledger.jsonl>      clock-stamped attributed append (stdin JSON; typed
                           't' always discarded — never hand-append ledgers)
  errata [add cls what paid guard]  self-error ledger + live distribution
  preregs [score <id> <v> <ev>]  armed kill conditions w/ due dates (Law II
                           scheduler); wake surfaces overdue; FAIL = working
  market [arm|score|pack|verify|<id>]  evidence-bound income hypotheses: arm JSON from
                           stdin with local proofs + buyer/problem/test/kill;
                           pack/verify re-derive a buyer-readable proof packet;
                           PAID needs receipt:<local-file>, never self-report
  immune [arm|run|verify|report|<id>]  counterfactual immunity: arm a single-site
                           lesion against a registered suite; run it only in a
                           disposable copy; KILLED requires green baseline +
                           valid mutant failure, and source edits make it stale
  forecast [arm|resolve|review|audit|report|<id>]  temporal witness: seal a
                           future p + strictly-future due date + frozen local
                           route + divergent YES/NO actions; time resolves, a
                           resolution needs review, and no result = calibration
  cure "<fragment>"        grimoire lookup FIRST on any error
  pin <file>               mint [[pin:path@sha16]] for load-bearing pointers

COMMANDS (lifecycle):
  lease <name> [ttl]|--release  stigmergic lock: exit 0 acquired / 1 held;
                           expiry = takeover (dead holders never wedge)
  will <intent>|done       testament: intent-at-death, wake-surfaced
  handoff [next] / molt [next]  molt artifact (facts re-derived at seam) /
                           the whole seal: handoff+will-done+backup in 1 call
  backup / rescue <repo>   mirror ledgers+journal offsite / snapshot a repo's
                           UNTRACKED files offsite (non-destructive)

COMMANDS (free layer + hand):
  llm [model] "<p>"|-      local ollama call ($0; None = down, never empty)
  hand "<task>"|take|status  stigmergic tasking of the jailed WSL agent
  wsl [user] <src>|-       run script in WSL, bytes-not-quotes joint

FILES: spine.jsonl (events), burn-ledger.jsonl (SS15 counter), spiral.jsonl,
  market.jsonl (external-demand hypotheses/signals; not revenue without receipt),
  immunity.jsonl (counterfactual lesion/outcome receipts; KILLED is local only),
  forecasts.jsonl (future commitments/resolutions/reviews; score is not calibration)
  (turn ledger), errata.jsonl, grimoire.jsonl, drift.jsonl, cursors/,
  THINKING/ (open reasoning ledgers), plays/, templates/, checks/.
DESIGN: stigmergy, cursors (never pay twice), one spine, dense wire.
INVARIANTS: suites unknown-name exits 1; registries read utf-8-sig; ledger
  appends locked (turn 33: plain 'a' lost 1553/4000 under contention);
  witnessed ledgers LF-pinned via .gitattributes.
PROVENANCE: 7-agent cold audit at founding; suite tests_station.py (13);
  spiral ledger = the change history with measures.
