#!/usr/bin/env python

from decouple import config

# NewsAPI Configuration
NEWS_API_KEY = config('NEWS_API_KEY', default="")
TOP_HEADLINES = config('TOP_HEADLINES', default="https://newsapi.org/v2/top-headlines")
EVERYTHING = config('EVERYTHING', default="https://newsapi.org/v2/everything")
PAGE_SIZE = config('PAGE_SIZE', default=100, cast=int)

# Filtering Configuration
EXCLUDE_DOMAINS = config('EXCLUDE_DOMAINS', default="")
EXCLUDE_URLS = config('EXCLUDE_URLS', default="goodbullhunting.com,queerty.com")

# RSS Feed Configuration
RSS_FEEDS = config('RSS_FEEDS', default="")

# Caching Configuration
CACHE_SESSION = config('CACHE_SESSION', default=True, cast=bool)
CACHE_HOURS = config('CACHE_HOURS', default=8, cast=int)
CACHE_TTL = CACHE_HOURS * 60 * 60  # Convert hours to seconds
TTL = config('CACHE_TTL', default=CACHE_TTL, cast=int)

# Categories for news fetching
CATEGORIES = (
    'business',
    'general',
    'health',
    'science',
    'technology',
)

# DJT filtering configuration
DJT_FILTER_ENABLED = config('DJT_FILTER_ENABLED', default=True, cast=bool)
DJT_FILTER_MIN_SCORE = config('DJT_FILTER_MIN_SCORE', default=1.0, cast=float)

# Sentiment analysis configuration (see docs/ai.md)
SENTIMENT_ENABLED = config('SENTIMENT_ENABLED', default=True, cast=bool)
SENTIMENT_MAX_SCORE = config('SENTIMENT_MAX_SCORE', default=0.0, cast=float)

# LLM judge configuration - any OpenAI-compatible chat completions endpoint (default: Fireworks)
LLM_API_KEY = config('LLM_API_KEY', default="")
LLM_BASE_URL = config('LLM_BASE_URL', default="https://api.fireworks.ai/inference/v1")
LLM_MODEL = config('LLM_MODEL', default="accounts/fireworks/models/gpt-oss-20b")
