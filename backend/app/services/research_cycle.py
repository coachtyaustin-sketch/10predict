"""Research cycle orchestrator - runs the complete 3x/day pipeline.

Pipeline:
  1. SCRAPE news, Reddit, blogs
  2. CLUSTER articles into macro trends
  3. CHAIN ANALYSIS on each trend (N-order effects -> penny stocks)
  4. VALIDATE discovered tickers (price < $10, Robinhood-tradeable)
  5. GRAPH UPDATE - store chains in Neo4j
  6. SWARM SIMULATE top candidates
  7. SCORE & REPORT
  8. ACCURACY CHECK on past predictions
"""

import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import async_session, get_neo4j
from app.services.data_collector import collect_all_articles
from app.services.trend_clusterer import cluster_articles_into_trends
from app.services.chain_analyzer import analyze_chain_effects
from app.services.ticker_validator import clear_validation_cache
from app.services.simulation_runner import run_swarm_simulation
from app.services.prediction_engine import generate_prediction
from app.services.report_agent import generate_report
from app.services.accuracy_tracker import evaluate_past_predictions
from app.graph.storage import store_chain_in_graph

logger = structlog.get_logger()


async def run_research_cycle(cycle_type: str = "manual"):
    """Execute a complete research cycle.

    Args:
        cycle_type: pre_market, midday, after_hours, or manual
    """
    start_time = datetime.datetime.now(datetime.timezone.utc)
    logger.info("Starting research cycle", cycle_type=cycle_type)

    clear_validation_cache()

    async with async_session() as db:
        # Step 1: Collect articles from all sources
        logger.info("Step 1: Collecting articles")
        new_articles = await collect_all_articles(db)
        if not new_articles:
            logger.warning("No new articles found, skipping cycle")
            return {"status": "skipped", "reason": "no_new_articles"}

        # Step 2: Cluster articles into macro trends
        logger.info("Step 2: Clustering into trends", articles=len(new_articles))
        trends = await cluster_articles_into_trends(new_articles, db)
        if not trends:
            logger.warning("No trends identified, skipping cycle")
            return {"status": "skipped", "reason": "no_trends"}

        # Step 3 & 4: Chain analysis + ticker validation for each trend
        logger.info("Step 3: Analyzing chain effects", trends=len(trends))
        all_chains = []
        for trend in trends:
            chains = await analyze_chain_effects(trend, db)
            all_chains.extend(chains)

        if not all_chains:
            logger.warning("No valid chains discovered this cycle")
            return {
                "status": "completed",
                "articles": len(new_articles),
                "trends": len(trends),
                "chains": 0,
                "predictions": 0,
            }

        # Step 5: Store chains in Neo4j knowledge graph
        logger.info("Step 5: Updating knowledge graph", chains=len(all_chains))
        neo4j_driver = await get_neo4j()
        if neo4j_driver:
            for chain in all_chains:
                trend = next((t for t in trends if t.id == chain.trend_id), None)
                if trend:
                    try:
                        await store_chain_in_graph(
                            driver=neo4j_driver,
                            trend_name=trend.name,
                            trend_category=trend.category,
                            ticker=chain.ticker,
                            company_name=chain.company_name,
                            chain_links=chain.chain_links or [],
                            chain_narrative=chain.chain_narrative,
                            connection_strength=chain.connection_strength,
                            direction=chain.direction,
                        )
                    except Exception as e:
                        logger.warning(
                            "Graph storage failed",
                            ticker=chain.ticker,
                            error=str(e),
                        )

        # Step 6: Rank chains and simulate top candidates
        ranked_chains = sorted(
            all_chains,
            key=lambda c: c.connection_strength,
            reverse=True,
        )[:settings.max_stocks_per_cycle]

        logger.info("Step 6: Running swarm simulations", candidates=len(ranked_chains))
        predictions = []
        for chain in ranked_chains:
            trend = next((t for t in trends if t.id == chain.trend_id), None)
            if not trend:
                continue

            # Get current price from the validation cache
            from app.services.ticker_validator import _validation_cache

            cached = _validation_cache.get(chain.ticker)
            stock_price = cached.price if cached else 0.0

            if stock_price <= 0:
                continue

            try:
                # Run swarm simulation
                simulation = await run_swarm_simulation(
                    chain=chain,
                    trend_name=trend.name,
                    trend_summary=trend.summary,
                    stock_price=stock_price,
                    db=db,
                )

                # Generate prediction
                prediction = generate_prediction(
                    chain=chain,
                    simulation=simulation,
                    stock_price=stock_price,
                    cycle_type=cycle_type,
                    why_most_miss_it=chain.reasoning,
                )

                # Generate report
                report = await generate_report(prediction, simulation)
                prediction.report_text = report

                # Link simulation to prediction
                simulation.prediction_id = prediction.id

                db.add(prediction)
                await db.commit()

                predictions.append(prediction)

                logger.info(
                    "Prediction complete",
                    ticker=chain.ticker,
                    signal=prediction.signal,
                    score=prediction.score,
                    confidence=prediction.confidence,
                )

            except Exception as e:
                logger.error(
                    "Simulation/prediction failed",
                    ticker=chain.ticker,
                    error=str(e),
                )
                continue

        # Step 7: Evaluate past predictions
        logger.info("Step 7: Evaluating past predictions")
        try:
            await evaluate_past_predictions(db)
        except Exception as e:
            logger.error("Accuracy evaluation failed", error=str(e))

        duration = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()

        result = {
            "status": "completed",
            "cycle_type": cycle_type,
            "duration_seconds": round(duration, 1),
            "articles_collected": len(new_articles),
            "trends_identified": len(trends),
            "chains_discovered": len(all_chains),
            "stocks_simulated": len(ranked_chains),
            "predictions_generated": len(predictions),
        }

        logger.info("Research cycle complete", **result)
        return result
