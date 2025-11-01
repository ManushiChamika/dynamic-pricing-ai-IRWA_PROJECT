"""
Performance Monitor for Dynamic Pricing AI System

This module provides real-time performance monitoring for IRWA compliance:
- Continuous performance tracking with configurable intervals
- Alert system with customizable thresholds
- System health monitoring (CPU, memory, disk)
- Dashboard data integration
- Event callbacks for performance issues
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

from .metrics import MetricsCalculator, SystemPerformanceMetrics


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertThresholds:
    """Configurable alert thresholds for performance monitoring"""
    # Pricing accuracy thresholds
    max_pricing_error_percent: float = 10.0
    min_precision_score: float = 75.0
    
    # System performance thresholds
    max_response_time_ms: float = 300.0
    max_data_freshness_minutes: float = 15.0
    min_availability_percent: float = 95.0
    max_memory_usage_percent: float = 85.0
    max_cpu_usage_percent: float = 80.0
    max_disk_usage_percent: float = 90.0
    max_error_rate_percent: float = 2.0
    
    # Business impact thresholds
    min_revenue_impact_percent: float = 5.0
    min_margin_improvement_percent: float = 2.0
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class PerformanceAlert:
    """Represents a performance alert"""
    alert_id: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'severity': self.severity.value,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None
        }


@dataclass
class SystemHealthSnapshot:
    """System health snapshot for monitoring"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io_bytes: int
    disk_io_bytes: int
    active_connections: int
    process_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_percent': self.memory_usage_percent,
            'disk_usage_percent': self.disk_usage_percent,
            'network_io_bytes': self.network_io_bytes,
            'disk_io_bytes': self.disk_io_bytes,
            'active_connections': self.active_connections,
            'process_count': self.process_count
        }


class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self, 
                 db_path: str = "app/data.db",
                 monitoring_interval: int = 60,
                 thresholds: Optional[AlertThresholds] = None):
        self.db_path = db_path
        self.monitoring_interval = monitoring_interval
        self.thresholds = thresholds or AlertThresholds()
        self.metrics_calculator = MetricsCalculator(db_path)
        
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        self.health_history: List[SystemHealthSnapshot] = []
        self.is_monitoring = False
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function to be called when alerts are triggered"""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous performance monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.logger.info("Starting performance monitoring")
        
        while self.is_monitoring:
            try:
                await self._monitor_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def stop_monitoring(self):
        """Stop continuous performance monitoring"""
        self.is_monitoring = False
        self.logger.info("Stopping performance monitoring")
    
    async def _monitor_cycle(self):
        """Execute one monitoring cycle"""
        # Collect system health snapshot
        health_snapshot = self._collect_system_health()
        self.health_history.append(health_snapshot)
        
        # Keep only last 24 hours of history
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.health_history = [
            h for h in self.health_history 
            if h.timestamp > cutoff_time
        ]
        
        # Get performance metrics
        try:
            performance_metrics = await self.metrics_calculator.calculate_system_performance_metrics()
            pricing_metrics = await self.metrics_calculator.calculate_pricing_accuracy_metrics(1)  # Last hour
            
            # Check thresholds and generate alerts
            await self._check_performance_thresholds(performance_metrics)
            await self._check_pricing_thresholds(pricing_metrics)
            await self._check_system_health_thresholds(health_snapshot)
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
    
    def _collect_system_health(self) -> SystemHealthSnapshot:
        """Collect current system health metrics"""
        try:
            # Get system resource usage
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network and disk I/O
            net_io = psutil.net_io_counters()
            disk_io = psutil.disk_io_counters()
            
            return SystemHealthSnapshot(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk.percent if disk else 0.0,
                network_io_bytes=net_io.bytes_sent + net_io.bytes_recv if net_io else 0,
                disk_io_bytes=disk_io.read_bytes + disk_io.write_bytes if disk_io else 0,
                active_connections=len(psutil.net_connections()),
                process_count=len(psutil.pids())
            )
        except Exception as e:
            self.logger.error(f"Error collecting system health: {e}")
            return SystemHealthSnapshot(
                timestamp=datetime.now(),
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                network_io_bytes=0,
                disk_io_bytes=0,
                active_connections=0,
                process_count=0
            )
    
    async def _check_performance_thresholds(self, metrics: SystemPerformanceMetrics):
        """Check performance metrics against thresholds"""
        
        # Response time check
        if metrics.average_response_time_ms > self.thresholds.max_response_time_ms:
            await self._trigger_alert(
                "response_time",
                AlertSeverity.WARNING,
                metrics.average_response_time_ms,
                self.thresholds.max_response_time_ms,
                f"Response time {metrics.average_response_time_ms:.1f}ms exceeds threshold {self.thresholds.max_response_time_ms:.1f}ms"
            )
        else:
            await self._resolve_alert("response_time")
        
        # Data freshness check
        if metrics.data_freshness_minutes > self.thresholds.max_data_freshness_minutes:
            severity = AlertSeverity.CRITICAL if metrics.data_freshness_minutes > 60 else AlertSeverity.WARNING
            await self._trigger_alert(
                "data_freshness",
                severity,
                metrics.data_freshness_minutes,
                self.thresholds.max_data_freshness_minutes,
                f"Data freshness {metrics.data_freshness_minutes:.1f} minutes exceeds threshold {self.thresholds.max_data_freshness_minutes:.1f} minutes"
            )
        else:
            await self._resolve_alert("data_freshness")
        
        # Availability check
        if metrics.system_availability_percent < self.thresholds.min_availability_percent:
            await self._trigger_alert(
                "availability",
                AlertSeverity.CRITICAL,
                metrics.system_availability_percent,
                self.thresholds.min_availability_percent,
                f"System availability {metrics.system_availability_percent:.1f}% below threshold {self.thresholds.min_availability_percent:.1f}%"
            )
        else:
            await self._resolve_alert("availability")
        
        # Error rate check
        if metrics.error_rate_percent > self.thresholds.max_error_rate_percent:
            await self._trigger_alert(
                "error_rate",
                AlertSeverity.WARNING,
                metrics.error_rate_percent,
                self.thresholds.max_error_rate_percent,
                f"Error rate {metrics.error_rate_percent:.1f}% exceeds threshold {self.thresholds.max_error_rate_percent:.1f}%"
            )
        else:
            await self._resolve_alert("error_rate")
    
    async def _check_pricing_thresholds(self, metrics):
        """Check pricing accuracy metrics against thresholds"""
        
        # Pricing accuracy check
        if metrics.mean_absolute_percentage_error > self.thresholds.max_pricing_error_percent:
            await self._trigger_alert(
                "pricing_accuracy",
                AlertSeverity.WARNING,
                metrics.mean_absolute_percentage_error,
                self.thresholds.max_pricing_error_percent,
                f"Pricing error {metrics.mean_absolute_percentage_error:.1f}% exceeds threshold {self.thresholds.max_pricing_error_percent:.1f}%"
            )
        else:
            await self._resolve_alert("pricing_accuracy")
        
        # Precision score check
        if metrics.precision_score < self.thresholds.min_precision_score:
            await self._trigger_alert(
                "pricing_precision",
                AlertSeverity.WARNING,
                metrics.precision_score,
                self.thresholds.min_precision_score,
                f"Pricing precision {metrics.precision_score:.1f}% below threshold {self.thresholds.min_precision_score:.1f}%"
            )
        else:
            await self._resolve_alert("pricing_precision")
    
    async def _check_system_health_thresholds(self, health: SystemHealthSnapshot):
        """Check system health metrics against thresholds"""
        
        # CPU usage check
        if health.cpu_usage_percent > self.thresholds.max_cpu_usage_percent:
            severity = AlertSeverity.CRITICAL if health.cpu_usage_percent > 95 else AlertSeverity.WARNING
            await self._trigger_alert(
                "cpu_usage",
                severity,
                health.cpu_usage_percent,
                self.thresholds.max_cpu_usage_percent,
                f"CPU usage {health.cpu_usage_percent:.1f}% exceeds threshold {self.thresholds.max_cpu_usage_percent:.1f}%"
            )
        else:
            await self._resolve_alert("cpu_usage")
        
        # Memory usage check
        if health.memory_usage_percent > self.thresholds.max_memory_usage_percent:
            severity = AlertSeverity.CRITICAL if health.memory_usage_percent > 95 else AlertSeverity.WARNING
            await self._trigger_alert(
                "memory_usage",
                severity,
                health.memory_usage_percent,
                self.thresholds.max_memory_usage_percent,
                f"Memory usage {health.memory_usage_percent:.1f}% exceeds threshold {self.thresholds.max_memory_usage_percent:.1f}%"
            )
        else:
            await self._resolve_alert("memory_usage")
        
        # Disk usage check
        if health.disk_usage_percent > self.thresholds.max_disk_usage_percent:
            severity = AlertSeverity.CRITICAL if health.disk_usage_percent > 95 else AlertSeverity.WARNING
            await self._trigger_alert(
                "disk_usage",
                severity,
                health.disk_usage_percent,
                self.thresholds.max_disk_usage_percent,
                f"Disk usage {health.disk_usage_percent:.1f}% exceeds threshold {self.thresholds.max_disk_usage_percent:.1f}%"
            )
        else:
            await self._resolve_alert("disk_usage")
    
    async def _trigger_alert(self, 
                           metric_name: str,
                           severity: AlertSeverity,
                           current_value: float,
                           threshold_value: float,
                           message: str):
        """Trigger a performance alert"""
        
        alert_id = f"{metric_name}_{int(time.time())}"
        
        # Check if we already have an active alert for this metric
        existing_alert_key = None
        for key, alert in self.active_alerts.items():
            if alert.metric_name == metric_name and not alert.resolved:
                existing_alert_key = key
                break
        
        if existing_alert_key:
            # Update existing alert
            self.active_alerts[existing_alert_key].current_value = current_value
            self.active_alerts[existing_alert_key].severity = severity
            self.active_alerts[existing_alert_key].message = message
            self.active_alerts[existing_alert_key].timestamp = datetime.now()
        else:
            # Create new alert
            alert = PerformanceAlert(
                alert_id=alert_id,
                severity=severity,
                metric_name=metric_name,
                current_value=current_value,
                threshold_value=threshold_value,
                message=message,
                timestamp=datetime.now()
            )
            
            self.active_alerts[alert_id] = alert
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.warning(f"Alert triggered: {message}")
            
            # Store alert in database
            await self._store_alert(alert)
    
    async def _resolve_alert(self, metric_name: str):
        """Resolve any active alerts for the given metric"""
        
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.metric_name == metric_name and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.now()
                
                self.logger.info(f"Alert resolved: {alert.message}")
                
                # Update alert in database
                await self._store_alert(alert)
    
    async def _store_alert(self, alert: PerformanceAlert):
        """Store alert in database"""
        import aiosqlite
        
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO evaluation_metrics (metric_type, metric_data, session_id)
                    VALUES (?, ?, ?)
                """, ("performance_alert", json.dumps(alert.to_dict()), alert.alert_id))
                await conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing alert: {e}")
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[PerformanceAlert]:
        """Get alert history for the specified number of hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.active_alerts.values()
            if alert.timestamp > cutoff_time
        ]
    
    def get_system_health_trends(self, hours: int = 6) -> Dict[str, List[float]]:
        """Get system health trends for dashboard display"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_health = [
            h for h in self.health_history
            if h.timestamp > cutoff_time
        ]
        
        if not recent_health:
            return {
                'timestamps': [],
                'cpu_usage': [],
                'memory_usage': [],
                'disk_usage': []
            }
        
        return {
            'timestamps': [h.timestamp.isoformat() for h in recent_health],
            'cpu_usage': [h.cpu_usage_percent for h in recent_health],
            'memory_usage': [h.memory_usage_percent for h in recent_health],
            'disk_usage': [h.disk_usage_percent for h in recent_health]
        }
    
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance data for dashboard"""
        active_alerts = self.get_active_alerts()
        health_trends = self.get_system_health_trends()
        
        # Calculate alert counts by severity
        alert_counts = {
            'critical': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            'warning': len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
            'info': len([a for a in active_alerts if a.severity == AlertSeverity.INFO])
        }
        
        # Get latest system health
        latest_health = self.health_history[-1] if self.health_history else None
        
        return {
            'monitoring_status': 'active' if self.is_monitoring else 'inactive',
            'alert_counts': alert_counts,
            'active_alerts': [alert.to_dict() for alert in active_alerts],
            'health_trends': health_trends,
            'latest_health': latest_health.to_dict() if latest_health else None,
            'thresholds': self.thresholds.to_dict(),
            'monitoring_interval': self.monitoring_interval
        }
    
    async def update_thresholds(self, new_thresholds: AlertThresholds):
        """Update alert thresholds"""
        self.thresholds = new_thresholds
        self.logger.info("Alert thresholds updated")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for reporting"""
        try:
            performance_metrics = await self.metrics_calculator.calculate_system_performance_metrics()
            active_alerts = self.get_active_alerts()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system_performance': performance_metrics.to_dict(),
                'active_alert_count': len(active_alerts),
                'critical_alerts': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                'monitoring_status': 'active' if self.is_monitoring else 'inactive',
                'health_score': self._calculate_health_score(performance_metrics, active_alerts)
            }
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _calculate_health_score(self, metrics: SystemPerformanceMetrics, alerts: List[PerformanceAlert]) -> float:
        """Calculate overall system health score (0-100)"""
        base_score = 100.0
        
        # Deduct for performance issues
        if metrics.average_response_time_ms > 200:
            base_score -= 10
        if metrics.data_freshness_minutes > 10:
            base_score -= 15
        if metrics.system_availability_percent < 99:
            base_score -= 20
        if metrics.error_rate_percent > 1:
            base_score -= 10
        
        # Deduct for active alerts
        for alert in alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                base_score -= 25
            elif alert.severity == AlertSeverity.WARNING:
                base_score -= 10
            elif alert.severity == AlertSeverity.INFO:
                base_score -= 5
        
        return max(0.0, base_score)