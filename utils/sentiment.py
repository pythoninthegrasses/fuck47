#!/usr/bin/env python

"""
LLM-based sentiment judge for DJT-related articles.

Rather than a lexicon-based scorer (VADER/TextBlob), this module sends a single
batched request to an OpenAI-compatible chat completions endpoint (default:
Fireworks) asking the model to judge whether coverage of DJT is favorable or
critical. Lexicon scorers miss critical *framing* that uses no negative words
(e.g. "Trump Pulled In $1.4 Billion From Crypto Ventures" reads neutral to a
lexicon but is critical coverage in context).
"""

import json
import re
import requests
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from eliot import start_action

REQUEST_TIMEOUT = 30

SYSTEM_PROMPT = (
    "You are a sentiment judge for news coverage of Donald Trump (DJT). "
    "For each article, decide whether the coverage is favorable or unfavorable to DJT, "
    "not whether the language itself contains positive/negative words. "
    "Respond with a JSON array only, no prose, one object per article: "
    '{"index": <int>, "sentiment_score": <float from -1.0 (very unfavorable/critical) '
    'to 1.0 (very favorable)>}.'
)

_CODE_FENCE_RE = re.compile(r'^```(?:json)?\s*|\s*```$', re.MULTILINE)
_JSON_ARRAY_RE = re.compile(r'\[.*\]', re.DOTALL)


class SentimentJudgeError(Exception):
    """Raised when the sentiment judge call fails or returns unusable output."""


def _build_prompt(articles: list[dict]) -> str:
    lines = []
    for i, article in enumerate(articles):
        title = article.get('title', '') or ''
        description = article.get('description', '') or ''
        lines.append(f"{i}. Title: {title}\n   Description: {description}")
    return "Score the following articles:\n\n" + "\n".join(lines)


def _parse_response(raw_content: str, expected_count: int) -> dict[int, float]:
    cleaned = _CODE_FENCE_RE.sub('', raw_content).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError, TypeError:
        # Some models (e.g. reasoning models via a local server) wrap the JSON array in
        # surrounding prose despite the system prompt asking for JSON only. Retry once
        # against the outermost [...] substring before giving up.
        match = _JSON_ARRAY_RE.search(cleaned)
        if match is None:
            raise SentimentJudgeError(f"Could not parse judge response as JSON: {cleaned!r}") from None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise SentimentJudgeError(f"Could not parse judge response as JSON: {e}") from e

    if not isinstance(parsed, list):
        raise SentimentJudgeError(f"Judge response was not a JSON array: {parsed!r}")

    scores: dict[int, float] = {}
    for entry in parsed:
        try:
            index = int(entry['index'])
            score = float(entry['sentiment_score'])
        except (KeyError, TypeError, ValueError) as e:
            raise SentimentJudgeError(f"Malformed entry in judge response: {entry!r} ({e})") from e
        scores[index] = score

    missing = set(range(expected_count)) - scores.keys()
    if missing:
        raise SentimentJudgeError(f"Judge response is missing scores for article indices: {sorted(missing)}")

    return scores


def score_articles(
    articles: list[dict],
    *,
    base_url: str = None,
    model: str = None,
    api_key: str = None,
    temperature: float = None,
    extra_body: dict = None,
    timeout: float = None,
) -> dict[int, float]:
    """
    Score each article's sentiment toward DJT via a single batched LLM call.

    Args:
        articles: List of article dictionaries (uses 'title' and 'description').
        base_url: Override for LLM_BASE_URL (e.g. to hit a local OpenAI-compatible server).
        model: Override for LLM_MODEL.
        api_key: Override for LLM_API_KEY.
        temperature: If given, included in the request payload. Omitted by default so the
            request sent to the configured provider (Fireworks) is unchanged.
        extra_body: Extra fields merged into the request JSON (e.g. provider-specific
            chat_template_kwargs). Ignored by providers that don't recognize them.
        timeout: Override for REQUEST_TIMEOUT, in seconds.

    Returns:
        Mapping of list-index -> sentiment_score (-1.0 very unfavorable .. 1.0 very favorable).

    Raises:
        SentimentJudgeError: on any network, HTTP, or response-parsing failure.
    """
    if not articles:
        return {}

    base_url = base_url or LLM_BASE_URL
    model = model or LLM_MODEL
    api_key = api_key or LLM_API_KEY
    timeout = timeout if timeout is not None else REQUEST_TIMEOUT

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': _build_prompt(articles)},
        ],
    }
    if temperature is not None:
        payload['temperature'] = temperature
    if extra_body:
        payload.update(extra_body)

    with start_action(action_type="sentiment_judge", article_count=len(articles)) as action:
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    'Authorization': f"Bearer {api_key}",
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            action.log(message_type="sentiment_judge:request_failed", error=str(e))
            raise SentimentJudgeError(f"Sentiment judge request failed: {e}") from e

        try:
            message = response.json()['choices'][0]['message']
            content = message['content']
        except (KeyError, IndexError, TypeError, ValueError) as e:
            action.log(message_type="sentiment_judge:unexpected_response_shape", error=str(e))
            raise SentimentJudgeError(f"Unexpected judge response shape: {e}") from e

        if not content or not content.strip():
            # Reasoning models served via a local bridge (e.g. oMLX) may leave 'content'
            # empty and put the answer in 'reasoning_content' instead.
            content = message.get('reasoning_content') or content

        try:
            scores = _parse_response(content, len(articles))
        except SentimentJudgeError as e:
            action.log(message_type="sentiment_judge:parse_failed", error=str(e))
            raise

        return scores
