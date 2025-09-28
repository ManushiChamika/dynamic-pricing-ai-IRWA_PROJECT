"""
Simple Data Collection Agent for Viva Demo
Collects market data from multiple sources and stores in database
"""
import asyncio
import sqlite3
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from core.agents.agent_sdk.activity_log import should_trace, activity_log, safe_redact, generate_trace_id
except Exception:
    should_trace = lambda: False
    activity_log = None
    def safe_redact(x): return x
    def generate_trace_id(): return ""

try:
    from core.events.journal import write_event
except Exception:
    def write_event(topic: str, payload: Dict[str, Any]) -> None: pass

class DataCollectionAgent:
    """
    Minimal Data Collection Agent for demo.
    
    Simulates collecting data from multiple sources:
    - Mock web scraping
    - API data fetching  
    - Market trend analysis
    - Competitive pricing data
    """
    
    def __init__(self):
        root = Path(__file__).resolve().parents[3]
        self.app_db = root / "app" / "data.db"
        self.market_db = root / "data" / "market.db"
        
        # Mock data sources
        self.mock_sources = [
            "daraz.lk",
            "kapruka.com", 
            "ikman.lk",
            "dealz.lk",
            "techcity.lk"
        ]
    
    async def collect_market_data(self, sku: str, sources: Optional[List[str]] = None, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Collect market data for a product from multiple sources"""
        local_trace = trace_id or generate_trace_id()
        start_time = datetime.now()
        
        # Log start
        try:
            if should_trace():
                activity_log.log(
                    agent="DataCollector",
                    action="collect.start",
                    status="in_progress",
                    message=f"Collecting market data for {sku}",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "sku": sku,
                        "sources": sources or self.mock_sources[:3]
                    })
                )
        except Exception:
            pass
        
        # Get product info first
        product_info = await self._get_product_info(sku)
        if not product_info:
            return {"error": f"Product {sku} not found"}
        
        # Use provided sources or default mock sources
        target_sources = sources or self.mock_sources[:3]
        collected_data = []
        
        # Simulate data collection from each source
        for i, source in enumerate(target_sources):
            try:
                if should_trace():
                    activity_log.log(
                        agent="DataCollector",
                        action="collect.source",
                        status="in_progress",
                        message=f"Fetching from {source}",
                        details=safe_redact({
                            "trace_id": local_trace,
                            "source": source,
                            "progress": f"{i+1}/{len(target_sources)}"
                        })
                    )
            except Exception:
                pass
                
            # Simulate async data collection
            await asyncio.sleep(0.5)  # Simulate network delay
            
            # Generate mock competitive data
            base_price = product_info['current_price']
            variance = random.uniform(0.8, 1.2)  # ±20% variance
            mock_price = base_price * variance
            
            data_point = {
                'source': source,
                'product_name': product_info['title'],
                'sku': sku,
                'price': round(mock_price, 2),
                'currency': 'LKR',
                'availability': random.choice(['in_stock', 'limited', 'out_of_stock']),
                'timestamp': datetime.now().isoformat(),
                'confidence': random.uniform(0.7, 0.95)
            }
            
            collected_data.append(data_point)
        
        # Store collected data in database
        stored_count = await self._store_market_data(collected_data, local_trace)
        
        # Analyze and summarize
        analysis = await self._analyze_collected_data(collected_data, product_info)
        
        result = {
            'status': 'success',
            'sku': sku,
            'product_name': product_info['title'],
            'sources_checked': len(target_sources),
            'data_points_collected': len(collected_data),
            'data_points_stored': stored_count,
            'collection_duration_ms': int((datetime.now() - start_time).total_seconds() * 1000),
            'analysis': analysis,
            'raw_data': collected_data
        }
        
        # Log completion
        try:
            if should_trace():
                activity_log.log(
                    agent="DataCollector",
                    action="collect.done",
                    status="completed",
                    message=f"Collected {len(collected_data)} data points for {sku}",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "result_summary": {k: v for k, v in result.items() if k != 'raw_data'}
                    })
                )
        except Exception:
            pass
        
        return result
    
    async def _get_product_info(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get product info from database"""
        try:
            uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT sku, title, current_price, cost FROM product_catalog WHERE sku=? LIMIT 1",
                    (sku,)
                ).fetchone()
                
                if row:
                    return dict(row)
        except Exception:
            pass
        return None
    
    async def _store_market_data(self, data_points: List[Dict[str, Any]], trace_id: str) -> int:
        """Store collected data in market database"""
        stored_count = 0
        
        try:
            uri_market = f"file:{self.market_db.as_posix()}"
            with sqlite3.connect(uri_market, uri=False) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT,
                        product_name TEXT,
                        sku TEXT,
                        price REAL,
                        currency TEXT,
                        availability TEXT,
                        confidence REAL,
                        collected_at TEXT,
                        trace_id TEXT
                    )
                """)
                
                for data_point in data_points:
                    conn.execute("""
                        INSERT INTO market_data 
                        (source, product_name, sku, price, currency, availability, confidence, collected_at, trace_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data_point['source'],
                        data_point['product_name'],
                        data_point['sku'],
                        data_point['price'],
                        data_point['currency'],
                        data_point['availability'],
                        data_point['confidence'],
                        data_point['timestamp'],
                        trace_id
                    ))
                    stored_count += 1
                
                conn.commit()
        except Exception as e:
            print(f"Error storing data: {e}")
        
        return stored_count
    
    async def _analyze_collected_data(self, data_points: List[Dict[str, Any]], product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze collected market data"""
        if not data_points:
            return {"error": "No data to analyze"}
        
        prices = [dp['price'] for dp in data_points if dp['price'] > 0]
        our_price = product_info['current_price']
        
        if not prices:
            return {"error": "No valid prices found"}
        
        analysis = {
            'market_avg_price': round(sum(prices) / len(prices), 2),
            'market_min_price': min(prices),
            'market_max_price': max(prices),
            'our_price': our_price,
            'price_position': 'competitive',
            'recommendations': []
        }
        
        # Determine price position
        avg_price = analysis['market_avg_price']
        if our_price > avg_price * 1.1:
            analysis['price_position'] = 'high'
            analysis['recommendations'].append('Consider lowering price to be more competitive')
        elif our_price < avg_price * 0.9:
            analysis['price_position'] = 'low'  
            analysis['recommendations'].append('Price is very competitive, consider increasing for better margins')
        else:
            analysis['recommendations'].append('Price is well-positioned in the market')
        
        # Stock availability analysis
        in_stock_count = len([dp for dp in data_points if dp['availability'] == 'in_stock'])
        if in_stock_count < len(data_points) * 0.5:
            analysis['recommendations'].append('Limited market availability detected - opportunity for higher prices')
        
        return analysis

    async def collect_comprehensive_data(self, scope: str = "category", sku: Optional[str] = None, category: Optional[str] = None, sources: Optional[List[str]] = None, force_refresh: bool = False, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Collect comprehensive market data based on scope"""
        local_trace = trace_id or generate_trace_id()
        start_time = datetime.now()
        
        # Log start
        try:
            if should_trace():
                activity_log.log(
                    agent="DataCollector",
                    action="comprehensive.start",
                    status="in_progress",
                    message=f"Starting comprehensive data collection ({scope})",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "scope": scope,
                        "sku": sku,
                        "category": category,
                        "sources": sources or self.mock_sources
                    })
                )
        except Exception:
            pass
        
        results = []
        total_collected = 0
        
        if scope == "single_sku" and sku:
            # Collect for single product
            result = await self.collect_market_data(sku, sources, local_trace)
            results.append(result)
            total_collected = result.get('data_points_collected', 0)
            
        elif scope == "category":
            # Get products by category
            products = await self._get_products_by_category(category or "gaming")
            
            for i, product in enumerate(products[:5]):  # Limit to 5 for demo
                try:
                    if should_trace():
                        activity_log.log(
                            agent="DataCollector",
                            action="comprehensive.product",
                            status="in_progress",
                            message=f"Collecting for {product['title']}",
                            details=safe_redact({
                                "trace_id": local_trace,
                                "progress": f"{i+1}/{len(products)}",
                                "sku": product['sku']
                            })
                        )
                except Exception:
                    pass
                    
                result = await self.collect_market_data(product['sku'], sources, local_trace)
                results.append(result)
                total_collected += result.get('data_points_collected', 0)
                
        elif scope == "all_products":
            # Get all products (limited for demo)
            products = await self._get_all_products(limit=10)
            
            for i, product in enumerate(products):
                try:
                    if should_trace():
                        activity_log.log(
                            agent="DataCollector",
                            action="comprehensive.product",
                            status="in_progress",  
                            message=f"Collecting for {product['title']}",
                            details=safe_redact({
                                "trace_id": local_trace,
                                "progress": f"{i+1}/{len(products)}",
                                "sku": product['sku']
                            })
                        )
                except Exception:
                    pass
                    
                result = await self.collect_market_data(product['sku'], sources, local_trace)
                results.append(result)
                total_collected += result.get('data_points_collected', 0)
        
        # Create comprehensive summary
        summary = {
            'status': 'success',
            'scope': scope,
            'products_processed': len(results),
            'total_data_points': total_collected,
            'sources_used': sources or self.mock_sources,
            'collection_duration_ms': int((datetime.now() - start_time).total_seconds() * 1000),
            'results': results,
            'agent': 'DataCollectionAgent',
            'trace_id': local_trace
        }
        
        # Log completion
        try:
            if should_trace():
                activity_log.log(
                    agent="DataCollector",
                    action="comprehensive.done",
                    status="completed",
                    message=f"Comprehensive collection complete: {total_collected} data points from {len(results)} products",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "summary": {k: v for k, v in summary.items() if k != 'results'}
                    })
                )
        except Exception:
            pass
        
        return summary

    async def _get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products filtered by category"""
        try:
            uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                # Simple category matching (case insensitive)
                rows = conn.execute("""
                    SELECT sku, title, current_price, cost
                    FROM product_catalog 
                    WHERE LOWER(title) LIKE LOWER(?)
                    OR LOWER(category) LIKE LOWER(?)
                    ORDER BY current_price DESC
                    LIMIT 10
                """, (f'%{category}%', f'%{category}%')).fetchall()
                
                return [dict(row) for row in rows]
        except Exception:
            return []

    async def _get_all_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all products (limited)"""
        try:
            uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                rows = conn.execute("""
                    SELECT sku, title, current_price, cost
                    FROM product_catalog 
                    ORDER BY current_price DESC
                    LIMIT ?
                """, (limit,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception:
            return []

    async def get_collection_summary(self) -> Dict[str, Any]:
        """Get summary of recent data collection activities"""
        try:
            uri_market = f"file:{self.market_db.as_posix()}?mode=ro"
            with sqlite3.connect(uri_market, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get recent collection stats
                recent_data = conn.execute("""
                    SELECT COUNT(*) as total_records,
                           COUNT(DISTINCT sku) as unique_products,
                           COUNT(DISTINCT source) as unique_sources,
                           MAX(collected_at) as latest_collection
                    FROM market_data 
                    WHERE collected_at > datetime('now', '-24 hours')
                """).fetchone()
                
                # Get top collected products
                top_products = conn.execute("""
                    SELECT sku, product_name, COUNT(*) as collection_count,
                           AVG(price) as avg_market_price
                    FROM market_data 
                    WHERE collected_at > datetime('now', '-24 hours')
                    GROUP BY sku, product_name
                    ORDER BY collection_count DESC
                    LIMIT 5
                """).fetchall()
                
                return {
                    'recent_stats': dict(recent_data) if recent_data else {},
                    'top_products': [dict(row) for row in top_products],
                    'status': 'active'
                }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }

# Singleton instance
_data_collector = None

def get_data_collector() -> DataCollectionAgent:
    """Get or create the data collector singleton"""
    global _data_collector
    if _data_collector is None:
        _data_collector = DataCollectionAgent()
    return _data_collector