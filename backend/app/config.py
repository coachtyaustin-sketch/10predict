from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://tenpredict:password@localhost:5432/tenpredict"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "tenpredict123"

    # LLM
    openai_api_key: str = ""
    openai_model_chain: str = "gpt-4o-mini"
    openai_model_agents: str = "gpt-4o-mini"
    openai_model_reports: str = "gpt-4o-mini"

    # Data Sources
    finnhub_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "10predict/1.0"

    # Scheduling
    cycle_premarket_hour: int = 6
    cycle_midday_hour: int = 12
    cycle_afterhours_hour: int = 17
    timezone: str = "US/Eastern"

    # Simulation
    max_agents_per_simulation: int = 12
    simulation_rounds: int = 5
    max_stocks_per_cycle: int = 8

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
