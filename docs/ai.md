# LLM Sentiment Judge

The filtered articles store (`filtered_articles.duckdb`, exported to `filtered_articles.parquet`) should only contain DJT-related coverage that reads as *negative/critical*, per the PRD (`backlog/docs/doc-001*`). Lexicon-based sentiment scorers (VADER, TextBlob) were considered and rejected: they score surface-level word polarity, not political framing, so headlines like *"Trump Pulled In About $1.4 Billion From Crypto Ventures"* read as neutral to a lexicon even though the coverage is clearly critical. Instead, `utils/sentiment.py` sends one batched request per pipeline run to an LLM and asks it to judge whether the coverage is favorable or unfavorable to DJT.

## How it works

1. After DJT-relevance filtering (`utils/filter.py`), `main.py` sends all DJT-related articles for that run to `utils/sentiment.score_articles()` in a single request.
2. The model returns a JSON array of `{"index": ..., "sentiment_score": ...}` (`-1.0` very unfavorable/critical .. `1.0` very favorable) for every article.
3. Articles with `sentiment_score <= SENTIMENT_MAX_SCORE` are kept; the rest are dropped.
4. If the request fails for any reason (missing/invalid key, network error, timeout, unparseable response), `main.py` logs the failure via eliot and **skips rewriting the filtered articles store for that run** — the site keeps serving the previous run's output rather than going blank or showing unfiltered content.

## Configuration

The judge is called against any OpenAI-compatible `/chat/completions` endpoint — not tied to a specific provider, so switching later (Together, a local vLLM/Ollama server, etc.) is a config-only change.

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_API_KEY` | *(empty)* | Bearer token sent as `Authorization: Bearer <key>`. |
| `LLM_BASE_URL` | `https://api.fireworks.ai/inference/v1` | Base URL; `/chat/completions` is appended. |
| `LLM_MODEL` | `accounts/fireworks/models/gpt-oss-20b` | Model name passed in the request body. |
| `SENTIMENT_ENABLED` | `True` | Set to `False` to skip the judge entirely and write all DJT-related articles (no negative-only gate) — an explicit opt-out, not a failure path. |
| `SENTIMENT_MAX_SCORE` | `0.0` | Inclusive upper bound; articles scoring at or below this threshold are kept. |

See `.env.example` for copy-paste defaults.

### Swapping providers

Any provider exposing an OpenAI-compatible chat completions API works — set:

```dotenv
# Together
LLM_BASE_URL=https://api.together.xyz/v1
LLM_MODEL=<together-model-id>

# Local vLLM / Ollama (OpenAI-compatible mode)
LLM_BASE_URL=http://localhost:PORT/v1
LLM_MODEL=<local-model-id>
```

`LLM_API_KEY` can be left empty for local servers that don't require auth.

### `cli.py`

For exploring the article store and benchmarking a candidate judge (e.g. a local oMLX model)
against the configured production judge before switching, without touching `LLM_*`/`.env`:

```bash
uv run ./cli.py health --target local     # smoke-test the local server + model
uv run ./cli.py fetch --hours 8            # populate the store (mirrors main.py, no sentiment gate)
uv run ./cli.py articles --hours 8 --djt-only
uv run ./cli.py judge --target local --hours 8
uv run ./cli.py compare --hours 8          # local vs remote side by side: deltas + keep/drop agreement
uv run ./cli.py judge --target remote --model accounts/fireworks/models/minimax-m3 --hours 8
# `--model` (health/judge only) overrides the resolved target's model, e.g. to
# benchmark a new hosted candidate without touching LLM_MODEL/.env
```

The `local` target reads `LOCAL_LLM_BASE_URL`/`LOCAL_LLM_MODEL`/`LOCAL_LLM_API_KEY` from `config.py`,
defaulting to `OMLX_BASE_URL`/`OMLX_API_KEY` (see `~/git/pi_config/docs/omlx-agentic-coding.md` for
oMLX server setup) and `gpt-oss-20b-OptiQ-4bit`. The `remote` target reuses the existing `LLM_*` config.

### Benchmark results

Candidates evaluated so far via `cli.py health`/`judge`/`compare` against the same real
DJT article set (see task-012 for full detail):

| Candidate | Latency (smoke test) | Notable result |
| --- | --- | --- |
| `gpt-oss-20b-OptiQ-4bit` (local oMLX) | ~3.2s | 84% keep/drop agreement with Fireworks gpt-oss-20b; both misjudge lexically-neutral-but-critical framing (e.g. crypto windfall headlines) as favorable |
| `accounts/fireworks/models/gpt-oss-20b` (Fireworks, default) | ~6.9s | Baseline production judge; same framing blind spot as the local variant |
| `accounts/fireworks/models/minimax-m3` (Fireworks) | ~1.5s | Correctly scored "Crypto Brought Trump a Huge Windfall..." as critical (-0.80) — the exact case gpt-oss got backwards on both targets |

`--model` (see `cli.py` usage above) is how a candidate like `minimax-m3` is pointed at
without touching `LLM_MODEL`/`.env`.

## Testing

`tests/test_sentiment.py` mocks `requests.post` — no real network calls or credentials are needed to run the test suite. `tests/test_main.py::TestMainSentimentGate` covers the threshold boundary and the judge-failure fallback path end-to-end.
