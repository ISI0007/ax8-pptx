# AX8 PPTX

An agentic presentation engine. Brief in, validated and rendered deck out.

The model never draws. It fills content slots in a schema the renderer owns, so
type scale, margins, colour and chart geometry stay consistent across every
slide — and a revision is a data edit, not a whole-deck reroll.

## Why it is built this way

| Failure mode of prompt-to-slide tools | What AX8 does instead |
|---|---|
| Text overflows its box | `fit.py` measures rendered height and shrinks or splits |
| Margins and type drift per slide | `tokens.py` owns every size and colour |
| Charts are pasted images | native `pptx` chart objects |
| Revision regenerates everything | slides are structured objects, regenerate one |
| Well-executed wrong deck | clarification card sets intent before generation |

## Install

```bash
pip install -r requirements.txt
```

Python 3.10+. No Office install required to build decks.

## Use

```bash
# offline fixture, always renderable, no API key
python -m ax8pptx.cli "Agentic presentation engines" --goal persuade --slides 10 --offline

# live generation
export DEEPSEEK_API_KEY=...        # PowerShell: $env:DEEPSEEK_API_KEY="..."
python -m ax8pptx.cli "AI agents in 2026" --audience "CTO" --goal report --slides 12

# with research crawl filling real citations
python -m ax8pptx.cli "topic" --research --seeds "https://a.com,https://b.com"
```

Output lands in `ax8pptx/out/`.

## Providers

One OpenAI-compatible client covers every endpoint below. Select with
`--provider <id>`, the `AX8_PROVIDER` env var, or let AX8 auto-pick the first
provider whose key is present (paid first, then local).

```bash
python AX8.py --list-providers     # tier, key status, readiness
python AX8.py --probe              # live reachability, no tokens spent
python AX8.py "topic" --provider groq --model llama-3.3-70b-versatile
```

| ID | Tier | Default model | Key env |
|---|---|---|---|
| `ollama` | free (local) | qwen2.5:14b | none |
| `lmstudio` | free (local) | local-model | none |
| `groq` | freemium | llama-3.3-70b-versatile | GROQ_API_KEY |
| `google` | freemium | gemini-2.5-flash | GOOGLE_API_KEY |
| `openrouter` | freemium | deepseek-chat-v3 | OPENROUTER_API_KEY |
| `cerebras` | freemium | llama-3.3-70b | CEREBRAS_API_KEY |
| `mistral` | freemium | mistral-large-latest | MISTRAL_API_KEY |
| `together` | freemium | Llama-3.3-70B-Turbo | TOGETHER_API_KEY |
| `zhipu` | freemium | glm-4.5 | ZHIPU_API_KEY |
| `qwen` | freemium | qwen-plus | DASHSCOPE_API_KEY |
| `deepseek` | paid | deepseek-chat | DEEPSEEK_API_KEY |
| `openai` | paid | gpt-4o-mini | OPENAI_API_KEY |
| `anthropic` | paid | claude-sonnet-4 | ANTHROPIC_API_KEY |
| `xai` | paid | grok-4 | XAI_API_KEY |
| `moonshot` | paid | kimi-k2 | MOONSHOT_API_KEY |

Any other endpoint: `--provider custom` with `AX8_ENDPOINT`, `AX8_MODEL`,
and optionally `AX8_API_KEY`.

Adding a provider is one dict entry in `providers.py`. Every entry is exercised
by `test_llm_wire.py` against a local stub server, so a typo in an endpoint or
model name fails in CI rather than in front of a user.

## Pipeline

```
brief (clarification card: topic, audience, goal, slide count, must-include)
  -> arc        deterministic layout sequence, sized to the slide budget
  -> research   optional crawl, ranked sources, citation block
  -> compose    LLM fills the JSON contract (or offline fixture)
  -> gates      brief valid + slide count matches + per-slide schema valid
  -> art        deterministic generated cover panel
  -> render     design tokens + layout registry -> native .pptx
  -> regress    structural fingerprint, drift detection
```

## Modules

| Module | Role |
|---|---|
| `tokens.py` | design tokens: 3 themes, type scale, grid |
| `spec.py` | slide schema, 9 layouts, validation |
| `intake.py` | clarification card, deterministic slide arc |
| `pipeline.py` | LLM prompt contract, JSON to Deck, gates |
| `fit.py` | text-fit measurement, shrink and split |
| `render.py` | layout registry, native charts and tables |
| `llm.py` | live DeepSeek call, key from env only |
| `research.py` | citation crawl and ranking |
| `images.py` | deterministic cover art, optional remote backend |
| `regress.py` | visual regression, structural fallback |
| `cli.py` | one command, topic to deck |

## Layouts

cover, section, bullets, two_col, kpi_row, chart, quote, table, closing.

## Themes

`midnight`, `paper`, `sand`.

## Verification

```bash
python ax8pptx/verify.py ax8pptx/out/<file>.pptx   # OOXML integrity + shape graph
python -m ax8pptx.test_pipeline                     # end-to-end pipeline test
python -m ax8pptx.test_llm_wire                     # LLM wire format against a local stub
python ax8pptx/scan_secrets.py                      # pre-commit secret scan
python -c "from ax8pptx.regress import compare; print(compare('path.pptx'))"
```

`test_llm_wire` stands up a local HTTP server speaking the chat-completions
wire format and drives the real `llm.complete()` code path through it, so the
request shape, auth header, JSON extraction and gates are all exercised without
an API key. It is not a substitute for a live call.

## Known limits

- **Pixel-diff regression needs a renderer.** `regress.py` uses LibreOffice
  headless when present, otherwise falls back to a structural snapshot. Install
  LibreOffice for true visual diffs.
- **SERP scraping is best-effort.** Pass `--seeds` for reliable citations.
- **Remote image backend needs an image API key.** The local generator is the
  default and needs nothing.
- **Live LLM path is wired but has not been exercised against the API** in this
  repo's test run; offline mode is what CI would use.

## Secrets

Nothing is stored in the repo. Keys are read from the environment at call time:
`DEEPSEEK_API_KEY`, optionally `OPENAI_API_KEY`. See `.env.example`.

## License

MIT
