---
id: TASK-012
title: Benchmark local LLM judge against Fireworks-hosted sentiment judge
status: In Progress
assignee: []
created_date: '2026-07-01 22:42'
updated_date: '2026-07-02 03:03'
labels: []
dependencies: []
references:
  - docs/ai.md
  - utils/sentiment.py
  - cli.py
  - ~/git/pi_config/docs/omlx-agentic-coding.md
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Evaluate running the LLM sentiment judge (`utils/sentiment.py`) against a local oMLX server instead of (or as a fallback to) the hosted Fireworks endpoint, and build reusable tooling to explore the article store and compare judge targets. Local target: `gpt-oss-20b-OptiQ-4bit` served by oMLX per `~/git/pi_config/docs/omlx-agentic-coding.md`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 score_articles() accepts optional per-call overrides (base_url/model/api_key/temperature/extra_body/timeout) without changing the default request sent to the configured provider (Fireworks)
- [x] #2 score_articles() tolerates reasoning models that leave 'content' empty (falls back to reasoning_content) or wrap the JSON array in surrounding prose
- [x] #3 A local-target config (LOCAL_LLM_BASE_URL/LOCAL_LLM_MODEL/LOCAL_LLM_API_KEY) is added, defaulting to the existing OMLX_BASE_URL/OMLX_API_KEY vars
- [x] #4 A cli.py at the repo root (uv run ./cli.py <cmd>) supports: health (smoke-test + model-loaded check), fetch (populate the store), articles (list/filter by recency and DJT-relevance), judge (score against one target), and compare (score against both targets side by side with delta + keep/drop agreement stats)
- [x] #5 All new/changed code has passing tests written test-first (TDD) and the full suite stays green
- [x] #6 docs/ai.md documents the local target and the CLI usage
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented in this session:

- `utils/sentiment.py`: `score_articles()` now takes optional keyword-only `base_url`, `model`, `api_key`, `temperature`, `extra_body`, `timeout`. All default to the existing config globals/`REQUEST_TIMEOUT` so the Fireworks request is byte-for-byte unchanged when called with no overrides (verified: `temperature` is only added to the payload when explicitly passed). Parsing hardened: falls back to `message['reasoning_content']` when `content` is empty/whitespace, and retries by regex-extracting the outermost `[...]` substring when `json.loads` fails on the raw content (handles reasoning models that answer with prose + trailing JSON).
- `config.py`: added `LOCAL_LLM_BASE_URL` (defaults to `f\"{OMLX_BASE_URL}/v1\"`), `LOCAL_LLM_MODEL` (default `gpt-oss-20b-OptiQ-4bit`), `LOCAL_LLM_API_KEY` (defaults to `OMLX_API_KEY`).
- New `cli.py` at repo root (moved there from `utils/cli.py` per request, executable, invoked as `uv run ./cli.py <cmd>`):
  - `health --target {local,remote}` — for `local`, GETs `{base_url}/models/status` to confirm the model is loaded, then runs a 2-article smoke test through `score_articles`.
  - `fetch --hours N` — mirrors `main.py`'s fetch step (prune + NewsAPI + RSS) without the sentiment gate, for populating a store to explore.
  - `articles --hours N [--djt-only] [--limit N]` — lists articles from the store filtered by `published_at` recency (reusing the same string-cutoff approach as `ArticleDB.clear_old_articles`) and optionally DJT-relevance.
  - `judge --target {local,remote} --hours N [--limit N] [--timeout N]` — scores current DJT-related articles against one target, prints keep/drop per the `SENTIMENT_MAX_SCORE` gate.
  - `compare --hours N [--limit N] [--timeout N]` — scores the same DJT set against both targets, reports per-article delta and keep/drop agreement, plus mean |delta| and disagreement count.
- Tests: extended `tests/test_sentiment.py` (+10 cases: overrides reach the request, temperature omitted by default, extra_body merge, reasoning_content fallback, embedded-JSON extraction) and new `tests/test_cli.py` (15 cases covering target resolution, recency/DJT filtering, judge/compare/health command behavior, all with `score_articles`/`requests.get` mocked — no network or credentials needed). Full suite: 127 passed. `ruff check`/`ruff format --check` clean.
- `docs/ai.md` and `.env.example` updated with the local-target config and CLI usage.

Live validation results (not covered by automated tests, informational):
- `uv run ./cli.py health --target local` — oMLX server reachable, `gpt-oss-20b-OptiQ-4bit` loaded, smoke test parsed in ~3.2s (faster than Fireworks' ~6.9s on the same smoke test).
- Real last-8h DJT article set (19 articles, fetched via `cli.py fetch --hours 8`): local scored all 19 in ~13s; Fireworks took ~67s and required raising the default request timeout well above the production judge's hardcoded 30s `REQUEST_TIMEOUT` (`utils/sentiment.py`) — flagged as a separate pre-existing production risk, not fixed here.
- `cli.py compare --hours 8`: 16/19 keep/drop agreement between local and remote (84%), mean |delta| = 0.174. Largest disagreement: "Crypto Brought Trump a Huge Windfall..." (local keep -0.70 vs remote drop +0.50).
- Notable quality signal: on "Trump Pulled In About $1.4 Billion From Crypto Ventures" — the exact headline `docs/ai.md` cites as the canonical example of critical-but-lexically-neutral coverage — both local (+0.60) and remote (+0.60) scored it favorable/drop, i.e. opposite of the intended judgment for that framing. Worth a closer look before treating either model as production-ready on this example class.

Follow-up noted but not started: explore other small local models as judge candidates (e.g. Gemma 4 variants — `gemma-4-31B-it` 8-bit and `gemma-4-26b-a4b-it` 4-bit are already profiled in `~/git/pi_config/docs/omlx-agentic-coding.md`) via the same `cli.py health`/`judge`/`compare` tooling, since gpt-oss-20b's local-vs-remote agreement on the "crypto windfall" framing case is not clearly better than Fireworks.

Ranked local judge candidates against Artificial Analysis' small open-source leaderboard (Intelligence Index v4.1, https://artificialanalysis.ai/models/open-source/small) on 2026-07-01. Gemma 4 ranks below Qwen3.6: Qwen3.6 27B (Intelligence 37, dense) and Qwen3.6 35B A3B (32, MoE / 3B active) are the top two small open models on the leaderboard; Gemma 4 31B (29) trails both, and the smaller Gemma 4 26B-A4B / E2B / E4B variants don't appear on the 4B-40B chart at all. On 64 GB unified RAM none are memory-bound (all fit at 8-bit): Qwen3.6 27B is the quality pick and Qwen3.6 35B A3B the speed/quality balance (3B active runs about as fast as a 3B dense model, 161 tok/s on cloud infra vs 35-57 tok/s for the dense options). All three are reasoning models, so the reasoning_content parsing fallback added in this task already covers them. Caveat: the Intelligence Index measures general capability (coding, science, agentic tool use), not sentiment-nuance on lexically-neutral-but-critical coverage — the task's actual failure mode — so `cli.py compare` remains the real arbiter before treating any of these as production-ready. Verify an MLX quant exists (e.g. under mlx-community/lmstudio-community) before downloading.

Added a candidate benchmarked against Fireworks directly (no local server needed): `accounts/fireworks/models/minimax-m3`, confirmed live on Fireworks as of 2026-06-12 (day-0 support), a reasoning model so the existing `reasoning_content`/embedded-JSON parsing fallbacks already cover it.

Tooling change: added a `--model` override flag to `cli.py`'s `health` and `judge` subcommands (test-first: 3 new cases in `tests/test_cli.py` confirmed red before implementation, all green after — full suite 130 passed). `compare` intentionally excludes `--model` since it contrasts the two *configured* targets, not a single overridden model. `docs/ai.md` updated with the flag and a `### Benchmark results` table summarizing all candidates evaluated so far.

Live results against `minimax-m3` via Fireworks (`--target remote --model accounts/fireworks/models/minimax-m3`):
- `health`: OK, parsed the 2-article smoke test in ~1.5s (vs ~6.9s for Fireworks gpt-oss-20b, ~3.2s for local gpt-oss-20b-OptiQ-4bit).
- `judge --hours 8` against 22 real DJT-related articles fetched fresh from NewsAPI/RSS: all scored cleanly, ~16 keep / 6 drop.
- Key result: on "Crypto Brought Trump a Huge Windfall, Even as Many Investors Lost Big" — the same framing-class headline both gpt-oss-local and gpt-oss-remote got backwards (scored it favorable/+0.60) — minimax-m3 correctly scored it -0.80 (critical/keep). This is the first candidate to get this specific test case right, suggesting it may handle lexically-neutral-but-critical framing better than gpt-oss-20b at either deployment target.

Caveat: single-run, single-example signal — not a statistically robust comparison. Worth a `compare`-style multi-run evaluation before treating minimax-m3 as a production swap candidate.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 ruff format --check --diff . passes with no changes needed
- [ ] #2 ruff check passes with no errors
- [ ] #3 pytest passes (all tests green)
- [ ] #4 New feature/bugfix developed test-first: failing test written before implementation
- [ ] #5 Relevant docs updated (README.md / AGENTS.md)
- [ ] #6 Committed as atomic conventional commit(s)
<!-- DOD:END -->
