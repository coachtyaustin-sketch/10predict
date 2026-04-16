"""Neo4j graph storage for chain-of-effects relationships."""

import structlog
from neo4j import AsyncDriver

from app.graph.schema import SETUP_QUERIES

logger = structlog.get_logger()


async def setup_graph_schema(driver: AsyncDriver):
    """Create constraints and indexes in Neo4j."""
    async with driver.session() as session:
        for query in SETUP_QUERIES:
            try:
                await session.run(query)
            except Exception as e:
                logger.warning("Graph schema setup query skipped", query=query, error=str(e))


async def store_chain_in_graph(
    driver: AsyncDriver,
    trend_name: str,
    trend_category: str,
    ticker: str,
    company_name: str,
    chain_links: list[dict],
    chain_narrative: str,
    connection_strength: float,
    direction: str,
):
    """Store a complete effect chain in Neo4j.

    Creates: Trend -> Industry -> ... -> Industry -> Stock
    """
    async with driver.session() as session:
        # Create/merge the trend node
        await session.run(
            """
            MERGE (t:Trend {name: $name})
            SET t.category = $category, t.updated_at = datetime()
            """,
            name=trend_name,
            category=trend_category,
        )

        # Create/merge the stock node
        await session.run(
            """
            MERGE (s:Stock {ticker: $ticker})
            SET s.name = $name, s.updated_at = datetime()
            """,
            ticker=ticker,
            name=company_name,
        )

        # Create chain node
        chain_id = f"{trend_name}::{ticker}"
        await session.run(
            """
            MERGE (c:Chain {chain_id: $chain_id})
            SET c.narrative = $narrative,
                c.strength = $strength,
                c.direction = $direction,
                c.depth = $depth,
                c.updated_at = datetime()
            """,
            chain_id=chain_id,
            narrative=chain_narrative,
            strength=connection_strength,
            direction=direction,
            depth=len(chain_links),
        )

        # Link trend -> chain -> stock
        await session.run(
            """
            MATCH (t:Trend {name: $trend_name})
            MATCH (c:Chain {chain_id: $chain_id})
            MERGE (t)-[:DISCOVERED_VIA]->(c)
            """,
            trend_name=trend_name,
            chain_id=chain_id,
        )
        await session.run(
            """
            MATCH (c:Chain {chain_id: $chain_id})
            MATCH (s:Stock {ticker: $ticker})
            MERGE (c)-[:AFFECTS]->(s)
            """,
            chain_id=chain_id,
            ticker=ticker,
        )

        # Create industry nodes and chain links
        for link in chain_links:
            from_entity = link.get("from", "")
            to_entity = link.get("to", "")
            rel_type = link.get("relationship", "REQUIRES")

            # Create/merge industry nodes
            await session.run(
                "MERGE (i:Industry {name: $name}) SET i.updated_at = datetime()",
                name=from_entity,
            )
            await session.run(
                "MERGE (i:Industry {name: $name}) SET i.updated_at = datetime()",
                name=to_entity,
            )

            # Create the chain link relationship
            await session.run(
                f"""
                MATCH (a:Industry {{name: $from_name}})
                MATCH (b:Industry {{name: $to_name}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.explanation = $explanation,
                    r.chain_id = $chain_id,
                    r.updated_at = datetime()
                """,
                from_name=from_entity,
                to_name=to_entity,
                explanation=link.get("explanation", ""),
                chain_id=chain_id,
            )

    logger.info("Stored chain in graph", trend=trend_name, ticker=ticker)


async def get_stock_chains(driver: AsyncDriver, ticker: str) -> list[dict]:
    """Retrieve all known chains affecting a stock."""
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (t:Trend)-[:DISCOVERED_VIA]->(c:Chain)-[:AFFECTS]->(s:Stock {ticker: $ticker})
            RETURN t.name as trend, c.narrative as chain, c.strength as strength,
                   c.direction as direction, c.depth as depth
            ORDER BY c.strength DESC
            """,
            ticker=ticker,
        )
        return [dict(record) async for record in result]


async def get_related_stocks(driver: AsyncDriver, ticker: str) -> list[dict]:
    """Find stocks connected through shared trends or industries."""
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s1:Stock {ticker: $ticker})<-[:AFFECTS]-(c1:Chain)<-[:DISCOVERED_VIA]-(t:Trend)
                  -[:DISCOVERED_VIA]->(c2:Chain)-[:AFFECTS]->(s2:Stock)
            WHERE s2.ticker <> $ticker
            RETURN DISTINCT s2.ticker as ticker, s2.name as name,
                   t.name as shared_trend, c2.narrative as chain
            LIMIT 10
            """,
            ticker=ticker,
        )
        return [dict(record) async for record in result]
