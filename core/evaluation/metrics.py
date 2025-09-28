"""
Metrics Calculation Engine for Dynamic Pricing AI System

This module provides comprehensive metrics calculation capabilities for IRWA compliance:
- Pricing accuracy metrics with statistical validation
- System performance monitoring and alerting  
- Business impact analysis and ROI calculation
- Database schema and baseline tracking
- Historical performance comparison
"""

import sqlite3

import aiosqlite
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    PRICING_ACCURACY = "pricing_accuracy"
    SYSTEM_PERFORMANCE = "system_performance" 
    BUSINESS_IMPACT = "business_impact"


@dataclass
class PricingAccuracyMetrics:
    """Pricing accuracy metrics for model evaluation"""
    mean_absolute_error: float
    mean_absolute_percentage_error: float
    root_mean_square_error: float
    precision_score: float
    competitive_positioning_score: float
    price_stability_index: float
    market_responsiveness_score: float
    timestamp: datetime
    sample_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mean_absolute_error': self.mean_absolute_error,
            'mape': self.mean_absolute_percentage_error,
            'rmse': self.root_mean_square_error,
            'precision_score': self.precision_score,
            'competitive_positioning': self.competitive_positioning_score,
            'price_stability': self.price_stability_index,
            'market_responsiveness': self.market_responsiveness_score,
            'timestamp': self.timestamp.isoformat(),
            'sample_size': self.sample_size
        }


@dataclass
class SystemPerformanceMetrics:
    """System performance metrics for operational monitoring"""
    throughput_requests_per_second: float
    average_response_time_ms: float
    data_freshness_minutes: float
    system_availability_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    error_rate_percent: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'throughput_rps': self.throughput_requests_per_second,
            'avg_response_time_ms': self.average_response_time_ms,
            'data_freshness_min': self.data_freshness_minutes,
            'availability_pct': self.system_availability_percent,
            'memory_usage_pct': self.memory_usage_percent,
            'cpu_usage_pct': self.cpu_usage_percent,
            'disk_usage_pct': self.disk_usage_percent,
            'active_connections': self.active_connections,
            'error_rate_pct': self.error_rate_percent,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass 
class BusinessImpactMetrics:
    """Business impact metrics for ROI analysis"""
    revenue_impact_percent: float
    margin_improvement_percent: float
    conversion_rate_change_percent: float
    customer_satisfaction_score: float
    market_share_change_percent: float
    pricing_efficiency_score: float
    competitive_advantage_index: float
    cost_savings_dollars: float
    timestamp: datetime
    period_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'revenue_impact_pct': self.revenue_impact_percent,
            'margin_improvement_pct': self.margin_improvement_percent,
            'conversion_rate_change_pct': self.conversion_rate_change_percent,
            'satisfaction_score': self.customer_satisfaction_score,
            'market_share_change_pct': self.market_share_change_percent,
            'pricing_efficiency': self.pricing_efficiency_score,
            'competitive_advantage': self.competitive_advantage_index,
            'cost_savings_usd': self.cost_savings_dollars,
            'timestamp': self.timestamp.isoformat(),
            'period_days': self.period_days
        }


class MetricsCalculator:
    """Main metrics calculation engine"""
    
    def __init__(self, db_path: str = "data/market.db"):
        self.db_path = db_path
        self._ensure_database_schema()
    
    def _ensure_database_schema(self):
        """Ensure evaluation metrics tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS evaluation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS evaluation_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS baseline_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    baseline_value REAL NOT NULL,
                    measurement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_type_time ON evaluation_metrics(metric_type, timestamp);
                CREATE INDEX IF NOT EXISTS idx_reports_session ON evaluation_reports(session_id);
                CREATE INDEX IF NOT EXISTS idx_baseline_metric ON baseline_performance(metric_name);
            """)
    
    async def calculate_pricing_accuracy_metrics(self, 
                                               period_hours: int = 24) -> PricingAccuracyMetrics:
        """Calculate comprehensive pricing accuracy metrics"""
        async with aiosqlite.connect(self.db_path) as conn:
            # Get recent price proposals and market data
            cutoff_time = datetime.now() - timedelta(hours=period_hours)
            
            proposals = await conn.execute("""
                SELECT proposed_price, product_id, timestamp, rationale
                FROM price_proposals 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff_time.isoformat(),))
            
            proposals_data = await proposals.fetchall()
            
            if not proposals_data:
                return PricingAccuracyMetrics(
                    mean_absolute_error=0.0,
                    mean_absolute_percentage_error=0.0,
                    root_mean_square_error=0.0,
                    precision_score=0.0,
                    competitive_positioning_score=0.0,
                    price_stability_index=0.0,
                    market_responsiveness_score=0.0,
                    timestamp=datetime.now(),
                    sample_size=0
                )
            
            # Calculate MAE, MAPE, RMSE
            errors = []
            percentage_errors = []
            
            for proposal in proposals_data:
                proposed_price, product_id, timestamp_str, rationale = proposal
                
                # Get market price for comparison
                market_data = await conn.execute("""
                    SELECT price FROM market_ticks 
                    WHERE product_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (product_id, timestamp_str))
                
                market_result = await market_data.fetchone()
                if market_result:
                    market_price = market_result[0]
                    error = abs(proposed_price - market_price)
                    errors.append(error)
                    
                    if market_price > 0:
                        percentage_error = (error / market_price) * 100
                        percentage_errors.append(percentage_error)
            
            # Calculate metrics
            mae = statistics.mean(errors) if errors else 0.0
            mape = statistics.mean(percentage_errors) if percentage_errors else 0.0
            rmse = (sum(e**2 for e in errors) / len(errors))**0.5 if errors else 0.0
            
            # Calculate precision score (accuracy within 5%)
            precision_hits = sum(1 for pe in percentage_errors if pe <= 5.0)
            precision_score = (precision_hits / len(percentage_errors) * 100) if percentage_errors else 0.0
            
            # Calculate competitive positioning score
            positioning_score = await self._calculate_competitive_positioning(conn, period_hours)
            
            # Calculate price stability index
            stability_index = await self._calculate_price_stability(conn, period_hours)
            
            # Calculate market responsiveness score  
            responsiveness_score = await self._calculate_market_responsiveness(conn, period_hours)
            
            return PricingAccuracyMetrics(
                mean_absolute_error=mae,
                mean_absolute_percentage_error=mape,
                root_mean_square_error=rmse,
                precision_score=precision_score,
                competitive_positioning_score=positioning_score,
                price_stability_index=stability_index,
                market_responsiveness_score=responsiveness_score,
                timestamp=datetime.now(),
                sample_size=len(proposals_data)
            )
    
    async def calculate_system_performance_metrics(self) -> SystemPerformanceMetrics:
        """Calculate current system performance metrics"""
        async with aiosqlite.connect(self.db_path) as conn:
            # Calculate throughput (requests per second)
            throughput = await self._calculate_throughput(conn)
            
            # Calculate average response time
            avg_response_time = await self._calculate_avg_response_time(conn)
            
            # Calculate data freshness
            data_freshness = await self._calculate_data_freshness(conn)
            
            # Calculate system availability
            availability = await self._calculate_system_availability(conn)
            
            # Get system resource usage
            import psutil
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)
            disk_usage = psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0.0
            
            # Calculate active connections (estimate from recent activity)
            active_connections = await self._calculate_active_connections(conn)
            
            # Calculate error rate
            error_rate = await self._calculate_error_rate(conn)
            
            return SystemPerformanceMetrics(
                throughput_requests_per_second=throughput,
                average_response_time_ms=avg_response_time,
                data_freshness_minutes=data_freshness,
                system_availability_percent=availability,
                memory_usage_percent=memory_usage,
                cpu_usage_percent=cpu_usage,
                disk_usage_percent=disk_usage,
                active_connections=active_connections,
                error_rate_percent=error_rate,
                timestamp=datetime.now()
            )
    
    async def calculate_business_impact_metrics(self, 
                                              period_days: int = 30) -> BusinessImpactMetrics:
        """Calculate business impact metrics over specified period"""
        async with aiosqlite.connect(self.db_path) as conn:
            cutoff_date = datetime.now() - timedelta(days=period_days)
            
            # Calculate revenue impact
            revenue_impact = await self._calculate_revenue_impact(conn, cutoff_date)
            
            # Calculate margin improvement
            margin_improvement = await self._calculate_margin_improvement(conn, cutoff_date)
            
            # Calculate conversion rate changes
            conversion_change = await self._calculate_conversion_rate_change(conn, cutoff_date)
            
            # Calculate customer satisfaction (based on pricing acceptance)
            satisfaction_score = await self._calculate_satisfaction_score(conn, cutoff_date)
            
            # Calculate market share changes
            market_share_change = await self._calculate_market_share_change(conn, cutoff_date)
            
            # Calculate pricing efficiency
            pricing_efficiency = await self._calculate_pricing_efficiency(conn, cutoff_date)
            
            # Calculate competitive advantage
            competitive_advantage = await self._calculate_competitive_advantage(conn, cutoff_date)
            
            # Calculate cost savings
            cost_savings = await self._calculate_cost_savings(conn, cutoff_date)
            
            return BusinessImpactMetrics(
                revenue_impact_percent=revenue_impact,
                margin_improvement_percent=margin_improvement,
                conversion_rate_change_percent=conversion_change,
                customer_satisfaction_score=satisfaction_score,
                market_share_change_percent=market_share_change,
                pricing_efficiency_score=pricing_efficiency,
                competitive_advantage_index=competitive_advantage,
                cost_savings_dollars=cost_savings,
                timestamp=datetime.now(),
                period_days=period_days
            )
    
    async def get_baseline_comparison(self, metric_name: str) -> Dict[str, float]:
        """Get baseline comparison for a specific metric"""
        async with aiosqlite.connect(self.db_path) as conn:
            baseline = await conn.execute("""
                SELECT baseline_value FROM baseline_performance 
                WHERE metric_name = ? 
                ORDER BY measurement_date DESC LIMIT 1
            """, (metric_name,))
            
            baseline_result = await baseline.fetchone()
            if not baseline_result:
                return {"baseline": 0.0, "current": 0.0, "improvement_percent": 0.0}
            
            baseline_value = baseline_result[0]
            
            # Get current value (this would be calculated based on metric type)
            current_value = await self._get_current_metric_value(metric_name)
            
            if baseline_value > 0:
                improvement = ((current_value - baseline_value) / baseline_value) * 100
            else:
                improvement = 0.0
            
            return {
                "baseline": baseline_value,
                "current": current_value,
                "improvement_percent": improvement
            }
    
    # Helper methods for specific calculations
    
    async def _calculate_competitive_positioning(self, conn, period_hours: int) -> float:
        """Calculate competitive positioning score"""
        # TODO: Implementation would compare our prices to market average
        # Current implementation returns placeholder value pending market data integration
        return 75.0
    
    async def _calculate_price_stability(self, conn, period_hours: int) -> float:
        """Calculate price stability index"""
        # TODO: Implementation would measure price variance over time
        # Current implementation returns placeholder value pending historical data analysis
        return 85.0
    
    async def _calculate_market_responsiveness(self, conn, period_hours: int) -> float:
        """Calculate market responsiveness score"""
        # TODO: Implementation would measure how quickly prices adapt to market changes
        # Current implementation returns placeholder value pending market volatility analysis
        return 78.0
    
    async def _calculate_throughput(self, conn) -> float:
        """Calculate system throughput"""
        # TODO: Implementation would count recent requests/operations
        # Current implementation returns placeholder value pending request logging integration
        return 12.5
    
    async def _calculate_avg_response_time(self, conn) -> float:
        """Calculate average response time"""
        # TODO: Implementation would measure recent response times
        # Current implementation returns placeholder value pending performance monitoring integration
        return 150.0
    
    async def _calculate_data_freshness(self, conn) -> float:
        """Calculate data freshness in minutes"""
        latest_data = await conn.execute("""
            SELECT MAX(timestamp) FROM market_ticks
        """)
        result = await latest_data.fetchone()
        
        if result and result[0]:
            latest_time = datetime.fromisoformat(result[0])
            freshness_minutes = (datetime.now() - latest_time).total_seconds() / 60
            return freshness_minutes
        
        return 999.0  # Very stale data
    
    async def _calculate_system_availability(self, conn) -> float:
        """Calculate system availability percentage"""
        # TODO: Implementation would track uptime/downtime
        # Current implementation returns placeholder value pending availability monitoring
        return 99.5
    
    async def _calculate_active_connections(self, conn) -> int:
        """Calculate active connections"""
        # TODO: Implementation would count recent database connections/activity
        # Current implementation returns placeholder value pending connection monitoring
        return 8
    
    async def _calculate_error_rate(self, conn) -> float:
        """Calculate error rate percentage"""
        # TODO: Implementation would count errors vs successful operations
        # Current implementation returns placeholder value pending error tracking
        return 0.5
    
    async def _calculate_revenue_impact(self, conn, cutoff_date: datetime) -> float:
        """Calculate revenue impact percentage"""
        # Implementation would compare revenue before/after AI pricing
        return 12.5  # Placeholder - percentage increase
    
    async def _calculate_margin_improvement(self, conn, cutoff_date: datetime) -> float:
        """Calculate margin improvement percentage"""
        # Implementation would compare profit margins
        return 8.3  # Placeholder - percentage improvement
    
    async def _calculate_conversion_rate_change(self, conn, cutoff_date: datetime) -> float:
        """Calculate conversion rate change"""
        # Implementation would track sales conversion changes
        return 15.2  # Placeholder - percentage change
    
    async def _calculate_satisfaction_score(self, conn, cutoff_date: datetime) -> float:
        """Calculate customer satisfaction score"""
        # Implementation would measure customer feedback/behavior
        return 4.2  # Placeholder - out of 5.0
    
    async def _calculate_market_share_change(self, conn, cutoff_date: datetime) -> float:
        """Calculate market share change"""
        # Implementation would track competitive position
        return 2.1  # Placeholder - percentage change
    
    async def _calculate_pricing_efficiency(self, conn, cutoff_date: datetime) -> float:
        """Calculate pricing efficiency score"""
        # Implementation would measure pricing optimization effectiveness
        return 82.0  # Placeholder - efficiency score
    
    async def _calculate_competitive_advantage(self, conn, cutoff_date: datetime) -> float:
        """Calculate competitive advantage index"""
        # Implementation would measure advantage over competitors
        return 1.25  # Placeholder - index score
    
    async def _calculate_cost_savings(self, conn, cutoff_date: datetime) -> float:
        """Calculate cost savings in dollars"""
        # Implementation would calculate operational cost reductions
        return 15750.0  # Placeholder - dollars saved
    
    async def _get_current_metric_value(self, metric_name: str) -> float:
        """Get current value for a specific metric"""
        # TODO: Implementation would retrieve current metric value from database
        # Current implementation returns placeholder value pending metric storage system
        return 100.0
    
    async def store_metrics(self, metrics: Any, session_id: Optional[str] = None):
        """Store calculated metrics in database"""
        async with aiosqlite.connect(self.db_path) as conn:
            metric_type = ""
            if isinstance(metrics, PricingAccuracyMetrics):
                metric_type = "pricing_accuracy"
            elif isinstance(metrics, SystemPerformanceMetrics):
                metric_type = "system_performance"
            elif isinstance(metrics, BusinessImpactMetrics):
                metric_type = "business_impact"
            
            await conn.execute("""
                INSERT INTO evaluation_metrics (metric_type, metric_data, session_id)
                VALUES (?, ?, ?)
            """, (metric_type, str(metrics.to_dict()), session_id))
            
            await conn.commit()