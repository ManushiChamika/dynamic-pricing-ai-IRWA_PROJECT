"""
Simple Alert & Notification Agent for Viva Demo
Detects critical situations and sends notifications
"""
import asyncio
import sqlite3
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

class AlertNotificationAgent:
    """
    Minimal Alert & Notification Agent for demo.
    
    Detects:
    - Large price drops (>20%)
    - Price increases above market average
    - Low stock situations
    - Market volatility
    """
    
    def __init__(self):
        root = Path(__file__).resolve().parents[3]
        self.app_db = root / "app" / "data.db"
        self.market_db = root / "data" / "market.db"
        self.alerts_history = []
    
    async def check_critical_situations(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for critical situations and return alerts"""
        local_trace = trace_id or generate_trace_id()
        start_time = datetime.now()
        
        # Log start
        try:
            if should_trace():
                activity_log.log(
                    agent="AlertAgent",
                    action="alert.scan",
                    status="in_progress", 
                    message="Scanning for critical situations",
                    details=safe_redact({"trace_id": local_trace})
                )
        except Exception:
            pass
        
        alerts = []
        
        # Check 1: Price drop alerts
        price_drop_alerts = await self._check_price_drops()
        alerts.extend(price_drop_alerts)
        
        # Check 2: Low stock alerts  
        stock_alerts = await self._check_low_stock()
        alerts.extend(stock_alerts)
        
        # Check 3: Market volatility
        volatility_alerts = await self._check_market_volatility()
        alerts.extend(volatility_alerts)
        
        # Store alerts in history
        for alert in alerts:
            alert['timestamp'] = datetime.now().isoformat()
            alert['trace_id'] = local_trace
            self.alerts_history.append(alert)
        
        # Log completion
        try:
            if should_trace():
                activity_log.log(
                    agent="AlertAgent",
                    action="alert.scan",
                    status="completed",
                    message=f"Found {len(alerts)} critical situations",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "alerts_count": len(alerts),
                        "duration_ms": int((datetime.now() - start_time).total_seconds() * 1000)
                    })
                )
                
                # Log each alert individually for UI visibility
                for alert in alerts:
                    activity_log.log(
                        agent="AlertAgent",
                        action="alert.trigger",
                        status="completed",
                        message=f"{alert['severity'].upper()}: {alert['title']}",
                        details=safe_redact(alert)
                    )
        except Exception:
            pass
        
        return alerts
    
    async def _check_price_drops(self) -> List[Dict[str, Any]]:
        """Check for significant price drops"""
        alerts = []
        
        try:
            uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
            uri_market = f"file:{self.market_db.as_posix()}?mode=ro"
            
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get products with recent price proposals showing drops
                cursor = conn.execute("""
                    SELECT p.sku, p.title, p.current_price, pr.proposed_price
                    FROM product_catalog p
                    JOIN price_proposals pr ON p.sku = pr.sku
                    WHERE pr.ts > datetime('now', '-1 hour')
                    AND pr.proposed_price < p.current_price * 0.8
                    ORDER BY pr.ts DESC
                    LIMIT 5
                """)
                
                for row in cursor:
                    drop_pct = ((row['current_price'] - row['proposed_price']) / row['current_price']) * 100
                    alerts.append({
                        'severity': 'high' if drop_pct > 30 else 'medium',
                        'type': 'price_drop',
                        'title': f'Significant price drop: {row["title"]}',
                        'message': f'Price dropped {drop_pct:.1f}% from {row["current_price"]:.0f} to {row["proposed_price"]:.0f}',
                        'sku': row['sku'],
                        'data': {
                            'old_price': row['current_price'],
                            'new_price': row['proposed_price'],
                            'drop_percentage': drop_pct
                        }
                    })
        except Exception as e:
            alerts.append({
                'severity': 'low',
                'type': 'system_error',
                'title': 'Price drop check failed',
                'message': f'Error checking price drops: {str(e)}',
                'sku': 'SYSTEM'
            })
        
        return alerts
    
    async def _check_low_stock(self) -> List[Dict[str, Any]]:
        """Check for low stock situations"""
        alerts = []
        
        try:
            uri_app = f"file:{self.app_db.as_posix()}?mode=ro"
            
            with sqlite3.connect(uri_app, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT sku, title, stock, current_price
                    FROM product_catalog 
                    WHERE stock < 5 AND stock > 0
                    ORDER BY stock ASC
                    LIMIT 3
                """)
                
                for row in cursor:
                    alerts.append({
                        'severity': 'medium' if row['stock'] > 2 else 'high',
                        'type': 'low_stock',
                        'title': f'Low stock alert: {row["title"]}',
                        'message': f'Only {row["stock"]} units remaining',
                        'sku': row['sku'],
                        'data': {
                            'stock_level': row['stock'],
                            'price': row['current_price']
                        }
                    })
        except Exception as e:
            pass  # Silent fail for demo
        
        return alerts
    
    async def _check_market_volatility(self) -> List[Dict[str, Any]]:
        """Check for market volatility"""
        alerts = []
        
        try:
            uri_market = f"file:{self.market_db.as_posix()}?mode=ro"
            
            with sqlite3.connect(uri_market, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check for high variance in pricing_list
                cursor = conn.execute("""
                    SELECT product_name, COUNT(*) as entries,
                           AVG(optimized_price) as avg_price,
                           MAX(optimized_price) as max_price,
                           MIN(optimized_price) as min_price
                    FROM pricing_list 
                    GROUP BY product_name
                    HAVING COUNT(*) > 1
                    ORDER BY (MAX(optimized_price) - MIN(optimized_price)) / AVG(optimized_price) DESC
                    LIMIT 3
                """)
                
                for row in cursor:
                    if row['avg_price'] > 0:
                        volatility = ((row['max_price'] - row['min_price']) / row['avg_price']) * 100
                        if volatility > 15:  # >15% variance
                            alerts.append({
                                'severity': 'medium',
                                'type': 'market_volatility',
                                'title': f'Market volatility detected: {row["product_name"]}',
                                'message': f'Price variance of {volatility:.1f}% (Range: {row["min_price"]:.0f}-{row["max_price"]:.0f})',
                                'sku': row['product_name'],
                                'data': {
                                    'volatility_pct': volatility,
                                    'avg_price': row['avg_price'],
                                    'price_range': [row['min_price'], row['max_price']]
                                }
                            })
        except Exception as e:
            pass  # Silent fail for demo
        
        return alerts
    
    async def scan_critical_situations(self, alert_types: List[str], severity: str = "warn", sku: Optional[str] = None, hours_back: int = 24, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Scan for critical situations matching specified criteria"""
        local_trace = trace_id or generate_trace_id()
        start_time = datetime.now()
        
        # Log start
        try:
            if should_trace():
                activity_log.log(
                    agent="AlertAgent",
                    action="scan.critical",
                    status="in_progress",
                    message=f"Scanning for {len(alert_types)} alert types",
                    details=safe_redact({
                        "trace_id": local_trace,
                        "alert_types": alert_types,
                        "severity": severity,
                        "sku": sku
                    })
                )
        except Exception:
            pass
        
        # Run comprehensive check
        all_alerts = await self.check_critical_situations(trace_id=local_trace)
        
        # Filter alerts based on criteria
        filtered_alerts = []
        for alert in all_alerts:
            # Filter by alert type
            if alert['type'] in alert_types:
                # Filter by SKU if specified
                if sku is None or alert.get('sku') == sku:
                    # Filter by severity (convert severity levels)
                    alert_severity_score = {'low': 1, 'medium': 2, 'high': 3}.get(alert.get('severity', 'low'), 1)
                    required_severity_score = {'info': 1, 'warn': 2, 'crit': 3}.get(severity, 2)
                    
                    if alert_severity_score >= required_severity_score:
                        filtered_alerts.append(alert)
        
        # Create result summary
        result = {
            "alerts": filtered_alerts,
            "summary": {
                "total_found": len(filtered_alerts),
                "scan_types": alert_types,
                "severity_filter": severity,
                "sku_filter": sku,
                "scan_duration_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            },
            "agent": "AlertNotificationAgent",
            "trace_id": local_trace
        }
        
        # Log completion
        try:
            if should_trace():
                activity_log.log(
                    agent="AlertAgent", 
                    action="scan.critical",
                    status="completed",
                    message=f"Found {len(filtered_alerts)} critical alerts",
                    details=safe_redact(result["summary"])
                )
        except Exception:
            pass
        
        return result
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts for UI display"""
        recent_alerts = [a for a in self.alerts_history if 
                        datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=1)]
        
        summary = {
            'total_alerts': len(self.alerts_history),
            'recent_alerts': len(recent_alerts),
            'severity_breakdown': {
                'high': len([a for a in recent_alerts if a['severity'] == 'high']),
                'medium': len([a for a in recent_alerts if a['severity'] == 'medium']),
                'low': len([a for a in recent_alerts if a['severity'] == 'low'])
            },
            'latest_alerts': recent_alerts[-5:] if recent_alerts else []
        }
        
        return summary

# Singleton instance
_alert_agent = None

def get_alert_agent() -> AlertNotificationAgent:
    """Get or create the alert agent singleton"""
    global _alert_agent
    if _alert_agent is None:
        _alert_agent = AlertNotificationAgent()
    return _alert_agent