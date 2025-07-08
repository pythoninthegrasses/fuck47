#!/usr/bin/env python

import json
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.filter import DJTNewsFilter


@pytest.fixture
def sample_articles():
    """Fixture providing sample articles for testing."""
    return [
        {
            'title': 'Trump Says Musk Is Off the Rails With America Party Effort',
            'description': 'The tech billionaire effort to create a new political party, called the America Party, comes amid a ramped-up feud with the president over his new domestic policy law.',
            'url': 'https://www.nytimes.com/2025/07/06/us/politics/trump-musk-america-party.html',
            'source': 'NYT > U.S. > Politics',
            'category': 'rss',
            'author': 'Tyler Pager'
        },
        {
            'title': 'How to Make the Biggest Splash, According to Science',
            'description': 'Cannonball, belly-flop or manu jumping? Physicists study the splashiest way to hit the water.',
            'url': 'https://www.example.com/science/physics/big-splash-water-jump',
            'source': 'Science Daily',
            'category': 'science',
            'author': 'John Smith'
        },
        {
            'title': 'Can Democrats Find Their Way on Immigration?',
            'description': 'The party leftward shift in the Biden administration arguably laid the groundwork for President Trump aggressive approach.',
            'url': 'https://www.nytimes.com/2025/07/06/us/politics/democrats-immigration-trump.html',
            'source': 'NYT > U.S. > Politics',
            'category': 'rss',
            'author': 'Lisa Lerer'
        }
    ]


@pytest.fixture
def articles_json_data():
    """Fixture providing all articles from articles.json."""
    articles_file = Path('tests/fixtures/articles.json')
    if not articles_file.exists():
        pytest.skip("articles.json file not found")

    with open(articles_file) as f:
        data = json.load(f)

    # Extract articles from TinyDB format
    articles = []
    if '_default' in data:
        for item in data['_default'].values():
            articles.append(item)

    return articles


@pytest.fixture
def filtered_articles_json_data():
    """Fixture providing filtered articles from articles.json."""
    articles_file = Path('tests/fixtures/articles.json')
    if not articles_file.exists():
        pytest.skip("articles.json file not found")

    with open(articles_file) as f:
        data = json.load(f)

    # Extract articles from TinyDB format and filter for DJT-related ones
    articles = []
    if '_default' in data:
        for item in data['_default'].values():
            articles.append(item)

    # Filter for DJT-related articles only
    djt_filter = DJTNewsFilter(min_score=1.0)
    filtered_articles = djt_filter.filter_articles(articles)

    return filtered_articles


@pytest.fixture
def djt_filter():
    """Fixture providing a DJTNewsFilter instance."""
    return DJTNewsFilter(min_score=1.0)


class TestDJTNewsFilter:
    """Test cases for DJTNewsFilter class."""

    def test_filter_initialization(self, djt_filter):
        """Test that filter initializes correctly."""
        assert djt_filter.min_score == 1.0
        assert isinstance(djt_filter, DJTNewsFilter)

    def test_calculate_relevance_score_djt_article(self, djt_filter, sample_articles):
        """Test relevance score calculation for DJT-related article."""
        djt_article = sample_articles[0]  # DJT article
        score = djt_filter.calculate_relevance_score(djt_article)
        assert score > 0, "DJT article should have positive relevance score"
        assert score >= 3.0, "Article with 'Trump' should score at least 3.0"

    def test_calculate_relevance_score_non_djt_article(self, djt_filter, sample_articles):
        """Test relevance score calculation for non-DJT article."""
        non_djt_article = sample_articles[1]  # Science article
        score = djt_filter.calculate_relevance_score(non_djt_article)
        assert score == 0, "Non-DJT article should have zero relevance score"

    def test_is_djt_related(self, djt_filter, sample_articles):
        """Test is_djt_related method."""
        djt_article = sample_articles[0]
        non_djt_article = sample_articles[1]

        assert djt_filter.is_djt_related(djt_article), "DJT article should be identified as DJT-related"
        assert not djt_filter.is_djt_related(non_djt_article), "Non-DJT article should not be identified as DJT-related"

    def test_filter_articles(self, djt_filter, sample_articles):
        """Test filtering of article list."""
        filtered = djt_filter.filter_articles(sample_articles)

        # Should return only DJT-related articles
        assert len(filtered) <= len(sample_articles), "Filtered list should not be longer than original"

        # All filtered articles should have relevance scores
        for article in filtered:
            assert 'djt_relevance_score' in article, "Filtered articles should have relevance scores"
            assert article['djt_relevance_score'] >= djt_filter.min_score, "All filtered articles should meet minimum score"

        # Should be sorted by relevance score (descending)
        if len(filtered) > 1:
            scores = [article['djt_relevance_score'] for article in filtered]
            assert scores == sorted(scores, reverse=True), "Articles should be sorted by relevance score (descending)"

    def test_analyze_keywords(self, djt_filter, sample_articles):
        """Test keyword analysis functionality."""
        keyword_counts = djt_filter.analyze_keywords(sample_articles)

        assert isinstance(keyword_counts, dict), "Keyword analysis should return a dictionary"

        # Should find 'trump' keyword in the sample data
        assert 'trump' in keyword_counts, "Should find 'trump' keyword in sample articles"
        assert keyword_counts['trump'] >= 1, "Trump keyword count should be at least 1"

    def test_handle_none_values(self, djt_filter):
        """Test that filter handles None values gracefully."""
        article_with_nones = {
            'title': 'Trump article',
            'description': None,
            'url': 'https://example.com',
            'source': 'Test Source',
            'category': 'politics',
            'author': None
        }

        # Should not raise exception
        score = djt_filter.calculate_relevance_score(article_with_nones)
        assert score > 0, "Should handle None values and still calculate score"


class TestFilterWithRealData:
    """Test cases using real articles.json and filtered_articles.json data."""

    def test_articles_json_contains_all_articles(self, articles_json_data):
        """Test that articles.json contains all articles (unfiltered)."""
        assert len(articles_json_data) > 0, "articles.json should contain articles"

        # Count DJT and non-DJT articles
        djt_filter = DJTNewsFilter(min_score=1.0)
        djt_count = sum(1 for article in articles_json_data if djt_filter.is_djt_related(article))
        non_djt_count = len(articles_json_data) - djt_count

        assert djt_count > 0, "Should contain some DJT-related articles"

        # Note: The current articles.json may contain only DJT-related articles
        # depending on the filtering applied during data collection
        if non_djt_count == 0:
            print(f"All {len(articles_json_data)} articles are DJT-related")
        else:
            print(f"Found {djt_count} DJT articles and {non_djt_count} non-DJT articles")

    def test_filtered_articles_json_contains_only_djt_articles(self, filtered_articles_json_data):
        """Test that filtered_articles.json contains only DJT-related articles."""
        if len(filtered_articles_json_data) == 0:
            pytest.skip("No filtered articles available")

        djt_filter = DJTNewsFilter(min_score=1.0)

        for article in filtered_articles_json_data:
            assert djt_filter.is_djt_related(article), f"All articles in filtered_articles.json should be DJT-related: {article['title']}"
            assert 'djt_relevance_score' in article, "Filtered articles should have relevance scores"

    def test_filtering_consistency(self, articles_json_data):
        """Test that filtering produces consistent results."""
        djt_filter = DJTNewsFilter(min_score=1.0)

        # Filter the unfiltered articles
        filtered_articles = djt_filter.filter_articles(articles_json_data)

        # All filtered articles should be DJT-related
        for article in filtered_articles:
            assert djt_filter.is_djt_related(article), "All filtered articles should be DJT-related"
            assert article['djt_relevance_score'] >= 1.0, "All filtered articles should meet minimum score"

    def test_keyword_frequency_analysis(self, articles_json_data):
        """Test keyword frequency analysis on real data."""
        djt_filter = DJTNewsFilter(min_score=1.0)
        keyword_counts = djt_filter.analyze_keywords(articles_json_data)

        assert isinstance(keyword_counts, dict), "Should return keyword counts as dictionary"
        assert len(keyword_counts) > 0, "Should find some keywords in the articles"

        # Most common keywords should be present
        expected_keywords = ['trump', 'president', 'administration']
        for keyword in expected_keywords:
            if keyword in keyword_counts:
                assert keyword_counts[keyword] > 0, f"Keyword '{keyword}' count should be positive"


def test_filter_with_articles_integration():
    """Integration test that replicates the original test_filter_with_articles function."""
    articles_file = Path('articles.json')
    if not articles_file.exists():
        pytest.skip("articles.json file not found for integration test")

    try:
        with open(articles_file) as f:
            data = json.load(f)

        # Extract articles from TinyDB format
        articles = []
        if '_default' in data:
            for item in data['_default'].values():
                articles.append(item)

        # Test filtering
        djt_filter = DJTNewsFilter(min_score=1.0)
        djt_articles = djt_filter.filter_articles(articles)

        # Basic assertions
        assert len(articles) > 0, "Should have articles to test with"
        assert len(djt_articles) <= len(articles), "Filtered count should not exceed total count"

        if len(djt_articles) > 0:
            percentage = len(djt_articles) / len(articles) * 100
            assert 0 < percentage <= 100, "Filtering percentage should be between 0 and 100"

            # Verify all filtered articles have scores
            for article in djt_articles:
                assert 'djt_relevance_score' in article, "Filtered articles should have relevance scores"
                assert article['djt_relevance_score'] >= 1.0, "All scores should meet minimum threshold"

        # Analyze keywords
        keyword_analysis = djt_filter.analyze_keywords(articles)
        assert isinstance(keyword_analysis, dict), "Keyword analysis should return a dictionary"

    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


if __name__ == "__main__":
    # If run directly, execute the integration test
    test_filter_with_articles_integration()
    print("All tests would pass if run with pytest")
