#!/usr/bin/env python

"""
News filtering module for DJT-related content.
Uses keyword matching based on Wikipedia word frequency analysis.
"""

import json
import re
from collections import Counter
from typing import Dict, List, Set

# DJT-related keywords based on Wikipedia frequency analysis
DJT_KEYWORDS = {
    # Primary keywords (high relevance)
    'primary': {
        'trump',
        'donald',
        'maga',
        'presidency',
        'president',
        'administration',
        'white house',
        'republican',
        'gop',
        'election',
        'campaign',
        'rally',
        'rallies',
        'impeachment',
        'january 6',
        'mar-a-lago',
        'truth social',
    },
    # Secondary keywords (moderate relevance)
    'secondary': {
        'biden',
        'harris',
        'pence',
        'desantis',
        'musk',
        'endorsement',
        'endorsements',
        'primary',
        'primaries',
        'convention',
        'debate',
        'debates',
        'transition',
        'appointment',
        'appointments',
        'nominee',
        'candidates',
        'nomination',
    },
    # Policy keywords (contextual relevance)
    'policy': {
        'immigration',
        'border',
        'wall',
        'mexico',
        'china',
        'trade',
        'tariffs',
        'supreme court',
        'judges',
        'foreign policy',
        'iran',
        'israel',
        'covid-19',
        'pandemic',
        'tax',
        'taxes',
        'classified documents',
        'indictment',
        'investigation',
        'fraud',
        'conviction',
        'lawsuit',
        'legal',
        'georgia',
        'new york',
        'florida',
    },
}

# All keywords combined for quick lookup
ALL_KEYWORDS = set()
for category in DJT_KEYWORDS.values():
    ALL_KEYWORDS.update(category)

# Compile regex patterns for efficient matching
KEYWORD_PATTERNS = {keyword: re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE) for keyword in ALL_KEYWORDS}


class DJTNewsFilter:
    """Filter for identifying DJT-related news articles."""

    def __init__(self, min_score: float = 1.0):
        """
        Initialize the filter with minimum relevance score.

        Args:
            min_score: Minimum relevance score for an article to be considered DJT-related
        """
        self.min_score = min_score

    def calculate_relevance_score(self, article: dict[str, str]) -> float:
        """
        Calculate relevance score for an article based on keyword matching.

        Args:
            article: Dictionary containing article data (title, description, etc.)

        Returns:
            Float score indicating DJT-relevance (higher = more relevant)
        """
        score = 0.0

        # Combine text fields for analysis (handle None values)
        text_content = ' '.join(
            [
                article.get('title', '') or '',
                article.get('description', '') or '',
                article.get('source', '') or '',
                article.get('author', '') or '',
            ]
        ).lower()

        # Count keyword matches with weighted scoring
        for keyword in DJT_KEYWORDS['primary']:
            if KEYWORD_PATTERNS[keyword].search(text_content):
                score += 3.0  # High weight for primary keywords

        for keyword in DJT_KEYWORDS['secondary']:
            if KEYWORD_PATTERNS[keyword].search(text_content):
                score += 2.0  # Medium weight for secondary keywords

        for keyword in DJT_KEYWORDS['policy']:
            if KEYWORD_PATTERNS[keyword].search(text_content):
                score += 1.0  # Lower weight for policy keywords

        return score

    def is_djt_related(self, article: dict[str, str]) -> bool:
        """
        Check if an article is DJT-related based on relevance score.

        Args:
            article: Dictionary containing article data

        Returns:
            Boolean indicating if article is DJT-related
        """
        score = self.calculate_relevance_score(article)
        return score >= self.min_score

    def filter_articles(self, articles: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Filter a list of articles to only include DJT-related ones.

        Args:
            articles: List of article dictionaries

        Returns:
            List of DJT-related articles with relevance scores added
        """
        djt_articles = []

        for article in articles:
            score = self.calculate_relevance_score(article)
            if score >= self.min_score:
                # Add relevance score to article
                article_with_score = article.copy()
                article_with_score['djt_relevance_score'] = score
                djt_articles.append(article_with_score)

        # Sort by relevance score (descending)
        djt_articles.sort(key=lambda x: x['djt_relevance_score'], reverse=True)

        return djt_articles

    def analyze_keywords(self, articles: list[dict[str, str]]) -> dict[str, int]:
        """
        Analyze keyword frequency in a collection of articles.

        Args:
            articles: List of article dictionaries

        Returns:
            Dictionary mapping keywords to their frequency counts
        """
        keyword_counts = Counter()

        for article in articles:
            text_content = ' '.join(
                [
                    article.get('title', '') or '',
                    article.get('description', '') or '',
                    article.get('source', '') or '',
                    article.get('author', '') or '',
                ]
            ).lower()

            for keyword in ALL_KEYWORDS:
                if KEYWORD_PATTERNS[keyword].search(text_content):
                    keyword_counts[keyword] += 1

        return dict(keyword_counts)


# Backward compatibility alias
TrumpNewsFilter = DJTNewsFilter
