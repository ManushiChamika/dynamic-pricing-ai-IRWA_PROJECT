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

try:
    from .performance_monitor import (
        PerformanceMonitor,
        AlertThresholds,
        PerformanceAlert
    )
    _has_performance_monitor = True
except ImportError:
    _has_performance_monitor = False

__all__ = [
    'MetricsCalculator',
    'PricingAccuracyMetrics', 
    'SystemPerformanceMetrics',
    'BusinessImpactMetrics',
    'EvaluationEngine',
    'EvaluationSession',
    'ABTestFramework'
]

if _has_performance_monitor:
    __all__.extend([
        'PerformanceMonitor',
        'AlertThresholds',
        'PerformanceAlert'
    ])