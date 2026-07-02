#!/usr/bin/env python

import json
import pytest
import requests
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sentiment import SentimentJudgeError, score_articles


def _chat_completion_response(payload):
    """Build a mock requests.Response returning the given payload as the model's message content."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'choices': [
            {'message': {'content': json.dumps(payload)}},
        ]
    }
    return response


@pytest.fixture
def sample_articles():
    """Fixture providing one clearly negative and one clearly positive article."""
    return [
        {
            'title': 'Trump Pulled In About $1.4 Billion From Crypto Ventures',
            'description': 'Financial disclosure shows the president profiting heavily while in office.',
        },
        {
            'title': 'Trump Signs Bipartisan Bill to Widespread Praise',
            'description': 'Lawmakers from both parties celebrate a rare moment of unity.',
        },
    ]


class TestScoreArticles:
    """Test cases for score_articles()."""

    @patch('utils.sentiment.requests.post')
    def test_known_negative_sample_scores_negative(self, mock_post, sample_articles):
        """A critical/negative article should receive a score <= 0."""
        mock_post.return_value = _chat_completion_response(
            [
                {'index': 0, 'sentiment_score': -0.8},
                {'index': 1, 'sentiment_score': 0.6},
            ]
        )

        scores = score_articles(sample_articles)

        assert scores[0] <= 0, "Negative-framed article should score at or below zero"

    @patch('utils.sentiment.requests.post')
    def test_known_positive_sample_scores_positive(self, mock_post, sample_articles):
        """A favorable article should receive a score > 0."""
        mock_post.return_value = _chat_completion_response(
            [
                {'index': 0, 'sentiment_score': -0.8},
                {'index': 1, 'sentiment_score': 0.6},
            ]
        )

        scores = score_articles(sample_articles)

        assert scores[1] > 0, "Favorable article should score above zero"

    @patch('utils.sentiment.requests.post')
    def test_response_wrapped_in_markdown_fence_is_parsed(self, mock_post, sample_articles):
        """Some models wrap JSON output in ```json fences; this should still parse."""
        payload = json.dumps([{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.3}])
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'choices': [{'message': {'content': f'```json\n{payload}\n```'}}]}
        mock_post.return_value = response

        scores = score_articles(sample_articles)

        assert scores[0] == -0.5
        assert scores[1] == 0.3

    @patch('utils.sentiment.requests.post')
    def test_non_200_status_raises_sentiment_judge_error(self, mock_post, sample_articles):
        """A non-200 HTTP status should raise SentimentJudgeError, not propagate raw HTTP errors."""
        response = Mock()
        response.status_code = 500
        response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = response

        with pytest.raises(SentimentJudgeError):
            score_articles(sample_articles)

    @patch('utils.sentiment.requests.post')
    def test_network_error_raises_sentiment_judge_error(self, mock_post, sample_articles):
        """A connection failure should raise SentimentJudgeError."""
        mock_post.side_effect = requests.ConnectionError("connection refused")

        with pytest.raises(SentimentJudgeError):
            score_articles(sample_articles)

    @patch('utils.sentiment.requests.post')
    def test_malformed_json_raises_sentiment_judge_error(self, mock_post, sample_articles):
        """Unparseable model output should raise SentimentJudgeError."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {'choices': [{'message': {'content': 'not valid json at all'}}]}
        mock_post.return_value = response

        with pytest.raises(SentimentJudgeError):
            score_articles(sample_articles)

    @patch('utils.sentiment.requests.post')
    def test_incomplete_coverage_raises_sentiment_judge_error(self, mock_post, sample_articles):
        """A response that omits scores for some input articles should raise SentimentJudgeError."""
        mock_post.return_value = _chat_completion_response([{'index': 0, 'sentiment_score': -0.5}])

        with pytest.raises(SentimentJudgeError):
            score_articles(sample_articles)

    def test_empty_article_list_returns_empty_scores_without_network_call(self):
        """No articles means no judge call is needed."""
        with patch('utils.sentiment.requests.post') as mock_post:
            scores = score_articles([])

            assert scores == {}
            mock_post.assert_not_called()


class TestScoreArticlesTargetOverrides:
    """Test cases for the optional target-override params (used by cli.py to hit a local judge)."""

    @patch('utils.sentiment.requests.post')
    def test_default_call_omits_temperature_and_uses_config_target(self, mock_post, sample_articles):
        """No overrides: request goes to the configured URL/model/key and has no 'temperature' key."""
        mock_post.return_value = _chat_completion_response(
            [{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.5}]
        )

        score_articles(sample_articles)

        _, kwargs = mock_post.call_args
        assert 'temperature' not in kwargs['json'], "temperature must be omitted to preserve existing Fireworks payload"

    @patch('utils.sentiment.requests.post')
    def test_overrides_reach_the_request(self, mock_post, sample_articles):
        """base_url/model/api_key/timeout overrides should be used instead of the config globals."""
        mock_post.return_value = _chat_completion_response(
            [{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.5}]
        )

        score_articles(
            sample_articles,
            base_url='http://localhost:8000/v1',
            model='gpt-oss-20b-OptiQ-4bit',
            api_key='omgitsomlx',
            timeout=60,
        )

        args, kwargs = mock_post.call_args
        assert args[0] == 'http://localhost:8000/v1/chat/completions'
        assert kwargs['json']['model'] == 'gpt-oss-20b-OptiQ-4bit'
        assert kwargs['headers']['Authorization'] == 'Bearer omgitsomlx'
        assert kwargs['timeout'] == 60

    @patch('utils.sentiment.requests.post')
    def test_temperature_included_when_given(self, mock_post, sample_articles):
        """Passing temperature should add it to the payload for deterministic local scoring."""
        mock_post.return_value = _chat_completion_response(
            [{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.5}]
        )

        score_articles(sample_articles, temperature=0)

        _, kwargs = mock_post.call_args
        assert kwargs['json']['temperature'] == 0

    @patch('utils.sentiment.requests.post')
    def test_extra_body_is_merged_into_payload(self, mock_post, sample_articles):
        """extra_body lets callers pass provider-specific hints without touching the default payload shape."""
        mock_post.return_value = _chat_completion_response(
            [{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.5}]
        )

        score_articles(sample_articles, extra_body={'chat_template_kwargs': {'enable_thinking': False}})

        _, kwargs = mock_post.call_args
        assert kwargs['json']['chat_template_kwargs'] == {'enable_thinking': False}


class TestScoreArticlesReasoningModelFallbacks:
    """Test cases for hardening against reasoning models (e.g. gpt-oss via oMLX) that may
    leave 'content' empty or wrap the JSON array in surrounding prose."""

    @patch('utils.sentiment.requests.post')
    def test_falls_back_to_reasoning_content_when_content_is_empty(self, mock_post, sample_articles):
        """Some local reasoning models emit the answer into reasoning_content and leave content blank."""
        payload = json.dumps([{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.5}])
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            'choices': [{'message': {'content': '', 'reasoning_content': payload}}],
        }
        mock_post.return_value = response

        scores = score_articles(sample_articles)

        assert scores == {0: -0.5, 1: 0.5}

    @patch('utils.sentiment.requests.post')
    def test_json_array_embedded_in_surrounding_prose_is_extracted(self, mock_post, sample_articles):
        """A model that answers with prose plus a trailing JSON array should still be parsed."""
        payload = json.dumps([{'index': 0, 'sentiment_score': -0.5}, {'index': 1, 'sentiment_score': 0.5}])
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            'choices': [{'message': {'content': f'Here is my analysis:\n{payload}\nHope that helps!'}}],
        }
        mock_post.return_value = response

        scores = score_articles(sample_articles)

        assert scores == {0: -0.5, 1: 0.5}
