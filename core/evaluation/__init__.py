"""
Evaluation Framework for Dynamic Pricing AI System

This module provides comprehensive evaluation capabilities for IRWA compliance:
- Pricing accuracy metrics and validation
- System performance monitoring and alerting  
- Business impact analysis and ROI calculation
- A/B testing framework for algorithm comparison
- Real-time monitoring with configurable thresholds
- Comprehensive reporting with insights and recommendations
"""

from .metrics import (
    MetricsCalculator,
    PricingAccuracyMetrics,
    SystemPerformanceMetrics,
    BusinessImpactMetrics
)

from .evaluation_engine import (
    EvaluationEngine,
    EvaluationSession,
    ABTestFramework
)

from .performance_monitor import (
    PerformanceMonitor,
    AlertThresholds,
    PerformanceAlert
)

from .evaluator import (
    DynamicPricingEvaluator,
    EvaluationReport,
    EvaluationConfig
)

__all__ = [
    'MetricsCalculator',
    'PricingAccuracyMetrics', 
    'SystemPerformanceMetrics',
    'BusinessImpactMetrics',
    'EvaluationEngine',
    'EvaluationSession',
    'ABTestFramework',
    'PerformanceMonitor',
    'AlertThresholds',
    'PerformanceAlert',
    'DynamicPricingEvaluator',
    'EvaluationReport',
    'EvaluationConfig'
]