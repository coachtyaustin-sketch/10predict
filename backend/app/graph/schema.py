"""Neo4j graph schema for chain-of-effects knowledge graph."""

# Node labels
TREND_LABEL = "Trend"
INDUSTRY_LABEL = "Industry"
STOCK_LABEL = "Stock"
EVENT_LABEL = "Event"
CHAIN_LABEL = "Chain"

# Relationship types
REQUIRES = "REQUIRES"
ENABLES = "ENABLES"
DISPLACES = "DISPLACES"
REGULATES = "REGULATES"
SUPPORTS = "SUPPORTS"
AFFECTS = "AFFECTS"
HAS_PLAYER = "HAS_PLAYER"
CHAIN_LINK = "CHAIN_LINK"
DISCOVERED_VIA = "DISCOVERED_VIA"

# Constraints and indexes (run on startup)
SETUP_QUERIES = [
    "CREATE CONSTRAINT stock_ticker IF NOT EXISTS FOR (s:Stock) REQUIRE s.ticker IS UNIQUE",
    "CREATE CONSTRAINT trend_name IF NOT EXISTS FOR (t:Trend) REQUIRE t.name IS UNIQUE",
    "CREATE INDEX industry_name IF NOT EXISTS FOR (i:Industry) ON (i.name)",
    "CREATE INDEX chain_id IF NOT EXISTS FOR (c:Chain) ON (c.chain_id)",
]
