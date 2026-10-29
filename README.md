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
python ax8pptx/verify.py ax8pptx/out/<file>.pptx     # OOXML integrity + shape graph
python -m ax8pptx.test_pipeline                       # end-to-end pipeline test
python -c "from ax8pptx.regress import compare; print(compare('path.pptx'))"
```

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
