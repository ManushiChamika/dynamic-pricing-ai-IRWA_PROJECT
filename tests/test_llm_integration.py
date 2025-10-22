import os
import sys
import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent))

from core.agents.price_optimizer.llm_brain import LLMBrain
from core.agents.price_optimizer.optimizer import optimize, Features
from backend.routers.messages import router as messages_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestPriceOptimizerLLMIntegration:
    
    def setup_method(self):
        self.db_path = Path(__file__).parent / "test_market.db"
        if self.db_path.exists():
            self.db_path.unlink()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE market_data (
                id INTEGER PRIMARY KEY,
                sku TEXT,
                competitor TEXT,
                price REAL,
                stock_level INTEGER,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO market_data (sku, competitor, price, stock_level, timestamp)
            VALUES ('LAP001', 'CompetitorA', 1200.0, 5, '2024-01-01')
        """)
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_optimize_function_basic(self):
        features = Features(
            sku="LAP001",
            our_price=1200.0,
            competitor_price=1150.0,
            demand_index=0.8,
            cost=900.0
        )
        
        result = optimize(features, min_price=950.0, max_price=1500.0, min_margin=0.12)
        
        assert "recommended_price" in result
        assert result["recommended_price"] > 0
        assert "confidence" in result
        assert "rationale" in result





class TestEndToEndLLMWorkflow:
    
    def setup_method(self):
        self.db_path = Path(__file__).parent / "test_e2e.db"
        if self.db_path.exists():
            self.db_path.unlink()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE market_data (
                id INTEGER PRIMARY KEY,
                sku TEXT,
                competitor TEXT,
                price REAL,
                stock_level INTEGER,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO market_data (sku, competitor, price, stock_level, timestamp)
            VALUES 
            ('LAP001', 'CompetitorA', 1200.0, 5, '2024-01-01'),
            ('LAP001', 'CompetitorB', 1250.0, 3, '2024-01-01'),
            ('LAP001', 'CompetitorC', 1180.0, 8, '2024-01-01')
        """)
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_full_pricing_workflow_basic(self):
        features = Features(
            sku="LAP001",
            our_price=1200.0,
            competitor_price=1180.0,
            cost=950.0,
            demand_index=0.75
        )
        
        result = optimize(features, min_price=1000.0, max_price=1500.0, min_margin=0.10)
        
        assert "recommended_price" in result
        assert "confidence" in result
        assert "rationale" in result
        assert result["recommended_price"] >= 1000.0
        assert result["recommended_price"] <= 1500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
