from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from neo4j import AsyncGraphDatabase

from app.config import settings

# PostgreSQL
engine = create_async_engine(settings.database_url, echo=False, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with async_session() as session:
        yield session


async def init_db():
    """Create tables on startup."""
    from app.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def shutdown_db():
    await engine.dispose()


# Neo4j
_neo4j_driver = None


async def init_neo4j():
    global _neo4j_driver
    _neo4j_driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


async def get_neo4j():
    return _neo4j_driver


async def shutdown_neo4j():
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()
