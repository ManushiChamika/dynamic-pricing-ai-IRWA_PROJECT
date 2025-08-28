# core/agents/data_collector/__init__.py
"""
Data Collector package for Dynamic Pricing project.

Contains:
- DataRepo: a small aiosqlite-backed repository for market ticks.
- DataCollector: ingestion and publish logic.
- Connectors: mock connector for development/demo.
"""
__all__ = ["repo", "collector", "connectors"]
