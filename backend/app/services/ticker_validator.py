"""Validates tickers: price under $10, US exchange, Robinhood-tradeable."""

import datetime
from typing import NamedTuple

import structlog
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_cache import StockCache

logger = structlog.get_logger()

# Robinhood supports NYSE, NASDAQ, AMEX (not OTC/Pink Sheets)
ROBINHOOD_EXCHANGES = {"NYQ", "NMS", "NGM", "NCM", "ASE", "PCX", "BTS", "NYSE", "NASDAQ", "AMEX"}

# Cache validation results in-memory for the duration of a cycle
_validation_cache: dict[str, "TickerValidation"] = {}


class TickerValidation(NamedTuple):
    ticker: str
    is_valid: bool  # meets all criteria
    price: float
    name: str
    exchange: str
    sector: str
    industry: str
    market_cap: float | None
    reason: str  # why invalid, or "OK"


def validate_ticker(ticker: str) -> TickerValidation:
    """Check if a ticker is under $10, on a US exchange, and Robinhood-tradeable."""
    ticker = ticker.upper().strip()

    # Check in-memory cache first
    if ticker in _validation_cache:
        return _validation_cache[ticker]

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            # Try fast_info as fallback
            try:
                price = stock.fast_info.get("lastPrice", 0)
            except Exception:
                result = TickerValidation(ticker, False, 0, "", "", "", "", None, "No data found")
                _validation_cache[ticker] = result
                return result
        else:
            price = info.get("regularMarketPrice", info.get("currentPrice", 0))

        if not price or price <= 0:
            result = TickerValidation(ticker, False, 0, "", "", "", "", None, "No price data")
            _validation_cache[ticker] = result
            return result

        name = info.get("shortName", info.get("longName", ticker))
        exchange = info.get("exchange", "")
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        market_cap = info.get("marketCap")

        # Check price
        if price >= 10.0:
            result = TickerValidation(
                ticker, False, price, name, exchange, sector, industry, market_cap,
                f"Price ${price:.2f} >= $10"
            )
            _validation_cache[ticker] = result
            return result

        # Check exchange (Robinhood eligibility)
        exchange_upper = exchange.upper()
        is_us_exchange = any(ex in exchange_upper for ex in ROBINHOOD_EXCHANGES)
        if not is_us_exchange and exchange:
            # Some tickers report exchange differently
            quote_type = info.get("quoteType", "")
            if quote_type == "EQUITY" and info.get("market") == "us_market":
                is_us_exchange = True

        if not is_us_exchange:
            result = TickerValidation(
                ticker, False, price, name, exchange, sector, industry, market_cap,
                f"Exchange '{exchange}' not Robinhood-eligible"
            )
            _validation_cache[ticker] = result
            return result

        # Check for OTC markers
        if "OTC" in exchange_upper or "PINK" in exchange_upper:
            result = TickerValidation(
                ticker, False, price, name, exchange, sector, industry, market_cap,
                "OTC/Pink Sheets not on Robinhood"
            )
            _validation_cache[ticker] = result
            return result

        result = TickerValidation(
            ticker, True, price, name, exchange, sector, industry, market_cap, "OK"
        )
        _validation_cache[ticker] = result
        return result

    except Exception as e:
        logger.warning("Ticker validation failed", ticker=ticker, error=str(e))
        result = TickerValidation(ticker, False, 0, "", "", "", "", None, f"Error: {str(e)}")
        _validation_cache[ticker] = result
        return result


async def validate_and_cache_ticker(ticker: str, db: AsyncSession) -> TickerValidation:
    """Validate a ticker and update the stock cache in the database."""
    validation = validate_ticker(ticker)

    # Upsert into stock cache
    result = await db.execute(
        select(StockCache).where(StockCache.ticker == ticker)
    )
    cached = result.scalar_one_or_none()

    if cached:
        cached.last_price = validation.price
        cached.is_robinhood_eligible = validation.is_valid
        cached.last_validated_at = datetime.datetime.now(datetime.timezone.utc)
    elif validation.is_valid:
        cached = StockCache(
            ticker=validation.ticker,
            name=validation.name,
            exchange=validation.exchange,
            sector=validation.sector,
            industry=validation.industry,
            last_price=validation.price,
            market_cap=validation.market_cap,
            is_robinhood_eligible=True,
            last_validated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(cached)

    await db.commit()
    return validation


def clear_validation_cache():
    """Clear the in-memory validation cache between cycles."""
    _validation_cache.clear()
