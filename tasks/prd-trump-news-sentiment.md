# PRD: Trump News Sentiment Analysis Feature

## Introduction/Overview

This feature will transform the existing static landing page into a dynamic news aggregation site that displays current events involving Donald Trump with negative sentiment analysis. The site will maintain its existing visual identity while adding real-time news content filtered for negative sentiment, displayed through a cartoon Trump character with speech bubble interface.

**Problem it solves:** Users want to see current negative news coverage about Donald Trump in a visually engaging format without navigating to multiple news sources.

**Goal:** Create an automated news aggregation system that displays Trump-related negative news stories in an entertaining, cartoon-style interface.

## Goals

1. Automatically aggregate Trump-related news from multiple sources (NewsAPI + RSS feeds)
2. Filter and display only articles with negative sentiment
3. Present content through a cartoon Trump character with speech bubble interface
4. Maintain current site branding while adding modern UI components
5. Ensure reliable, periodic content updates without manual intervention

## User Stories

- **As a visitor**, I want to see current negative news about Trump so that I can stay informed about controversial developments
- **As a user**, I want the news to refresh automatically so that I always see the latest content without manual refreshing
- **As a viewer**, I want an entertaining visual presentation so that consuming news feels engaging rather than overwhelming
- **As a mobile user**, I want the interface to work well on all devices so that I can access content anywhere

## Functional Requirements

1. **News Aggregation System**
   - Must integrate with NewsAPI for real-time news fetching
   - Must support RSS feed parsing from pre-selected negative-leaning sources
   - Must search for Trump-related keywords ("Trump", "Donald Trump", "45th President", "47th President")
   - Must store and manage API keys securely via environment variables

2. **Content Filtering & Sentiment Analysis**
   - Must pre-filter news sources known for negative Trump coverage
   - Must analyze article sentiment and display only negative-sentiment articles
   - Must handle sentiment scoring with configurable thresholds
   - Must fallback gracefully when sentiment analysis fails

3. **Static Site Generation**
   - Must generate static HTML files with embedded news content
   - Must rebuild site automatically based on configurable time intervals (environment variable)
   - Must maintain existing site structure and GitHub Pages compatibility
   - Must handle build failures gracefully without breaking the site

4. **Visual Presentation**
   - Must position cartoon Trump image in bottom-left corner of page
   - Must display news content in a speech bubble positioned in center of page
   - Must implement text truncation with ellipsis for long articles
   - Must use BasecoatUI components for news cards, buttons, and interactive elements
   - Must maintain responsive design for mobile and desktop

5. **Content Display**
   - Must show article headlines, source, and publication date
   - Must provide links to original articles
   - Must display multiple articles with smooth transitions
   - Must handle empty states when no negative articles are found

6. **Technical Infrastructure**
   - Must use Python for business logic (sentiment analysis, API calls, content processing)
   - Must use HTMX for dynamic content loading without full page refreshes
   - Must implement error handling for API failures and network issues
   - Must include logging for debugging and monitoring

## Non-Goals (Out of Scope)

- Real-time chat or user interaction features
- User accounts or personalization
- Comments or social sharing functionality
- Administrative dashboard for content management
- Support for other political figures or general news
- Complex sentiment analysis beyond basic negative/positive classification
- Database storage (content is regenerated on each build)

## Design Considerations

- **BasecoatUI Integration**: Use BasecoatUI's card, button, and typography components for news display
- **Visual Hierarchy**: Speech bubble should be prominent and centered, with Trump cartoon as supporting visual element
- **Responsive Design**: Ensure proper scaling on mobile devices, with speech bubble adapting to screen size
- **Loading States**: Implement subtle loading indicators when content is being fetched
- **Error States**: Design fallback content when news feeds are unavailable

## Technical Considerations

- **API Rate Limits**: Implement proper rate limiting and caching for NewsAPI and RSS feeds
- **Build Performance**: Optimize build times by caching API responses and processing incrementally
- **Security**: Store API keys in environment variables, never commit to repository
- **Reliability**: Implement retry logic for failed API calls and graceful degradation
- **GitHub Pages**: Ensure all generated content is compatible with GitHub Pages hosting
- **Python Dependencies**: Use lightweight libraries for sentiment analysis (TextBlob, VADER) to minimize build complexity

## Success Metrics

- **Content Freshness**: News content updates within configured time interval (measurable via build logs)
- **Sentiment Accuracy**: 90%+ of displayed articles have genuinely negative sentiment about Trump
- **Site Performance**: Page load time remains under 3 seconds despite dynamic content
- **User Engagement**: Increased time on site and return visits compared to static version
- **Technical Reliability**: 95%+ uptime with successful builds and content updates

## Open Questions

1. **Content Moderation**: Should there be any content filtering beyond sentiment analysis (e.g., explicit language, extreme content)?
2. **Article Limits**: How many articles should be displayed at once? Should there be pagination or infinite scroll?
3. **Update Frequency**: What's the optimal refresh interval to balance freshness with API costs and build performance?
4. **Fallback Content**: What should be displayed when no negative articles are found or APIs are down?
5. **Analytics**: Should we track which articles are most clicked or how users interact with the content?
6. **Mobile Experience**: Should the cartoon Trump and speech bubble layout adapt differently for mobile vs desktop?