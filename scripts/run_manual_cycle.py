#!/usr/bin/env python3
"""Manually trigger a single research cycle from the command line."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.services.research_cycle import run_research_cycle


async def main():
    cycle_type = sys.argv[1] if len(sys.argv) > 1 else "manual"
    print(f"Starting {cycle_type} research cycle...")
    result = await run_research_cycle(cycle_type)
    print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
