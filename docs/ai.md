# LLM Sentiment Judge

`filtered_articles.json` should only contain DJT-related coverage that reads as *negative/critical*, per the PRD (`backlog/docs/doc-001*`). Lexicon-based sentiment scorers (VADER, TextBlob) were considered and rejected: they score surface-level word polarity, not political framing, so headlines like *"Trump Pulled In About $1.4 Billion From Crypto Ventures"* read as neutral to a lexicon even though the coverage is clearly critical. Instead, `utils/sentiment.py` sends one batched request per pipeline run to an LLM and asks it to judge whether the coverage is favorable or unfavorable to DJT.

## How it works

1. After DJT-relevance filtering (`utils/filter.py`), `main.py` sends all DJT-related articles for that run to `utils/sentiment.score_articles()` in a single request.
2. The model returns a JSON array of `{"index": ..., "sentiment_score": ...}` (`-1.0` very unfavorable/critical .. `1.0` very favorable) for every article.
3. Articles with `sentiment_score <= SENTIMENT_MAX_SCORE` are kept; the rest are dropped.
4. If the request fails for any reason (missing/invalid key, network error, timeout, unparseable response), `main.py` logs the failure via eliot and **skips rewriting `filtered_articles.json` for that run** — the site keeps serving the previous run's output rather than going blank or showing unfiltered content.

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

## Testing

`tests/test_sentiment.py` mocks `requests.post` — no real network calls or credentials are needed to run the test suite. `tests/test_main.py::TestMainSentimentGate` covers the threshold boundary and the judge-failure fallback path end-to-end.
