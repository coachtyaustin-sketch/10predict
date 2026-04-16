# 10Predict

**Chain-of-Effects Penny Stock Intelligence**

10Predict discovers hidden stock plays by analyzing N-order effects that most investors miss. Instead of tracking stocks directly, it scans news, Reddit, and financial feeds for macro trends, then reasons through supply chain dependencies to find penny stocks (<$10, Robinhood-tradeable) that could make significant moves.

## How It Works

```
News: "Microsoft announces $50B AI data center expansion"
         |
    1st Order (obvious): AI stocks (NVDA, AMD) - everyone knows this
    2nd Order: Chip manufacturing equipment - some know this  
    3rd Order: Power companies near data center sites - HIDDEN PLAY
         |
    Filter: <$10, NYSE/NASDAQ/AMEX, Robinhood-tradeable
         |
    Swarm Simulation: 12 AI agents debate the chain connection
         |
    Output: "STRONG_BUY: $USEG - US Energy Corp @ $3.20"
            Chain: AI Expansion -> Power Demand -> Small Energy Producers
            Confidence: 72% | 3rd Order Effect
```

## Architecture

- **Research-First Pipeline**: Scrape -> Cluster Trends -> Chain Analysis -> Validate -> Simulate -> Predict
- **Chain-of-Effects Engine**: LLM reasons 3+ levels deep through supply chains, dependencies, and market effects
- **Swarm Simulation**: 12 specialized AI agents (supply chain analyst, skeptic, timing analyst, etc.) debate each chain connection
- **Runs 3x Daily**: Pre-market (6 AM), Midday (12 PM), After-hours (5 PM) ET

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.12+) |
| Database | PostgreSQL + pgvector |
| Knowledge Graph | Neo4j |
| LLM | OpenAI (gpt-4o-mini) |
| Scheduling | APScheduler |
| Frontend | Vue 3 + Tailwind CSS |
| Data Sources | Reddit (PRAW), Finnhub, RSS Feeds, yfinance |

## Quick Start

1. Copy environment config:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. Start databases:
   ```bash
   docker compose up -d postgres neo4j
   ```

3. Install dependencies:
   ```bash
   make install
   ```

4. Run the backend:
   ```bash
   make backend
   ```

5. Run the frontend (separate terminal):
   ```bash
   make frontend
   ```

6. Trigger a research cycle:
   ```bash
   make cycle
   ```

## API Keys Required

- **OpenAI** (`OPENAI_API_KEY`): For chain analysis, agent simulation, and reports
- **Reddit** (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`): For scraping r/pennystocks, r/wallstreetbets, etc.
- **Finnhub** (`FINNHUB_API_KEY`): For financial news (free tier: 60 calls/min)

## Estimated Cost

~$0.50-0.80/day using gpt-4o-mini with 12 agents, 8 stocks/cycle, 3 cycles/day.

## Project Structure

```
10predict/
├── backend/
│   └── app/
│       ├── api/           # REST endpoints
│       ├── models/        # SQLAlchemy ORM (articles, trends, chains, predictions)
│       ├── services/      # Core logic
│       │   ├── chain_analyzer.py      # N-order effect reasoning
│       │   ├── trend_clusterer.py     # Article -> trend clustering
│       │   ├── simulation_runner.py   # Multi-agent swarm debate
│       │   ├── prediction_engine.py   # Quantitative scoring
│       │   └── research_cycle.py      # Full pipeline orchestrator
│       ├── agents/        # Agent persona definitions
│       ├── graph/         # Neo4j knowledge graph
│       └── scheduler/     # 3x daily cron jobs
├── frontend/
│   └── src/
│       ├── views/         # Dashboard, Predictions, Research Monitor
│       └── components/    # Signal badges, confidence meters, chain indicators
└── docker-compose.yml
```
