# Recursive Language Models (RLM) — research findings

Date: 2026-07-03. Task: mechanism / results / limits / minimal local harness.

## Paper identification

- **The RLM paper is arXiv:2512.24601** — "Recursive Language Models", Alex L. Zhang, Tim Kraska, Omar Khattab (MIT CSAIL), submitted 2025-12-31.
  - https://arxiv.org/abs/2512.24601 (HTML: https://arxiv.org/html/2512.24601v1)
- **Precursor: Oct 2025 MIT blogpost** by Alex Zhang & Omar Khattab (same line of work, earlier results): https://alexzhang13.github.io/blog/2025/rlm/
- **arXiv:2510.04871 is NOT the RLM paper.** It is "Less is More: Recursive Reasoning with Tiny Networks" (Jolicoeur-Martineau, TRM/HRM — recursive *weight-tied networks*, unrelated inference paradigm). The "Zhang & Khattab Oct 2025" reference in the wild is the blogpost above, not that arXiv ID.
- Code IS released, MIT license:
  - Full engine: https://github.com/alexzhang13/rlm (OpenAI/Anthropic/OpenRouter/Portkey/vLLM backends; local `exec`, IPython, Docker, Modal, E2B sandboxes; RL training harness on prime-rl; trajectory visualizer)
  - Minimal reference: https://github.com/alexzhang13/rlm-minimal
  - Third-party reimpl: https://github.com/fullstackwebdev/rlm_repl
- HF paper page: https://huggingface.co/papers/2512.24601 · Khattab thread: https://x.com/lateinteraction/status/2007212972721275281

## 1. Core mechanism

The insight (Khattab's framing): not "LLM calls itself" but **the LLM interacts with its own prompt as an object**.

- The long prompt is **never put in the root model's context**. It is stored as a Python variable (`context`) inside a **REPL environment**. The root LM (depth 0) receives only the user query + metadata (total length, structure hints).
- Loop: root LM emits Python code → harness `exec`s it → stdout/prints are fed back → repeat. Inside the REPL the model can:
  - **peek** (slice `context[:2000]`), **grep** (regex/keyword filter), **partition** (chunk by tokens/newlines/headers),
  - call **`llm_query(prompt)`** — a recursive sub-LM call (depth 1, plain LM not RLM) over a snippet (~up to 500K chars per sub-call),
  - accumulate results in variables (buffer stitching).
- **Termination:** the root emits `FINAL(answer)` or `FINAL_VAR(varname)`.
- **Depth:** all experiments use depth = 1 (root RLM + plain-LM sub-calls). Deeper recursion is future work.
- Emergent strategies observed (not hard-coded): peek → grep → partition+map → per-chunk sub-query → aggregate → verify.

## 2. Headline results

Instantiation: GPT-5 / GPT-5-mini as root in the Python REPL.

| Benchmark | Base GPT-5 | RLM(GPT-5) |
|---|---|---|
| OOLONG (131K tok, semantic aggregation) | 44.0% | 56.5% |
| OOLONG-Pairs (32K, pairwise reasoning) | ~0.04% | 58.0% |
| BrowseComp-Plus (multi-hop QA, 6–11M tok) | 0% (overflow) | 91.3% |
| CodeQA (repo QA, 23K–4.2M tok) | 24.0% | 62.0% |

- Handles inputs **up to two orders of magnitude beyond the context window** (10M+ tokens; blogpost: near-perfect on BrowseComp-Plus at 1,000 docs ≈ 10M+ tok).
- Blogpost: RLM(GPT-5-mini) beat GPT-5 on OOLONG by ~34 pts (~114% relative) **at comparable API cost**.
- Post-trained **RLM-Qwen3-8B**: +28.3% avg over base Qwen3-8B; approaches vanilla GPT-5 on 3 long-context tasks — small models CAN be trained into the role.
- **Cost:** median comparable or cheaper than direct ingestion (BrowseComp-Plus: $0.99 avg vs $1.50–2.75 direct); up to 3× cheaper than a summarization agent while up to 29% better. High variance (trajectory length varies).
- Ablation: RLM without sub-calls is fine on sparse retrieval but drops 10–59% on information-dense tasks — the recursion is load-bearing for aggregation, the REPL alone suffices for retrieval.

## 3. Failure modes / limits (as reported)

- **Sequential blocking sub-calls → slow** (seconds to minutes; no async, no prefix caching in the released impl).
- **Brittle termination:** models emit plans/thoughts without `FINAL()`; redundant self-verification loops burn tokens (one trace: 5+ re-verify cycles).
- **Model-dependent behavior:** GPT-5 ≈ 10 sub-calls; Qwen3-Coder fires *thousands* on simple tasks unless the prompt explicitly warns against over-calling. Prompts don't transfer across models.
- **Small models struggle as the ROOT** (untrained Qwen3-8B: insufficient coding ability); thinking models can exhaust output budget.
- **No cost/runtime guarantees**; depth capped at 1; counting-type tasks degrade at extreme lengths.

## 4. Minimal harness — qwen2.5-coder:7b via ollama + Python stdlib

Feasibility: yes, but the paper's evidence says a 7B is a **weak root** and a fine **sub-worker**. Design accordingly.

### Essential design choices

1. **Don't give a 7B the full open REPL.** The paper's failure data (Qwen3-8B too weak to drive codegen; Qwen3-Coder sub-call explosions) says free-form code-writing roots need frontier-level coding. For a 7B, replace the REPL with a **fixed action DSL** the harness parses: `PEEK a b` / `GREP <regex>` / `MAP <question>` / `FINAL <answer>`. Same peek/grep/partition/map power, zero codegen risk, trivially sandboxed (no `exec` needed at all).
2. **Chunking vs peek/grep:** do both, harness-side. Grep first (cheap, narrows haystack — the paper shows retrieval-type tasks need no recursion at all); chunk+map only when the query is aggregative ("summarize", "how many", "across the whole log"). Chunk on structure: JSONL → N lines/chunk; logs → time/marker blocks; code → per-file/per-def. Chunk size = worker context minus overhead: with ollama set `num_ctx` 16384–32768 (ollama default 4–8K silently truncates — the classic gotcha) and feed ~8–12K-token chunks.
3. **When to recurse vs answer:** recurse (split chunk further) only when a chunk still exceeds the window; otherwise answer. **Depth limit 2–3 and a hard sub-call budget (e.g. 64)** — this is the anti-explosion gate the paper lacked and paid for.
4. **Termination:** require the exact `FINAL:` sentinel; on missing sentinel after k turns, force a "you must answer now" turn. Expect to enforce this — brittleness is a reported failure mode.
5. **Aggregation = one reduce call** over the concatenated map outputs (recursively reduced if the concat itself is too big — same loop, so it's free).

### Skeleton (stdlib only: urllib.request + json + re)

```python
import json, re, urllib.request

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:7b"
NUM_CTX = 16384
CHUNK_CHARS = 24000        # ~8K tokens; safe inside NUM_CTX with prompt overhead
MAX_DEPTH, BUDGET = 3, 64  # hard gates the paper lacked
calls = 0

def llm(system, user):
    global calls; calls += 1; assert calls <= BUDGET, "sub-call budget exhausted"
    body = json.dumps({"model": MODEL, "stream": False,
        "options": {"num_ctx": NUM_CTX, "temperature": 0},
        "messages": [{"role":"system","content":system},{"role":"user","content":user}]}).encode()
    req = urllib.request.Request(OLLAMA, body, {"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=600).read())["message"]["content"]

def chunks(text, size=CHUNK_CHARS):     # newline-aligned uniform chunking
    out, i = [], 0
    while i < len(text):
        j = text.rfind("\n", i, i + size); j = i + size if j <= i else j
        out.append(text[i:j]); i = j
    return out

def rlm(query, context, depth=0):
    if len(context) <= CHUNK_CHARS:     # fits: answer directly (base case)
        return llm("Answer from the provided text only. Say NOTHING_RELEVANT if absent.",
                   f"TEXT:\n{context}\n\nQUESTION: {query}")
    # grep phase: ask model for a filter regex (one cheap call), fall back to no filter
    if depth == 0:
        pat = llm("Output ONLY a Python regex that lines relevant to the question would match, or ALL.",
                  f"Question: {query}\nSample:\n{context[:2000]}").strip()
        if pat != "ALL":
            try:
                hits = "\n".join(l for l in context.splitlines() if re.search(pat, l))
                if 0 < len(hits) <= len(context) // 3: context = hits
            except re.error: pass
    if len(context) <= CHUNK_CHARS or depth >= MAX_DEPTH:
        return rlm(query, context[:CHUNK_CHARS], MAX_DEPTH)   # truncate at depth wall
    maps = [rlm(query, c, depth + 1) for c in chunks(context)]        # map (recurse)
    merged = "\n---\n".join(m for m in maps if "NOTHING_RELEVANT" not in m)
    return rlm(f"Combine these partial answers into one final answer to: {query}",
               merged, depth + 1)                                      # reduce (recurse)
```

That is the whole thing: ~50 lines, stdlib-only, and it keeps the paper's three load-bearing properties — context never enters a single window whole, grep-before-chunk, recursion only when a piece still doesn't fit — while adding the two guards the paper says it needed (call budget, depth wall). Upgrade path if the root proves capable: swap the fixed loop for the true REPL (`exec` with `context` + `llm_query` in scope, `FINAL()` sentinel), which is exactly rlm-minimal's shape; ollama's OpenAI-compatible endpoint (`/v1/chat/completions`) also plugs straight into the official repo's OpenAI backend with a custom base_url.

## Sources

- https://arxiv.org/abs/2512.24601 · https://arxiv.org/html/2512.24601v1
- https://alexzhang13.github.io/blog/2025/rlm/
- https://github.com/alexzhang13/rlm · https://github.com/alexzhang13/rlm-minimal
- https://github.com/fullstackwebdev/rlm_repl
- https://huggingface.co/papers/2512.24601
- https://x.com/lateinteraction/status/2007212972721275281
- (Disambiguation) https://arxiv.org/abs/2510.04871 = "Less is More: Recursive Reasoning with Tiny Networks" — unrelated.
