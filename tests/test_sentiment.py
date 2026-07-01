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
