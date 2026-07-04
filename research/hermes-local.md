# Hermes (Nous Research) for local CPU-only use — research findings
Date: 2026-07-03. Hardware frame: 12900K, 32GB RAM, no usable GPU → ~7-9B q4 practical (~5-10 tok/s), 14B q4 marginal (~4-6 tok/s), 36B q4 fits RAM but ~1.5-2.5 tok/s.

## 1. Latest generation + sizes

**Current lineup (mid-2026):**
- **Hermes 4** (released 2025-08-25): **14B** (base: Qwen3-14B), **70B**, **405B** (Llama-3.1 bases).
  - https://hermes4.nousresearch.com/ , https://huggingface.co/NousResearch/Hermes-4-14B
- **Hermes 4.3 — 36B only** (Dec 2025): base = ByteDance Seed-OSS-36B, 512K context, first Hermes post-trained entirely on the **Psyche** decentralized network (DisTrO optimizer, 24 nodes, Solana-secured). Nearly matches/exceeds Hermes 4 70B at half the params.
  - https://nousresearch.com/introducing-hermes-4-3 , https://huggingface.co/NousResearch/Hermes-4.3-36B , official GGUF: https://huggingface.co/NousResearch/Hermes-4.3-36B-GGUF
- **NousCoder-14B** (late Dec 2025/Jan 2026): olympiad-coding model, Qwen3-14B + RL via Atropos. LiveCodeBench v6 pass@1 67.87% vs Qwen3-14B baseline 60.79%.
  - https://huggingface.co/NousResearch/NousCoder-14B

**Ollama availability — the key absence:** there is **NO official ollama library tag for Hermes 4 or 4.3**. Official library stops at **`hermes3`** (3b/8b/70b/405b): https://ollama.com/library/hermes3 → `ollama run hermes3:8b` (~4.7GB q4, the only one-command official Hermes).
- Hermes 4 14B on ollama: pull GGUF direct from HF: `ollama run hf.co/mradermacher/Hermes-4-14B-GGUF:Q4_K_M` (~9GB). https://huggingface.co/mradermacher/Hermes-4-14B-GGUF
- Hermes 4.3 36B community ollama: `ollama run gurubot/Hermes-4.3-36B-GGUF` or `HammerAI/hermes-4.3:36b-q4_K_M` (~22GB) — fits 32GB RAM but CPU-only ≈1.5-2.5 tok/s → not practical for interactive use. https://ollama.com/HammerAI/hermes-4.3 , https://ollama.com/gurubot/Hermes-4.3-36B-GGUF
- NousCoder-14B GGUF: `ollama run hf.co/bartowski/NousResearch_NousCoder-14B-GGUF:Q4_K_M` (~9GB). https://huggingface.co/bartowski/NousResearch_NousCoder-14B-GGUF

**Fit verdict for this box:** hermes3:8b = comfortable (5-10 tok/s). Hermes-4-14B q4 / NousCoder-14B q4 = usable-slow (~4-6 tok/s). Hermes-4.3-36B = fits RAM, too slow on CPU. 70B/405B = out.

## 2. What Hermes is tuned FOR vs base Llama/Qwen

From the Hermes 4 model cards + tech report (https://huggingface.co/NousResearch/Hermes-4-14B):
- **Function calling / tool use**: ChatML prompt format; tool schemas injected in system prompt inside `<tools>...</tools>`; model emits `<tool_call>{"name": ..., "arguments": {...}}</tool_call>` (JSON inside XML tags); results returned in `<tool_response>` tags. Parsers ship in vLLM/SGLang; ollama's hermes3 template maps this to the ollama tools API. Supports multiple/parallel tool calls in a single assistant turn.
- **Structured JSON output**: explicitly "trained to produce valid JSON for given schemas and to **repair malformed objects**" — schema-adherence is a first-class training target, not incidental.
- **Hybrid reasoning**: optional `<think>...</think>` deliberation toggled by flag/system prompt (Hermes 4/4.3; hermes3 lacks this).
- **Steerability / neutral alignment**: "extreme improvements on steerability, especially on reduced refusal rates"; system prompt obeyed strongly (personas, formats, refusal policy). This is the historic Hermes differentiator vs instruct-tuned Llama/Qwen.
- What it is NOT: a code-specialist (that's NousCoder / qwen2.5-coder territory).

## 3. Does Nous ship an actual agent framework? YES.

- **Hermes Agent** — https://github.com/NousResearch/hermes-agent , docs https://hermes-agent.nousresearch.com/docs/ — "the self-improving AI agent." v0.18.0 (2026-07-01), ~209k stars. Terminal + messaging platforms (Telegram/Discord/Slack/WhatsApp/Signal), 40+ tools, cron scheduler, isolated subagents, agent-curated memory, autonomous skill creation, execution backends (local/Docker/SSH/Modal/Daytona). Model-agnostic: Nous Portal, OpenRouter, OpenAI, **any custom OpenAI-compatible endpoint incl. ollama** (known rough edge with ollama thinking-models/context: issue #46833).
- **Atropos** — https://github.com/NousResearch/atropos — RL **environments** framework (trajectory collection/eval, ~1000 task verifiers); training infra, not a user agent. NousCoder was trained in it.
- **Forge** — commercial multi-model reasoning **API** (pipeline combining models), not local, not open.
- **Psyche** — decentralized training network (trained Hermes 4.3). Infra, not agentic.

## 4. Role recommendations

**(a) Small Python optimization scripts from spec:**
- **Primary: `qwen2.5-coder:7b`** — still the best code quality per token at CPU-viable speed; Hermes 8B/14B are generalists and lose to it on code.
- Quality-over-speed option: **NousCoder-14B q4** (`hf.co/bartowski/NousResearch_NousCoder-14B-GGUF:Q4_K_M`) — beats Qwen3-14B on LiveCodeBench, but ~4-5 tok/s and reasoning-token-hungry (thinks before coding) → slow wall-clock on CPU.
- Worth one test: `qwen3-coder:30b` (MoE, ~3.3B active params → CPU-fast despite ~19GB q4 footprint) if it's in the local ollama library; MoE is the one architecture that dodges the CPU wall. (Not deep-verified in this pass.)
- Hermes-class: not recommended for this role.

**(b) Logs/transcripts → fixed-schema one-line summaries + anomaly flags:**
- **Primary: `hermes3:8b` + ollama structured outputs** (`format: <json-schema>` in the API) — Hermes is the one family explicitly trained for schema-valid JSON + malformed-JSON repair and strong system-prompt adherence, and grammar-constrained decoding on top makes invalid JSON structurally impossible. Belt and suspenders.
- Load-bearing general fact: ollama's `format`/JSON-schema constraint (grammar-level, works with any model) matters more for *validity* than model choice; model choice then determines *content* quality (correct fields, sensible anomaly judgment). Hermes's tuning targets exactly that second half.
- Upgrade path if 4-6 tok/s acceptable: Hermes-4-14B q4 (`hf.co/mradermacher/Hermes-4-14B-GGUF:Q4_K_M`) — same tuning, newer/stronger, thinking OFF for throughput.
- qwen2.5:7b-instruct is an adequate fallback with the schema constraint but is less steerable on refusals/format edge cases.

## Sources
- https://hermes4.nousresearch.com/
- https://huggingface.co/NousResearch/Hermes-4-14B
- https://nousresearch.com/introducing-hermes-4-3
- https://huggingface.co/NousResearch/Hermes-4.3-36B-GGUF
- https://ollama.com/library/hermes3
- https://ollama.com/HammerAI/hermes-4.3
- https://ollama.com/gurubot/Hermes-4.3-36B-GGUF
- https://huggingface.co/mradermacher/Hermes-4-14B-GGUF
- https://github.com/NousResearch/hermes-agent
- https://hermes-agent.nousresearch.com/docs/
- https://github.com/NousResearch/atropos
- https://huggingface.co/NousResearch/NousCoder-14B
- https://huggingface.co/bartowski/NousResearch_NousCoder-14B-GGUF
