"""
Evaluation Engine for Dynamic Pricing AI System

This module provides comprehensive evaluation orchestration for IRWA compliance:
- Complete system evaluation workflow
- A/B testing framework for algorithm comparison  
- Insights generation and analysis
- Structured reporting with recommendations
- Session tracking and benchmarking
"""

import json
import uuid
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .metrics import (
    MetricsCalculator,
    PricingAccuracyMetrics,
    SystemPerformanceMetrics,
    BusinessImpactMetrics
)


class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvaluationSession:
    """Represents an evaluation session"""
    session_id: str
    evaluation_type: str
    start_time: datetime
    end_time: Optional[datetime]
    status: EvaluationStatus
    metrics_collected: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'evaluation_type': self.evaluation_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'metrics_collected': self.metrics_collected,
            'insights': self.insights,
            'recommendations': self.recommendations
        }


@dataclass
class ABTestResult:
    """Results from A/B testing different pricing algorithms"""
    test_id: str
    algorithm_a: str
    algorithm_b: str
    sample_size_a: int
    sample_size_b: int
    metrics_a: Dict[str, float]
    metrics_b: Dict[str, float]
    statistical_significance: bool
    confidence_level: float
    winner: str
    improvement_percentage: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'algorithm_a': self.algorithm_a,
            'algorithm_b': self.algorithm_b,
            'sample_size_a': self.sample_size_a,
            'sample_size_b': self.sample_size_b,
            'metrics_a': self.metrics_a,
            'metrics_b': self.metrics_b,
            'statistical_significance': self.statistical_significance,
            'confidence_level': self.confidence_level,
            'winner': self.winner,
            'improvement_percentage': self.improvement_percentage,
            'timestamp': self.timestamp.isoformat()
        }


class ABTestFramework:
    """A/B testing framework for comparing pricing algorithms"""
    
    def __init__(self, metrics_calculator: MetricsCalculator):
        self.metrics_calculator = metrics_calculator
    
    async def run_ab_test(self,
                         algorithm_a: str,
                         algorithm_b: str,
                         test_duration_hours: int = 24,
                         confidence_level: float = 0.95) -> ABTestResult:
        """Run A/B test comparing two pricing algorithms"""
        
        test_id = str(uuid.uuid4())
        
        # Get metrics for both algorithms
        metrics_a = await self._get_algorithm_metrics(algorithm_a, test_duration_hours)
        metrics_b = await self._get_algorithm_metrics(algorithm_b, test_duration_hours)
        
        # Calculate statistical significance
        significance = self._calculate_statistical_significance(
            metrics_a, metrics_b, confidence_level
        )
        
        # Determine winner
        winner, improvement = self._determine_winner(metrics_a, metrics_b)
        
        return ABTestResult(
            test_id=test_id,
            algorithm_a=algorithm_a,
            algorithm_b=algorithm_b,
            sample_size_a=metrics_a.get('sample_size', 0),
            sample_size_b=metrics_b.get('sample_size', 0),
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            statistical_significance=significance,
            confidence_level=confidence_level,
            winner=winner,
            improvement_percentage=improvement,
            timestamp=datetime.now()
        )
    
    async def _get_algorithm_metrics(self, algorithm: str, hours: int) -> Dict[str, float]:
        """Get performance metrics for a specific algorithm"""
        # This would integrate with actual algorithm tracking
        # For now, return simulated metrics
        return {
            'accuracy': 85.2 if algorithm == 'A' else 87.1,
            'response_time': 150.0 if algorithm == 'A' else 145.0,
            'revenue_impact': 12.5 if algorithm == 'A' else 15.2,
            'sample_size': 1000
        }
    
    def _calculate_statistical_significance(self,
                                          metrics_a: Dict[str, float],
                                          metrics_b: Dict[str, float],
                                          confidence_level: float) -> bool:
        """Calculate if results are statistically significant"""
        # Simplified significance test
        # In practice, would use proper statistical tests
        sample_a = metrics_a.get('sample_size', 0)
        sample_b = metrics_b.get('sample_size', 0)
        
        # Require minimum sample size for significance
        return sample_a >= 100 and sample_b >= 100
    
    def _determine_winner(self,
                         metrics_a: Dict[str, float],
                         metrics_b: Dict[str, float]) -> Tuple[str, float]:
        """Determine winning algorithm and improvement percentage"""
        
        # Use revenue impact as primary metric
        revenue_a = metrics_a.get('revenue_impact', 0.0)
        revenue_b = metrics_b.get('revenue_impact', 0.0)
        
        if revenue_b > revenue_a:
            improvement = ((revenue_b - revenue_a) / revenue_a) * 100 if revenue_a > 0 else 0
            return 'B', improvement
        else:
            improvement = ((revenue_a - revenue_b) / revenue_b) * 100 if revenue_b > 0 else 0
            return 'A', improvement


class EvaluationEngine:
    """Main evaluation engine orchestrating comprehensive system assessment"""
    
    def __init__(self, db_path: str = "data/market.db"):
        self.metrics_calculator = MetricsCalculator(db_path)
        self.ab_framework = ABTestFramework(self.metrics_calculator)
        self.db_path = db_path
    
    async def run_comprehensive_evaluation(self,
                                         evaluation_type: str = "full_system",
                                         period_hours: int = 24) -> EvaluationSession:
        """Run comprehensive evaluation of the pricing system"""
        
        session_id = str(uuid.uuid4())
        session = EvaluationSession(
            session_id=session_id,
            evaluation_type=evaluation_type,
            start_time=datetime.now(),
            end_time=None,
            status=EvaluationStatus.RUNNING,
            metrics_collected={},
            insights=[],
            recommendations=[]
        )
        
        try:
            # Collect all metrics
            pricing_metrics = await self.metrics_calculator.calculate_pricing_accuracy_metrics(period_hours)
            performance_metrics = await self.metrics_calculator.calculate_system_performance_metrics()
            business_metrics = await self.metrics_calculator.calculate_business_impact_metrics(period_hours // 24)
            
            # Store metrics in session
            session.metrics_collected = {
                'pricing_accuracy': pricing_metrics.to_dict(),
                'system_performance': performance_metrics.to_dict(),
                'business_impact': business_metrics.to_dict()
            }
            
            # Generate insights
            session.insights = self._generate_insights(
                pricing_metrics, performance_metrics, business_metrics
            )
            
            # Generate recommendations
            session.recommendations = self._generate_recommendations(
                pricing_metrics, performance_metrics, business_metrics
            )
            
            # Mark as completed
            session.end_time = datetime.now()
            session.status = EvaluationStatus.COMPLETED
            
            # Store session results
            await self._store_evaluation_session(session)
            
        except Exception as e:
            session.status = EvaluationStatus.FAILED
            session.end_time = datetime.now()
            session.insights.append(f"Evaluation failed: {str(e)}")
        
        return session
    
    def _generate_insights(self,
                          pricing_metrics: PricingAccuracyMetrics,
                          performance_metrics: SystemPerformanceMetrics,
                          business_metrics: BusinessImpactMetrics) -> List[str]:
        """Generate analytical insights from collected metrics"""
        
        insights = []
        
        # Pricing accuracy insights
        if pricing_metrics.mean_absolute_percentage_error < 5.0:
            insights.append("Excellent pricing accuracy: MAPE below 5% indicates highly accurate predictions")
        elif pricing_metrics.mean_absolute_percentage_error < 10.0:
            insights.append("Good pricing accuracy: MAPE below 10% shows reliable pricing decisions")
        else:
            insights.append("Pricing accuracy needs improvement: MAPE above 10% suggests model refinement needed")
        
        if pricing_metrics.precision_score > 80.0:
            insights.append("High precision: Over 80% of prices are within 5% of market prices")
        elif pricing_metrics.precision_score > 60.0:
            insights.append("Moderate precision: 60-80% of prices are within acceptable range")
        else:
            insights.append("Low precision: Less than 60% of prices meet accuracy targets")
        
        # Performance insights
        if performance_metrics.data_freshness_minutes < 5.0:
            insights.append("Excellent data freshness: Market data updated within 5 minutes")
        elif performance_metrics.data_freshness_minutes < 15.0:
            insights.append("Good data freshness: Market data reasonably current")
        else:
            insights.append("Data freshness concern: Market data may be stale, affecting pricing accuracy")
        
        if performance_metrics.system_availability_percent > 99.0:
            insights.append("Outstanding system reliability: Over 99% uptime achieved")
        elif performance_metrics.system_availability_percent > 95.0:
            insights.append("Good system reliability: Over 95% uptime maintained")
        else:
            insights.append("System reliability issue: Uptime below 95% may impact business operations")
        
        # Business impact insights
        if business_metrics.revenue_impact_percent > 10.0:
            insights.append("Significant revenue impact: AI pricing driving substantial revenue growth")
        elif business_metrics.revenue_impact_percent > 5.0:
            insights.append("Positive revenue impact: AI pricing contributing to revenue growth")
        elif business_metrics.revenue_impact_percent > 0.0:
            insights.append("Modest revenue impact: AI pricing showing positive but limited impact")
        else:
            insights.append("Revenue impact concern: AI pricing not yet driving expected revenue growth")
        
        if business_metrics.margin_improvement_percent > 5.0:
            insights.append("Strong margin improvement: AI pricing effectively optimizing profitability")
        elif business_metrics.margin_improvement_percent > 2.0:
            insights.append("Moderate margin improvement: AI pricing positively impacting margins")
        else:
            insights.append("Limited margin improvement: Pricing strategy may need refinement")
        
        return insights
    
    def _generate_recommendations(self,
                                pricing_metrics: PricingAccuracyMetrics,
                                performance_metrics: SystemPerformanceMetrics,
                                business_metrics: BusinessImpactMetrics) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        
        recommendations = []
        
        # Pricing accuracy recommendations
        if pricing_metrics.mean_absolute_percentage_error > 10.0:
            recommendations.append("Retrain pricing model with recent market data to improve accuracy")
            recommendations.append("Consider ensemble methods or additional features to reduce prediction errors")
        
        if pricing_metrics.precision_score < 70.0:
            recommendations.append("Implement dynamic confidence intervals for pricing decisions")
            recommendations.append("Add market volatility adjustments to improve precision")
        
        if pricing_metrics.market_responsiveness_score < 75.0:
            recommendations.append("Increase data collection frequency to improve market responsiveness")
            recommendations.append("Implement real-time price adjustment mechanisms")
        
        # Performance recommendations
        if performance_metrics.data_freshness_minutes > 10.0:
            recommendations.append("Optimize data pipeline to reduce latency and improve freshness")
            recommendations.append("Implement automated data validation and quality checks")
        
        if performance_metrics.average_response_time_ms > 200.0:
            recommendations.append("Optimize pricing algorithm performance to reduce response time")
            recommendations.append("Consider caching strategies for frequently accessed data")
        
        if performance_metrics.system_availability_percent < 99.0:
            recommendations.append("Implement redundancy and failover mechanisms for higher availability")
            recommendations.append("Set up comprehensive monitoring and alerting for system health")
        
        # Business impact recommendations
        if business_metrics.revenue_impact_percent < 5.0:
            recommendations.append("Analyze pricing strategy effectiveness and adjust algorithms")
            recommendations.append("Conduct market analysis to identify optimization opportunities")
        
        if business_metrics.customer_satisfaction_score < 4.0:
            recommendations.append("Review pricing fairness and customer perception metrics")
            recommendations.append("Implement customer feedback loops for pricing strategy")
        
        if business_metrics.competitive_advantage_index < 1.1:
            recommendations.append("Enhance competitive intelligence and market positioning")
            recommendations.append("Develop unique value propositions beyond price competition")
        
        return recommendations
    
    async def _store_evaluation_session(self, session: EvaluationSession):
        """Store evaluation session results in database"""
        import aiosqlite
        
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO evaluation_reports (session_id, report_type, report_data)
                VALUES (?, ?, ?)
            """, (
                session.session_id,
                session.evaluation_type,
                json.dumps(session.to_dict())
            ))
            await conn.commit()
    
    async def get_evaluation_history(self, limit: int = 10) -> List[EvaluationSession]:
        """Get recent evaluation sessions"""
        import aiosqlite
        
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                SELECT report_data FROM evaluation_reports
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = await cursor.fetchall()
            sessions = []
            
            for row in results:
                try:
                    session_data = json.loads(row[0])
                    session = EvaluationSession(
                        session_id=session_data['session_id'],
                        evaluation_type=session_data['evaluation_type'],
                        start_time=datetime.fromisoformat(session_data['start_time']),
                        end_time=datetime.fromisoformat(session_data['end_time']) if session_data['end_time'] else None,
                        status=EvaluationStatus(session_data['status']),
                        metrics_collected=session_data['metrics_collected'],
                        insights=session_data['insights'],
                        recommendations=session_data['recommendations']
                    )
                    sessions.append(session)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
            
            return sessions
    
    async def generate_evaluation_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        import aiosqlite
        
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                SELECT report_data FROM evaluation_reports
                WHERE session_id = ?
            """, (session_id,))
            
            result = await cursor.fetchone()
            if not result:
                return {"error": "Session not found"}
            
            try:
                session_data = json.loads(result[0])
                
                # Calculate summary statistics
                metrics = session_data['metrics_collected']
                summary = self._generate_report_summary(metrics)
                
                return {
                    "session_id": session_id,
                    "evaluation_type": session_data['evaluation_type'],
                    "timestamp": session_data['start_time'],
                    "status": session_data['status'],
                    "summary": summary,
                    "detailed_metrics": metrics,
                    "insights": session_data['insights'],
                    "recommendations": session_data['recommendations'],
                    "overall_score": self._calculate_overall_score(metrics)
                }
            
            except (json.JSONDecodeError, KeyError):
                return {"error": "Invalid session data"}
    
    def _generate_report_summary(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Generate summary statistics for report"""
        summary = {}
        
        if 'pricing_accuracy' in metrics:
            pa = metrics['pricing_accuracy']
            summary['pricing_accuracy'] = f"MAPE: {pa.get('mape', 0):.1f}%, Precision: {pa.get('precision_score', 0):.1f}%"
        
        if 'system_performance' in metrics:
            sp = metrics['system_performance']
            summary['system_performance'] = f"Availability: {sp.get('availability_pct', 0):.1f}%, Response: {sp.get('avg_response_time_ms', 0):.0f}ms"
        
        if 'business_impact' in metrics:
            bi = metrics['business_impact']
            summary['business_impact'] = f"Revenue: +{bi.get('revenue_impact_pct', 0):.1f}%, Margin: +{bi.get('margin_improvement_pct', 0):.1f}%"
        
        return summary
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall system score (0-100)"""
        scores = []
        
        # Pricing accuracy score (0-100)
        if 'pricing_accuracy' in metrics:
            pa = metrics['pricing_accuracy']
            mape = pa.get('mape', 100)
            precision = pa.get('precision_score', 0)
            accuracy_score = max(0, 100 - mape * 2) * 0.6 + precision * 0.4
            scores.append(accuracy_score)
        
        # Performance score (0-100)
        if 'system_performance' in metrics:
            sp = metrics['system_performance']
            availability = sp.get('availability_pct', 0)
            response_time = sp.get('avg_response_time_ms', 1000)
            performance_score = availability * 0.7 + max(0, 100 - response_time / 10) * 0.3
            scores.append(performance_score)
        
        # Business impact score (0-100)
        if 'business_impact' in metrics:
            bi = metrics['business_impact']
            revenue = bi.get('revenue_impact_pct', 0)
            margin = bi.get('margin_improvement_pct', 0)
            business_score = min(100, revenue * 4 + margin * 6)
            scores.append(business_score)
        
        return sum(scores) / len(scores) if scores else 0.0