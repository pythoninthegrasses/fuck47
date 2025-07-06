# Task List: Trump News Sentiment Analysis Feature

Based on `prd-trump-news-sentiment.md`

## Relevant Files

- `.github/workflows/news-refresh.yml` - GitHub Actions workflow for scheduled news data refresh
- `scripts/news_aggregator.py` - Main Python script for news collection and sentiment analysis
- `scripts/requirements.txt` - Python dependencies for news aggregation
- `scripts/config.py` - Configuration management for API keys and settings
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
- BasecoatUI components loaded via CDN for simplicity
- HTMX loaded via CDN for dynamic interactions
- Alpine.js loaded via CDN for reactive frontend components
- News data stored as static JSON files committed to repository
- GitHub Actions handles scheduling and environment variable management

## Tasks

- [ ] 1.0 Set up Python CI pipeline and scheduled data refresh jobs
  - [ ] 1.1 Create GitHub Actions workflow file for scheduled runs
  - [ ] 1.2 Configure environment variables for NewsAPI key and settings
  - [ ] 1.3 Set up Python environment and dependencies in CI
  - [ ] 1.4 Implement error handling and notification for failed builds
  - [ ] 1.5 Configure cron schedule for automated news refresh
- [ ] 2.0 Implement news aggregation system (NewsAPI + RSS feeds)
  - [ ] 2.1 Create NewsAPI client with rate limiting and error handling
  - [ ] 2.2 Implement RSS feed parser for multiple news sources
  - [ ] 2.3 Define Trump-related keyword search patterns
  - [ ] 2.4 Build article deduplication logic
  - [ ] 2.5 Create unified article data structure
- [ ] 3.0 Build sentiment analysis and content filtering pipeline
  - [ ] 3.1 Implement sentiment analysis using TextBlob or VADER
  - [ ] 3.2 Create negative sentiment filtering with configurable thresholds
  - [ ] 3.3 Add pre-filtering for known negative news sources
  - [ ] 3.4 Implement fallback handling for sentiment analysis failures
  - [ ] 3.5 Generate JSON output with filtered articles and metadata
- [ ] 4.0 Create frontend with BasecoatUI styling, HTMX, and Alpine.js integration
  - [ ] 4.1 Update HTML structure with BasecoatUI components
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