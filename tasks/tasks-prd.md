# Task List: Trump News Sentiment Analysis Feature

Based on `prd-trump-news-sentiment.md`

## Relevant Files

- `.github/workflows/news-refresh.yml` - GitHub Actions workflow for scheduled news data refresh
- `scripts/news_aggregator.py` - Main Python script for news collection and sentiment analysis
- `scripts/requirements.txt` - Python dependencies for news aggregation
- `config.py` - Configuration management for API keys and settings
- `utils/filter.py` - DJT-related news filtering using Wikipedia keyword analysis
- `scripts/sentiment_analyzer.py` - Sentiment analysis logic and filtering
- `scripts/rss_parser.py` - RSS feed parsing utilities
- `scripts/newsapi_client.py` - NewsAPI integration and rate limiting
- `data/news_data.json` - Generated news data consumed by frontend
- `data/last_updated.json` - Timestamp tracking for build status
- `docs/index.html` - Updated main HTML page with BasecoatUI and HTMX
- `docs/css/styles.css` - Custom styles and BasecoatUI integration
- `docs/js/app.js` - Alpine.js components for navigation, auto-refresh animations, and interactions
- `docs/assets/trump-cartoon.png` - Cartoon Trump character image
- `.env.example` - Example environment variables file
- `README.md` - Updated documentation with build and deployment instructions

### Notes

- Python scripts run in CI environment, no local testing infrastructure needed
- Basecoat components loaded via CDN for simplicity
- HTMX loaded via CDN for dynamic interactions
- Alpine.js loaded via CDN for reactive frontend components
- News data stored as static JSON files committed to repository
- GitHub Actions handles scheduling and environment variable management

## Tasks

- [ ] 1.0 Set up Python CI pipeline and scheduled data refresh jobs
  - [x] 1.1 Create GitHub Actions workflow file for scheduled runs
  - [ ] 1.2 Configure environment variables for NewsAPI key and settings
  - [ ] 1.3 Set up Python environment and dependencies in CI
  - [ ] 1.4 Implement error handling and notification for failed builds
  - [ ] 1.5 Configure cron schedule for automated news refresh
- [ ] 2.0 Implement news aggregation system (NewsAPI + RSS feeds)
  - [x] 2.1 Create NewsAPI client with rate limiting and error handling
  - [x] 2.2 Implement RSS feed parser for multiple news sources
  - [ ] 2.3 Define Trump-related keyword search patterns
  - [x] 2.4 Build article deduplication logic
  - [x] 2.5 Create unified article data structure
  - [x] 2.6 Remove FastHTML web framework dependencies and related imports
  - [x] 2.7 Remove Starlette server components (FileResponse, Response, uvicorn)
  - [x] 2.8 Remove all HTTP routing decorators and web server endpoints
  - [x] 2.9 Remove HTML generation functions and UI components
  - [x] 2.10 Replace ArticleDB with TinyDB for URL storage and caching
  - [x] 2.11 Filter news sources to only include legitimate news outlets per NewsAPI sources endpoint
  - [x] 2.12 Rename `scratch.py` to `main.py`
  - [x] 2.13 Write business logic for rss feed parsing
  - [x] 2.14 Concatenate articles.json with rss feed articles
  - [x] 2.15 Add `news_aggregator.py` to `utils/` (Split from main.py)
  - [x] 2.16 Add `db.py` to `utils/` (Split from news_aggregator.py)
  - [x] 2.17 Add `rss.py` to `utils/` (Split from news_aggregator.py)
  - [x] 2.18 Split environment variables into a config.py file
    - Use decouple to load environment variables and .env files
  - [x] 2.19 Convert from web application to static JSON generation script
  - [x] 2.21 Implement proper deduplication using TinyDB for URL tracking
  - [x] 2.20 Add `utils/filter.py` - Update configuration to focus on DJT-related news filtering
- [ ] 3.0 Build sentiment analysis and content filtering pipeline
  - [ ] 3.1 Implement sentiment analysis using `TextBlob` or `VADER`
  - [ ] 3.2 Create negative sentiment filtering with configurable thresholds
  - [ ] 3.3 Add pre-filtering for known negative news sources
  - [ ] 3.4 Implement fallback handling for sentiment analysis failures
  - [ ] 3.5 Generate JSON output with filtered articles and metadata
- [ ] 4.0 Create frontend with Basecoat styling, HTMX, and Alpine.js integration
  - [ ] 4.1 Update HTML structure with Basecoat components
  - [ ] 4.2 Position cartoon Trump image in bottom-left corner
  - [ ] 4.3 Design oversized speech bubble layout for center content display
  - [ ] 4.4 Integrate HTMX for dynamic content loading
  - [ ] 4.5 Set up Alpine.js for reactive frontend components
  - [ ] 4.6 Implement responsive design for mobile and desktop
- [ ] 5.0 Implement data rendering and UI interactions with Alpine.js
  - [ ] 5.1 Create Alpine.js component for article display with headlines, sources, and dates
  - [ ] 5.2 Implement text truncation with ellipsis for long content using Alpine.js
  - [ ] 5.3 Add left/right navigation arrows within speech bubble (hidden until hover) using Alpine.js
  - [ ] 5.4 Implement manual article navigation with arrow controls using Alpine.js
  - [ ] 5.5 Create auto-refresh animation every 10 seconds with right-to-left fade using Alpine.js
  - [ ] 5.6 Add smooth transitions between articles for both manual and auto navigation
  - [ ] 5.7 Handle empty states when no articles are available using Alpine.js
  - [ ] 5.8 Add loading states and error handling for dynamic content using Alpine.js
