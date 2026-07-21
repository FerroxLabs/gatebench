# MODELS — lane slugs, what they are, and what reproduces

Lane slugs in `results/` are the **routing aliases used at measurement time** (2026-07-21).
Three transports appear in the `via` column:

- **openrouter** — public OpenRouter slugs, billed at real retail. **Third-party reproducible**
  today with `runners/run_bench.py` (subject to normal provider model-version drift).
- **flux** — a private metered router using pinned model aliases (`flux-pinned-*`). The
  underlying model families are public; you can re-run them through any provider, but the exact
  pinned snapshots and flat-rate billing are not re-runnable from this repo. **Static evidence
  here; family-level reproducible elsewhere.**
- **system** — third-party fusion/agent products invoked as systems at measurement time.
  **Static evidence.**

| lane slug | what it is | via (alias at measurement) | reproducible? |
|---|---|---|---|
| `anvil-v2` | **Gate-first executor — the product under test.** Cheap-model pool (first probe: MiniMax M3) climbing a machine gate under a non-regressive rule. Implementation not in this repo. | flux (pool of pinned cheap models) | **Static evidence** — audit via `verify/verify_results.py`, climb traces in `results-full.json` |
| `minimax-solo` | MiniMax M3, ungated one-shot — the executor's own first-probe model, run bare (the ±gate control) | flux (`flux-pinned-minimax-m3`) | family-level (MiniMax M3 is public) |
| `deepseek-v4-pro` | DeepSeek V4 Pro | openrouter `deepseek/deepseek-v4-pro` | **yes — run_bench.py** |
| `gemini-3-1-pro` | Google Gemini 3.1 Pro (preview) | openrouter `google/gemini-3.1-pro-preview` | **yes — run_bench.py** |
| `claude-sonnet-5` | Anthropic Claude Sonnet 5 | openrouter `anthropic/claude-sonnet-5` | **yes — run_bench.py** |
| `kimi-k3` | Moonshot Kimi K3 | openrouter `moonshotai/kimi-k3` | **yes — run_bench.py** |
| `glm-5-2` | Zhipu GLM 5.2 | openrouter `z-ai/glm-5.2` | **yes — run_bench.py** |
| `opus-4-8` | Anthropic Claude Opus 4.8 | flux (`flux-pinned-claude-opus-4-8`) | family-level |
| `gpt-5-6-sol` / `gpt-5-6-terra` / `gpt-5-6-luna` | OpenAI GPT-5.6 tier variants (large → small) | flux (`flux-pinned-gpt-5-6-*`) | family-level |
| `grok-4-5` | xAI Grok 4.5 | flux (`flux-pinned-grok-4-5`) | family-level |
| `claude-haiku` | Anthropic Claude Haiku | flux (`flux-pinned-claude-haiku`) | family-level |
| `fable-5` | Anthropic Claude Fable 5 — **flagged**: router content-filter bug returned silent-empty 200s; 0 score is a router fault, not capability | flux (`flux-pinned-claude-fable-5`) | family-level |
| `fable-5-bare` | The same model retried bare-prompt via OpenRouter (partial recovery; most cells still content-filtered) | openrouter | yes (as a retry protocol) |
| `mistral-large` | Mistral Large | flux (`flux-pinned-mistral-large`) | family-level |
| `qwen-plus` | Alibaba Qwen Plus | flux (`flux-pinned-qwen-plus`) | family-level |
| `fugu` | Sakana "Fugu" fusion system (multi-model fusion product) | system | static evidence |
| `fugu-ultra` | Sakana Fugu, deep/ultra mode | system | static evidence |
| `openrouter-fusion` | Mixture-of-agents panel + judge fusion product | system | static evidence |
| `hermes` | MoA agent product — **flagged**: empty/timeout on every task this run; reliability observation, not a score | system | static evidence |
| `anvil-v3` / `anvil-ultra` | Post-hoc partial probes of newer executor variants (2/5 and 1/5 cells; not part of the published 20-lane table) | flux | static evidence |

Notes:

- Lane slugs are routing aliases, not marketing names; where a public model family is named
  above, that is the family the alias was pinned to at measurement time. Provider-side model
  updates mean an external re-run is a *family-level* replication, not a bit-exact one.
- The five OpenRouter lanes were deliberately measured at retail so that any third party can
  reproduce both the scores and the costs with nothing but an `OPENROUTER_API_KEY`.
- The judge panel for axis 3 drew from the opus-4.8 / gpt-5.6-luna / grok-4.5 aliases; per-judge
  scores and panel membership are recorded inside every result record (`judge.panel`).
