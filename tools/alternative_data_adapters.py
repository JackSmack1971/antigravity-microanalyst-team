"""
Alternative Data Adapters module for non-traditional data sources.

This module provides adapters for alternative data sources including:
- News Sentiment Analysis (CryptoPanic, web scraping)
- Social Media Monitoring (Reddit via PRAW)
- Google Trends correlation
- GitHub development activity
- Options Market Data (Deribit)

All adapters are designed to work with free API tiers and include
intelligent caching and fallback mechanisms.
"""
import os
import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from bs4 import BeautifulSoup
import re

# Import from blockchain_adapters for cache reuse
from tools.blockchain_adapters import BlockchainDataCache, RateLimitError


class CryptoPanicAdapter:
    """Adapter for CryptoPanic free API.

    CryptoPanic provides free access to:
    - Cryptocurrency news aggregation
    - Sentiment indicators (positive/negative/neutral)
    - News from major crypto outlets
    - Community voting on news relevance

    Free tier: No API key required, but rate limits apply.
    """

    BASE_URL = "https://cryptopanic.com/api/v1"

    def __init__(self, cache: BlockchainDataCache, api_token: Optional[str] = None):
        """Initialize CryptoPanic adapter.

        Args:
            cache: Cache instance for data persistence.
            api_token: Optional API token for higher rate limits.
        """
        self.cache = cache
        self.api_token = api_token or os.getenv("CRYPTOPANIC_API_TOKEN")

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_news_sentiment(
        self,
        currencies: Optional[List[str]] = None,
        kind: str = 'news'
    ) -> Dict[str, Any]:
        """Get cryptocurrency news with sentiment.

        Args:
            currencies: List of currency codes (e.g., ['BTC', 'ETH']).
            kind: Type of posts ('news', 'media', 'all').

        Returns:
            Dict containing news articles with sentiment scores.

        Example:
            >>> adapter = CryptoPanicAdapter(cache)
            >>> news = await adapter.get_news_sentiment(['BTC'])
            >>> print(news['sentiment_summary'])
        """
        cache_key = f"cryptopanic:news:{','.join(currencies or ['all'])}:{kind}"

        # Try cache first
        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        params = {
            'kind': kind,
            'public': 'true'
        }

        if self.api_token:
            params['auth_token'] = self.api_token

        if currencies:
            params['currencies'] = ','.join(currencies)

        url = f"{self.BASE_URL}/posts/"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    raise RateLimitError("CryptoPanic rate limit exceeded")

                response.raise_for_status()
                data = await response.json()

                # Calculate sentiment summary
                sentiment_data = self._analyze_sentiment(data.get('results', []))
                data['sentiment_summary'] = sentiment_data

                # Cache for 5 minutes
                await self.cache.set(cache_key, data, 'warm')
                return data

    def _analyze_sentiment(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news posts.

        Args:
            posts: List of news posts.

        Returns:
            Dict with sentiment breakdown and scores.
        """
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total = len(posts)

        if total == 0:
            return {
                'sentiment_score': 0.0,
                'distribution': sentiment_counts,
                'total_posts': 0
            }

        for post in posts:
            votes = post.get('votes', {})
            positive = votes.get('positive', 0)
            negative = votes.get('negative', 0)

            if positive > negative:
                sentiment_counts['positive'] += 1
            elif negative > positive:
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1

        # Calculate overall sentiment score (-100 to +100)
        sentiment_score = (
            (sentiment_counts['positive'] - sentiment_counts['negative']) / total * 100
        )

        return {
            'sentiment_score': round(sentiment_score, 2),
            'distribution': sentiment_counts,
            'total_posts': total,
            'positive_pct': round(sentiment_counts['positive'] / total * 100, 2),
            'negative_pct': round(sentiment_counts['negative'] / total * 100, 2),
            'neutral_pct': round(sentiment_counts['neutral'] / total * 100, 2)
        }


class RedditSentimentAdapter:
    """Adapter for Reddit sentiment analysis via PRAW.

    Monitors cryptocurrency subreddits:
    - r/cryptocurrency
    - r/bitcoin
    - r/ethereum
    - etc.

    Free tier: Reddit API is free with registration.
    """

    def __init__(self, cache: BlockchainDataCache):
        """Initialize Reddit adapter.

        Args:
            cache: Cache instance for data persistence.
        """
        self.cache = cache
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "crypto-sentiment-analyzer/1.0")

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_subreddit_sentiment(
        self,
        subreddit: str = 'cryptocurrency',
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get sentiment from a cryptocurrency subreddit.

        Args:
            subreddit: Subreddit name (without 'r/').
            limit: Number of posts to analyze.

        Returns:
            Dict containing sentiment analysis and top keywords.
        """
        cache_key = f"reddit:sentiment:{subreddit}:{limit}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        if not self.client_id or not self.client_secret:
            return {
                'error': 'Reddit API credentials not configured',
                'sentiment_score': 0.0,
                'message': 'Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env'
            }

        try:
            import praw

            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )

            posts_data = []
            subreddit_obj = reddit.subreddit(subreddit)

            for post in subreddit_obj.hot(limit=limit):
                posts_data.append({
                    'title': post.title,
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'upvote_ratio': post.upvote_ratio,
                    'created_utc': datetime.fromtimestamp(post.created_utc).isoformat()
                })

            # Analyze sentiment
            sentiment_analysis = self._calculate_reddit_sentiment(posts_data)

            result = {
                'subreddit': subreddit,
                'posts_analyzed': len(posts_data),
                'sentiment_analysis': sentiment_analysis,
                'top_posts': posts_data[:10],  # Top 10 posts
                'timestamp': datetime.utcnow().isoformat()
            }

            # Cache for 5 minutes
            await self.cache.set(cache_key, result, 'warm')
            return result

        except Exception as e:
            return {
                'error': f'Reddit API error: {str(e)}',
                'sentiment_score': 0.0
            }

    def _calculate_reddit_sentiment(self, posts: List[Dict]) -> Dict[str, Any]:
        """Calculate sentiment from Reddit posts.

        Args:
            posts: List of Reddit posts data.

        Returns:
            Dict with sentiment metrics.
        """
        if not posts:
            return {'sentiment_score': 0.0, 'engagement_score': 0.0}

        total_score = sum(post['score'] for post in posts)
        total_comments = sum(post['num_comments'] for post in posts)
        avg_upvote_ratio = sum(post['upvote_ratio'] for post in posts) / len(posts)

        # Sentiment score based on upvote ratio (0-100 scale)
        sentiment_score = (avg_upvote_ratio - 0.5) * 200  # Maps 0.5-1.0 to 0-100

        # Engagement score based on comments and upvotes
        engagement_score = (total_score + total_comments * 2) / len(posts)

        return {
            'sentiment_score': round(sentiment_score, 2),
            'engagement_score': round(engagement_score, 2),
            'avg_upvote_ratio': round(avg_upvote_ratio, 3),
            'total_upvotes': total_score,
            'total_comments': total_comments,
            'posts_count': len(posts)
        }


class GoogleTrendsAdapter:
    """Adapter for Google Trends data via pytrends.

    Provides:
    - Search interest over time
    - Related queries
    - Regional interest
    - Correlation with price movements

    Free tier: Unlimited (with rate limiting).
    """

    def __init__(self, cache: BlockchainDataCache):
        """Initialize Google Trends adapter.

        Args:
            cache: Cache instance for data persistence.
        """
        self.cache = cache

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_search_interest(
        self,
        keywords: List[str],
        timeframe: str = 'now 7-d'
    ) -> Dict[str, Any]:
        """Get Google Trends search interest.

        Args:
            keywords: List of search terms (max 5).
            timeframe: Time period (e.g., 'now 7-d', 'today 1-m', 'today 3-m').

        Returns:
            Dict containing search interest trends.
        """
        cache_key = f"trends:search:{','.join(keywords)}:{timeframe}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        try:
            from pytrends.request import TrendReq

            # Initialize pytrends
            pytrends = TrendReq(hl='en-US', tz=0)

            # Build payload
            pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='', gprop='')

            # Get interest over time
            interest_over_time = pytrends.interest_over_time()

            if interest_over_time.empty:
                return {
                    'error': 'No data available',
                    'trend_score': 0.0
                }

            # Convert to dictionary
            trends_data = interest_over_time.to_dict('index')

            # Calculate trend metrics
            trend_analysis = self._analyze_trends(interest_over_time, keywords)

            result = {
                'keywords': keywords,
                'timeframe': timeframe,
                'trends_data': {
                    str(k): v for k, v in list(trends_data.items())[-10:]  # Last 10 data points
                },
                'trend_analysis': trend_analysis,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Cache for 5 minutes
            await self.cache.set(cache_key, result, 'warm')
            return result

        except Exception as e:
            return {
                'error': f'Google Trends error: {str(e)}',
                'trend_score': 0.0
            }

    def _analyze_trends(self, df, keywords: List[str]) -> Dict[str, Any]:
        """Analyze trend data.

        Args:
            df: Pandas DataFrame with trend data.
            keywords: List of keywords.

        Returns:
            Dict with trend metrics.
        """
        if df.empty:
            return {'trend_score': 0.0, 'momentum': 'neutral'}

        analysis = {}

        for keyword in keywords:
            if keyword in df.columns:
                values = df[keyword].values

                # Calculate trend momentum
                recent_avg = values[-3:].mean() if len(values) >= 3 else values[-1]
                overall_avg = values.mean()

                momentum = (recent_avg - overall_avg) / (overall_avg + 1) * 100

                # Determine trend direction
                if momentum > 20:
                    direction = 'strong_increase'
                elif momentum > 5:
                    direction = 'moderate_increase'
                elif momentum < -20:
                    direction = 'strong_decrease'
                elif momentum < -5:
                    direction = 'moderate_decrease'
                else:
                    direction = 'neutral'

                analysis[keyword] = {
                    'current_interest': int(values[-1]) if len(values) > 0 else 0,
                    'avg_interest': round(overall_avg, 2),
                    'momentum_pct': round(momentum, 2),
                    'direction': direction,
                    'peak_interest': int(values.max()),
                    'min_interest': int(values.min())
                }

        return analysis


class GitHubActivityAdapter:
    """Adapter for GitHub repository activity tracking.

    Monitors:
    - Commit frequency
    - Contributor activity
    - Issue/PR activity
    - Star/fork growth

    Free tier: GitHub API is free with registration.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, cache: BlockchainDataCache, api_token: Optional[str] = None):
        """Initialize GitHub adapter.

        Args:
            cache: Cache instance for data persistence.
            api_token: Optional GitHub API token for higher rate limits.
        """
        self.cache = cache
        self.api_token = api_token or os.getenv("GITHUB_API_TOKEN")
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.api_token:
            self.headers['Authorization'] = f'token {self.api_token}'

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_repository_activity(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """Get development activity for a repository.

        Args:
            owner: Repository owner (e.g., 'bitcoin').
            repo: Repository name (e.g., 'bitcoin').

        Returns:
            Dict containing repository activity metrics.
        """
        cache_key = f"github:activity:{owner}/{repo}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        async with aiohttp.ClientSession() as session:
            # Get repository info
            repo_url = f"{self.BASE_URL}/repos/{owner}/{repo}"

            async with session.get(repo_url, headers=self.headers) as response:
                if response.status == 429:
                    raise RateLimitError("GitHub rate limit exceeded")

                if response.status == 404:
                    return {'error': f'Repository {owner}/{repo} not found'}

                response.raise_for_status()
                repo_data = await response.json()

            # Get commit activity (last 52 weeks)
            commits_url = f"{self.BASE_URL}/repos/{owner}/{repo}/stats/commit_activity"

            async with session.get(commits_url, headers=self.headers) as response:
                if response.status == 200:
                    commit_activity = await response.json()
                else:
                    commit_activity = []

            # Analyze activity
            activity_analysis = self._analyze_github_activity(repo_data, commit_activity)

            result = {
                'repository': f"{owner}/{repo}",
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'watchers': repo_data.get('watchers_count', 0),
                'open_issues': repo_data.get('open_issues_count', 0),
                'last_update': repo_data.get('updated_at'),
                'activity_analysis': activity_analysis,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Cache for 5 minutes
            await self.cache.set(cache_key, result, 'warm')
            return result

    def _analyze_github_activity(
        self,
        repo_data: Dict,
        commit_activity: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze GitHub activity data.

        Args:
            repo_data: Repository metadata.
            commit_activity: Weekly commit activity.

        Returns:
            Dict with activity metrics.
        """
        if not commit_activity:
            return {
                'activity_score': 0.0,
                'trend': 'unknown',
                'recent_commits': 0
            }

        # Get recent commit counts
        recent_weeks = commit_activity[-4:] if len(commit_activity) >= 4 else commit_activity
        older_weeks = commit_activity[-8:-4] if len(commit_activity) >= 8 else []

        recent_commits = sum(week.get('total', 0) for week in recent_weeks)
        older_commits = sum(week.get('total', 0) for week in older_weeks) if older_weeks else recent_commits

        # Calculate activity trend
        if older_commits > 0:
            trend_pct = ((recent_commits - older_commits) / older_commits) * 100
        else:
            trend_pct = 0

        if trend_pct > 20:
            trend = 'accelerating'
        elif trend_pct > 0:
            trend = 'growing'
        elif trend_pct < -20:
            trend = 'declining'
        elif trend_pct < 0:
            trend = 'slowing'
        else:
            trend = 'stable'

        # Activity score (0-100)
        activity_score = min(100, (recent_commits / 4) * 10)  # Scale based on commits per week

        return {
            'activity_score': round(activity_score, 2),
            'trend': trend,
            'trend_pct': round(trend_pct, 2),
            'recent_commits': recent_commits,
            'avg_commits_per_week': round(recent_commits / len(recent_weeks), 2)
        }


class DeribitOptionsAdapter:
    """Adapter for Deribit public options data.

    Provides:
    - Options volume and open interest
    - Put/Call ratios
    - Implied volatility metrics
    - Options flow data

    Free tier: Public endpoints are free (no authentication required).
    """

    BASE_URL = "https://www.deribit.com/api/v2/public"

    def __init__(self, cache: BlockchainDataCache):
        """Initialize Deribit adapter.

        Args:
            cache: Cache instance for data persistence.
        """
        self.cache = cache

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_options_summary(
        self,
        currency: str = 'BTC'
    ) -> Dict[str, Any]:
        """Get options market summary.

        Args:
            currency: Currency code ('BTC' or 'ETH').

        Returns:
            Dict containing options market data and metrics.
        """
        cache_key = f"deribit:options:{currency}"

        if cached := await self.cache.get(cache_key, 'hot'):
            return cached

        async with aiohttp.ClientSession() as session:
            # Get book summary by currency
            url = f"{self.BASE_URL}/get_book_summary_by_currency"
            params = {
                'currency': currency,
                'kind': 'option'
            }

            async with session.get(url, params=params) as response:
                if response.status == 429:
                    raise RateLimitError("Deribit rate limit exceeded")

                response.raise_for_status()
                data = await response.json()

            if not data.get('result'):
                return {'error': 'No options data available'}

            # Analyze options data
            options_analysis = self._analyze_options_data(data['result'])

            result = {
                'currency': currency,
                'options_count': len(data['result']),
                'options_analysis': options_analysis,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Cache for 1 minute
            await self.cache.set(cache_key, result, 'hot')
            return result

    def _analyze_options_data(self, options: List[Dict]) -> Dict[str, Any]:
        """Analyze options market data.

        Args:
            options: List of options instruments.

        Returns:
            Dict with options metrics.
        """
        if not options:
            return {
                'put_call_ratio': 0.0,
                'avg_iv': 0.0,
                'total_volume': 0.0
            }

        puts = [opt for opt in options if '-P' in opt.get('instrument_name', '')]
        calls = [opt for opt in options if '-C' in opt.get('instrument_name', '')]

        put_volume = sum(opt.get('volume', 0) for opt in puts)
        call_volume = sum(opt.get('volume', 0) for opt in calls)

        put_oi = sum(opt.get('open_interest', 0) for opt in puts)
        call_oi = sum(opt.get('open_interest', 0) for opt in calls)

        # Put/Call ratio (by volume)
        pc_ratio = put_volume / call_volume if call_volume > 0 else 0

        # Put/Call ratio (by open interest)
        pc_ratio_oi = put_oi / call_oi if call_oi > 0 else 0

        # Average implied volatility
        iv_values = [
            opt.get('mark_iv', 0)
            for opt in options
            if opt.get('mark_iv', 0) > 0
        ]
        avg_iv = sum(iv_values) / len(iv_values) if iv_values else 0

        # Total volume
        total_volume = sum(opt.get('volume', 0) for opt in options)
        total_oi = sum(opt.get('open_interest', 0) for opt in options)

        # Market sentiment based on P/C ratio
        if pc_ratio > 1.2:
            sentiment = 'bearish'
        elif pc_ratio > 0.8:
            sentiment = 'neutral'
        else:
            sentiment = 'bullish'

        return {
            'put_call_ratio': round(pc_ratio, 3),
            'put_call_ratio_oi': round(pc_ratio_oi, 3),
            'avg_implied_volatility': round(avg_iv, 2),
            'total_volume': round(total_volume, 2),
            'total_open_interest': round(total_oi, 2),
            'put_volume': round(put_volume, 2),
            'call_volume': round(call_volume, 2),
            'market_sentiment': sentiment,
            'options_count': len(options)
        }


# Example usage and testing functions
async def test_alternative_adapters():
    """Test all alternative data adapters."""
    cache = BlockchainDataCache()

    print("Testing CryptoPanic News Sentiment...")
    cryptopanic = CryptoPanicAdapter(cache)
    news = await cryptopanic.get_news_sentiment(['BTC', 'ETH'])
    print(f"Sentiment Score: {news.get('sentiment_summary', {}).get('sentiment_score', 'N/A')}")

    print("\nTesting Reddit Sentiment...")
    reddit = RedditSentimentAdapter(cache)
    reddit_data = await reddit.get_subreddit_sentiment('cryptocurrency', limit=50)
    print(f"Reddit Sentiment: {reddit_data.get('sentiment_analysis', {}).get('sentiment_score', 'N/A')}")

    print("\nTesting Google Trends...")
    trends = GoogleTrendsAdapter(cache)
    trends_data = await trends.get_search_interest(['Bitcoin', 'Ethereum'], timeframe='now 7-d')
    print(f"Trends Analysis: {trends_data.get('trend_analysis', {})}")

    print("\nTesting GitHub Activity...")
    github = GitHubActivityAdapter(cache)
    github_data = await github.get_repository_activity('bitcoin', 'bitcoin')
    print(f"GitHub Activity Score: {github_data.get('activity_analysis', {}).get('activity_score', 'N/A')}")

    print("\nTesting Deribit Options...")
    deribit = DeribitOptionsAdapter(cache)
    options_data = await deribit.get_options_summary('BTC')
    print(f"Put/Call Ratio: {options_data.get('options_analysis', {}).get('put_call_ratio', 'N/A')}")

    print("\nAll alternative data adapter tests completed!")


if __name__ == "__main__":
    asyncio.run(test_alternative_adapters())
