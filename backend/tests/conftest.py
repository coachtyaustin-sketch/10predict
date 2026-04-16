import pytest


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    return [
        {
            "source": "reddit",
            "source_id": "reddit_abc123",
            "title": "Microsoft announces $50B AI data center expansion",
            "body": "This is huge for the AI infrastructure space...",
            "url": "https://reddit.com/r/stocks/abc123",
            "author": "test_user",
            "subreddit": "stocks",
            "score": 500.0,
        },
        {
            "source": "finnhub",
            "source_id": "finnhub_def456",
            "title": "FDA approves new cancer treatment from small biotech",
            "body": "The FDA has granted approval...",
            "url": "https://example.com/fda-approval",
            "author": "Reuters",
            "subreddit": None,
            "score": 0.0,
        },
    ]


@pytest.fixture
def sample_chain_data():
    """Sample chain-of-effects data for testing."""
    return {
        "ticker": "USEG",
        "company_name": "US Energy Corp",
        "chain_narrative": "AI Data Centers -> Power Demand -> Small Energy Producers",
        "chain_links": [
            {
                "from": "AI Data Center Expansion",
                "to": "Power Grid Infrastructure",
                "relationship": "REQUIRES",
                "explanation": "Data centers consume enormous electricity",
            },
            {
                "from": "Power Grid Infrastructure",
                "to": "US Energy Corp",
                "relationship": "ENABLES",
                "explanation": "Small producers benefit from increased demand",
            },
        ],
        "chain_depth": 2,
        "connection_strength": 0.65,
        "direction": "bullish",
    }
