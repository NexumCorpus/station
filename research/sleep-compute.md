# Sleep-time compute & offline cognition for LLM agents — research digest
Date: 2026-07-03. Scope: Letta sleep-time compute, offline consolidation systems, failure modes, and what a nightly local-7B cron can safely do.

---

## 1. Letta sleep-time compute — exact mechanism and evidence

**Paper:** "Sleep-time Compute: Beyond Inference Scaling at Test-time" — Lin, Snell, Wang, Packer, Wooders, Stoica, Gonzalez (Letta / UC Berkeley), arXiv:2504.13171, submitted 2025-04-17.
- https://arxiv.org/abs/2504.13171
- Blog: https://www.letta.com/blog/sleep-time-compute/
- Code/benchmarks: https://github.com/letta-ai/sleep-time-compute

### Mechanism (paper)
- Decompose a prompt into persistent **context c** and **query q**. Offline (idle time), the model processes c *without knowing q*: it anticipates likely queries, draws inferences, pre-computes useful quantities, and **rewrites c into a "learned context" c′** (natural-language artifact, produced via prompted self-editing, e.g. `rethink_memory`-style calls).
- At test time the model answers q against c′ instead of raw c — so less test-time reasoning is needed.
- Artifacts = rewritten context / enriched memory state (text), not weights. Consumed by simple substitution into the awake agent's context window.

### Mechanism (Letta product implementation)
- Docs: https://docs.letta.com/guides/agents/architectures/sleeptime/ ; https://deepwiki.com/letta-ai/letta-python/12.3-sleeptime-and-background-agents
- Creating a sleeptime-enabled agent spawns **two agents sharing memory blocks**: a **primary agent** (talks to user, calls tools, searches external memory — but has NO tools to edit its own core memory blocks) and a **sleep-time agent** (owns memory editing: `rethink_memory` etc., rewrites the primary's in-context memory blocks asynchronously, "anytime" fashion).
- Trigger: every N steps/messages, **default N=5**, configurable via `sleeptime_agent_frequency`; higher frequency = more tokens burned but more revision cycles. Also used for async document ingestion (sleep-time agent parses uploads into memory).
- Multi-agent architecture note: sleep-time agents are "a special form of multi-agent architecture where all agents share one or more memory blocks"; they convert "raw context" (conversation history, files) into "learned context" (distilled insights). Non-blocking: primary never waits.
- Community best practices: https://forum.letta.com/t/sleeptime-agents-for-memory-consolidation-best-practices-guide/154

### Measured gains
- **~5x reduction in test-time compute** at matched accuracy on Stateful GSM-Symbolic and Stateful AIME.
- Scaling sleep-time compute raises accuracy **up to +13% (Stateful GSM-Symbolic)** and **+18% (Stateful AIME)**.
- **Amortization:** sharing one sleep-time pass across related queries about the same context cuts average cost/query **~2.5x** (Multi-Query GSM-Symbolic).
- Case study on a realistic agentic SWE task (SWE-Features) showing applicability beyond math.

### Where gains were NOT found (paper is explicit)
- **Query predictability is the gating variable**: efficacy correlates with how predictable the query is from the context. For **unpredictable / context-unrelated queries, sleep-time compute underperforms plain test-time compute** — the offline work is wasted or off-target.
- One-shot, unrelated queries get no amortization benefit; the win requires repeated queries over a persistent context.
- On the hardest / least predictable instances, standard test-time scaling (incl. parallel sampling) remains competitive or better.
- No claim of gains from weight updates — this is purely context rewriting.

---

## 2. Other credible offline-consolidation systems/papers

| System | Mechanism | Evidence |
|---|---|---|
| **"Do Language Models Need Sleep? Offline Recurrence"** (Lee, McLeish, Goldstein, Fanti; arXiv:2605.26099, May 2026) https://arxiv.org/abs/2605.26099 | When KV cache fills, model enters "sleep": multiple forward passes over accumulated context, recursively updating **persistent fast weights** via a learned local rule, then clears the cache. Wake-time latency preserved. | Solves controlled tasks (cellular automata, multi-hop graph retrieval, long math) where plain transformers and SSM-attention hybrids fail. Architecture-level: requires training the consolidation rule — not a drop-in for existing agents. |
| **"LLMs Need Sleep: Learning to Self-Modify and Consolidate Memories"** (arXiv:2606.03979) https://www.emergentmind.com/papers/2606.03979 | Two-phase sleep: (1) consolidation = upward distillation of a smaller-self's memories into a larger net; (2) **"dreaming"** = RL-generated synthetic curriculum to rehearse new knowledge. | Ablations: removing dreaming or consolidation causes "dramatic reduction in durable knowledge integration and generalization." Weight-training pipeline, heavy. |
| **ExpeL** (Zhao et al., arXiv:2308.10144) https://arxiv.org/pdf/2308.10144 | Offline pass over collected trajectories → abstracts **natural-language insights** (guidelines/constraints) + stores successful trajectories; at test time injects insights + retrieves top-k similar successes as few-shot examples. **No gradient updates.** | Improvements on HotpotQA / ALFWorld / WebShop over ReAct/Reflexion baselines. The closest published template for "pre-digest state before the main agent wakes." |
| **Generative Agents reflection** (Park et al. 2023) | Periodic offline synthesis of raw memory-stream observations into higher-level reflections used for retrieval. | Ablation: removing reflection degraded agents from coherent multi-day planning to repetitive context-free behavior within ~48 simulated hours (cited in memory surveys, e.g. arXiv:2603.07670). |
| **MemoryBank** (Zhong et al. 2024) | Vector-DB memories refreshed/decayed on an Ebbinghaus forgetting-curve schedule; periodic summary updates. | Long-term companion-chat evaluations; weaker evidence than the above. |
| **Mem0** (Chhikara et al. 2025) | Online+offline extraction and consolidation pipeline (ADD/UPDATE/DELETE ops on salient facts). | Reported large token/latency savings vs full-context replay; widely deployed; consolidation quality critiques exist (see §3). |
| 2026 experience-distillation lineage: **EvolveR** (arXiv:2510.16079), **Decocted Experience** (arXiv:2604.04373), **MemMA** (arXiv:2603.18718), **ExpSeek** (arXiv:2601.08605) | Offline "self-distillation" of trajectories into instance-level + principle-level experience; injected at test time. | Benchmarked gains on web/agent tasks; young literature, mostly single-paper evidence each. |

Survey anchor: "Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers" (arXiv:2603.07670) frames consolidation as **offline policy improvement on already-collected data** (offline-RL analogy).

**Absence noted:** no rigorous public evaluation found of commercial "background agents" (Cursor background agents, Devin knowledge refresh, etc.) doing measured offline consolidation — marketing exists, evidence does not. Letta remains the only production system with a paper attached.

---

## 3. Failure modes & keeping offline rewrites safe

### Documented failure modes
- **Error propagation / experience-following** — "How Memory Management Impacts LLM Agents" (arXiv:2505.16067): high input-similarity retrieval makes agents reproduce past outputs; erroneous stored experiences compound ("error propagation"), and even correct-looking past executions can mislead ("misaligned experience replay"). https://arxiv.org/abs/2505.16067
- **Memory misevolution** — MemEvoBench (arXiv:2604.15774): iterative updates corrupt memory; **riskiest operations = summarization/compression (lossy distortion), memory merging (conflict amplification), long-horizon consolidation, retrieval-augmented updates (poisoning vector)**. https://arxiv.org/pdf/2604.15774
- **Hallucinated consolidation** — TRUSTMEM (arXiv:2606.25161): retrieval-based consolidation introduces hallucinations/factual drift; existing managers lack any check that the consolidated memory is faithful to sources. https://arxiv.org/pdf/2606.25161
- **Longitudinal safety drift** — "Remembering More, Risking More" (arXiv:2605.17830): safety risks accumulate in memory-equipped agents over time.
- **Unbounded stores** silently degrade via stale facts + cross-context contamination (practitioner synthesis: https://tianpan.co/blog/2026-04-12-the-forgetting-problem-when-agent-memory-becomes-a-liability).

### What the literature says keeps rewrites SAFE
Converging prescriptions (TRUSTMEM + MemEvoBench + 2505.16067):
1. **Candidates, not overwrites** — evaluate candidate consolidations against source material before acceptance; never destructively rewrite (TRUSTMEM's core design).
2. **Provenance chains** — every derived memory keeps links to its source interactions/ledger lines; re-verification against sources must stay possible (TRUSTMEM, MemEvoBench "periodic verification").
3. **Independent verification** — a judge/evaluator distinct from the generator checks semantic+factual fidelity of the rewrite; conservative acceptance thresholds (TRUSTMEM; generator≠grader).
4. **Audit log of all memory modifications** for anomaly detection; redundancy of critical memories (MemEvoBench).
5. **Feedback-gated addition + active deletion** of bad experiences beats naive accumulation (2505.16067: trajectory evaluators mitigate error propagation).
6. Treat consolidated artifacts as **derived caches over an append-only source of truth**, rebuildable at any time — the append-only ledger IS the safety mechanism.

---

## 4. Nightly cron, local 7B on CPU, append-only ledgers — what pays off

Small-model reality check: faithfulness scales with size — ≤20B models average **0.61 faithfulness (vs 0.81 for >70B)** with huge variance (FaithJudge/RAG leaderboards, arXiv:2505.04847); Llama3.1-8B produces **17–30% unfaithful abstractive summaries** (CNNDM/SAMSum/XSum; arXiv:2510.09915 lineage), though a well-tuned 7B can hit GPT-4-level hallucination rates on *grounded extractive* tasks (Vectara HHEM: https://www.vectara.com/blog/do-smaller-models-hallucinate-more). Conclusion: **7B is trustworthy when extractive/schema-bound and checkable, untrustworthy when abstractively compressing.**

### DO (ranked, best evidence of payoff)
1. **Log digestion into fixed-schema summaries** — per-entry classify/tag/extract into rigid fields (who/what/verdict/refs), extractive-leaning, each field carrying a ledger-line reference. Best-case regime for sleep-time compute: the downstream queries ("what happened / what's unread / what failed") are maximally predictable, which is exactly where 2504.13171 found the gains. Schema + provenance makes output mechanically checkable, neutralizing 7B weakness.
2. **Memory-index refresh PROPOSALS** — candidate re-tags, dedup flags, cross-link suggestions, stale-entry nominations, written to a proposals file for the strong awake agent (or human) to accept. Directly implements TRUSTMEM's candidates-not-overwrites; wrong proposals cost one review glance, not corruption. This is ExpeL's offline-insights pattern with the acceptance gate the safety literature demands.
3. **Anomaly/inconsistency flagging** — pointer-only output: "ledger line X contradicts line Y", "suite Z hasn't reported in N days". Flags are advisory and cheap to verify; a weak model pointing at real bytes cannot corrupt anything. (Weakest direct literature support of the three — justified by the asymmetry: low cost of false positives, provenance built in.)

### DO NOT attempt with a 7B
- **Destructive rewrite/compression of memory** — the two riskiest operations in MemEvoBench (summarization/compression, merging) executed by the model class with 17–83% unfaithful-summary rates; hallucinated compression then gets experience-followed → error propagation (2505.16067).
- **Abstract insight/hypothesis pre-generation** ("dreaming" a strategy layer) — paper gains came from frontier models on predictable queries; a 7B's abstractive inferences over sparse logs are exactly the hallucinated-consolidation failure TRUSTMEM measures. If wanted at all, run it on the strong model at wake-time over the 7B's *digests*.
- **Autonomous deletion/merging of ledger or memory entries** — violates append-only and every mitigation in §3.
- **Weight-level consolidation** (fast-weights 2605.26099, distill/dream 2606.03979) — requires training infrastructure; irrelevant to a CPU cron.

---

## Source list
- arXiv:2504.13171 — Sleep-time Compute (Letta/Berkeley) — https://arxiv.org/abs/2504.13171
- Letta blog — https://www.letta.com/blog/sleep-time-compute/ ; docs — https://docs.letta.com/guides/agents/architectures/sleeptime/ ; code — https://github.com/letta-ai/sleep-time-compute ; forum best-practices — https://forum.letta.com/t/sleeptime-agents-for-memory-consolidation-best-practices-guide/154
- arXiv:2605.26099 — Do LMs Need Sleep? Offline Recurrence — https://arxiv.org/abs/2605.26099
- arXiv:2606.03979 — LLMs Need Sleep (self-modify + dream) — https://www.emergentmind.com/papers/2606.03979
- arXiv:2308.10144 — ExpeL — https://arxiv.org/pdf/2308.10144
- arXiv:2603.07670 — Memory for Autonomous LLM Agents survey — https://arxiv.org/html/2603.07670v1
- arXiv:2606.25161 — TRUSTMEM — https://arxiv.org/pdf/2606.25161
- arXiv:2604.15774 — MemEvoBench — https://arxiv.org/pdf/2604.15774
- arXiv:2505.16067 — Experience-Following study — https://arxiv.org/abs/2505.16067
- arXiv:2605.17830 — Remembering More, Risking More — https://arxiv.org/pdf/2605.17830
- arXiv:2505.04847 — RAG faithfulness leaderboards — https://arxiv.org/html/2505.04847v1
- Vectara: Do Smaller Models Hallucinate More? — https://www.vectara.com/blog/do-smaller-models-hallucinate-more
- arXiv:2510.16079 (EvolveR), 2604.04373 (Decocted Experience), 2603.18718 (MemMA), 2601.08605 (ExpSeek)
- Practitioner: https://tianpan.co/blog/2026-04-12-the-forgetting-problem-when-agent-memory-becomes-a-liability
