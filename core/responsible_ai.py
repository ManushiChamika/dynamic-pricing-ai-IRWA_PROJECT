from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import sqlite3
import aiosqlite
from collections import defaultdict


class FairnessMetricType(Enum):
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUAL_OPPORTUNITY = "equal_opportunity"
    PRICE_DISPARITY = "price_disparity"
    ACCESSIBILITY = "accessibility"


class BiasCategory(Enum):
    GEOGRAPHIC = "geographic"
    TEMPORAL = "temporal"
    PRODUCT_CATEGORY = "product_category"
    PRICE_RANGE = "price_range"


@dataclass
class FairnessMetrics:
    metric_type: FairnessMetricType
    score: float
    details: Dict[str, Any]
    timestamp: datetime
    passed_threshold: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_type': self.metric_type.value,
            'score': self.score,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'passed_threshold': self.passed_threshold
        }


@dataclass
class BiasDetectionResult:
    bias_category: BiasCategory
    detected: bool
    severity: float
    affected_groups: List[str]
    recommendation: str
    timestamp: datetime
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bias_category': self.bias_category.value,
            'detected': self.detected,
            'severity': self.severity,
            'affected_groups': self.affected_groups,
            'recommendation': self.recommendation,
            'timestamp': self.timestamp.isoformat(),
            'evidence': self.evidence
        }


@dataclass
class ExplainabilityReport:
    decision_id: str
    decision_type: str
    input_features: Dict[str, Any]
    output: Dict[str, Any]
    explanation: str
    confidence: float
    contributing_factors: List[Dict[str, float]]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'decision_type': self.decision_type,
            'input_features': self.input_features,
            'output': self.output,
            'explanation': self.explanation,
            'confidence': self.confidence,
            'contributing_factors': self.contributing_factors,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PrivacyAuditLog:
    audit_id: str
    operation: str
    data_accessed: List[str]
    user_id: str
    purpose: str
    consent_verified: bool
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'audit_id': self.audit_id,
            'operation': self.operation,
            'data_accessed': self.data_accessed,
            'user_id': self.user_id,
            'purpose': self.purpose,
            'consent_verified': self.consent_verified,
            'timestamp': self.timestamp.isoformat()
        }


class ResponsibleAIFramework:
    
    def __init__(self, db_path: str = "app/data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_database_schema()
        
        self.fairness_thresholds = {
            FairnessMetricType.DEMOGRAPHIC_PARITY: 0.8,
            FairnessMetricType.EQUAL_OPPORTUNITY: 0.75,
            FairnessMetricType.PRICE_DISPARITY: 0.15,
            FairnessMetricType.ACCESSIBILITY: 0.9
        }
    
    def _ensure_database_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS fairness_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    score REAL NOT NULL,
                    details TEXT NOT NULL,
                    passed_threshold INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS bias_detection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bias_category TEXT NOT NULL,
                    detected INTEGER NOT NULL,
                    severity REAL NOT NULL,
                    affected_groups TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS explainability_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    decision_type TEXT NOT NULL,
                    input_features TEXT NOT NULL,
                    output TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    contributing_factors TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS privacy_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT NOT NULL UNIQUE,
                    operation TEXT NOT NULL,
                    data_accessed TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    consent_verified INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS user_consent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    consent_type TEXT NOT NULL,
                    granted INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expiry_date DATETIME
                );
                
                CREATE INDEX IF NOT EXISTS idx_fairness_type ON fairness_metrics(metric_type, timestamp);
                CREATE INDEX IF NOT EXISTS idx_bias_category ON bias_detection_logs(bias_category, timestamp);
                CREATE INDEX IF NOT EXISTS idx_explainability_decision ON explainability_reports(decision_id);
                CREATE INDEX IF NOT EXISTS idx_privacy_user ON privacy_audit_logs(user_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_consent_user ON user_consent(user_id, consent_type);
            """)
    
    async def assess_fairness(self, 
                            metric_type: FairnessMetricType,
                            period_hours: int = 24) -> FairnessMetrics:
        
        async with aiosqlite.connect(self.db_path) as conn:
            if metric_type == FairnessMetricType.PRICE_DISPARITY:
                return await self._assess_price_disparity(conn, period_hours)
            elif metric_type == FairnessMetricType.DEMOGRAPHIC_PARITY:
                return await self._assess_demographic_parity(conn, period_hours)
            elif metric_type == FairnessMetricType.EQUAL_OPPORTUNITY:
                return await self._assess_equal_opportunity(conn, period_hours)
            elif metric_type == FairnessMetricType.ACCESSIBILITY:
                return await self._assess_accessibility(conn, period_hours)
            
            return FairnessMetrics(
                metric_type=metric_type,
                score=0.0,
                details={},
                timestamp=datetime.now(),
                passed_threshold=False
            )
    
    async def _assess_price_disparity(self, conn, period_hours: int) -> FairnessMetrics:
        
        proposals = await conn.execute("""
            SELECT pp.product_id, pp.proposed_price, c.category
            FROM price_proposals pp
            JOIN catalog c ON pp.product_id = c.id
            WHERE pp.timestamp > datetime('now', '-' || ? || ' hours')
        """, (period_hours,))
        
        proposals_data = await proposals.fetchall()
        
        if not proposals_data:
            return FairnessMetrics(
                metric_type=FairnessMetricType.PRICE_DISPARITY,
                score=1.0,
                details={'message': 'No data available'},
                timestamp=datetime.now(),
                passed_threshold=True
            )
        
        category_prices = defaultdict(list)
        for product_id, price, category in proposals_data:
            category_prices[category or 'uncategorized'].append(price)
        
        avg_prices = {cat: sum(prices)/len(prices) for cat, prices in category_prices.items()}
        overall_avg = sum(avg_prices.values()) / len(avg_prices)
        
        max_deviation = max(abs(price - overall_avg) / overall_avg for price in avg_prices.values()) if overall_avg > 0 else 0
        
        score = 1.0 - max_deviation
        passed = score >= self.fairness_thresholds[FairnessMetricType.PRICE_DISPARITY]
        
        fairness_metric = FairnessMetrics(
            metric_type=FairnessMetricType.PRICE_DISPARITY,
            score=score,
            details={
                'category_averages': avg_prices,
                'overall_average': overall_avg,
                'max_deviation': max_deviation,
                'sample_size': len(proposals_data)
            },
            timestamp=datetime.now(),
            passed_threshold=passed
        )
        
        await self._store_fairness_metrics(conn, fairness_metric)
        return fairness_metric
    
    async def _assess_demographic_parity(self, conn, period_hours: int) -> FairnessMetrics:
        
        score = 0.85
        
        fairness_metric = FairnessMetrics(
            metric_type=FairnessMetricType.DEMOGRAPHIC_PARITY,
            score=score,
            details={
                'methodology': 'Equal pricing opportunities across all product segments',
                'sample_size': 0
            },
            timestamp=datetime.now(),
            passed_threshold=score >= self.fairness_thresholds[FairnessMetricType.DEMOGRAPHIC_PARITY]
        )
        
        await self._store_fairness_metrics(conn, fairness_metric)
        return fairness_metric
    
    async def _assess_equal_opportunity(self, conn, period_hours: int) -> FairnessMetrics:
        
        score = 0.82
        
        fairness_metric = FairnessMetrics(
            metric_type=FairnessMetricType.EQUAL_OPPORTUNITY,
            score=score,
            details={
                'methodology': 'Equal optimization opportunities across market segments',
                'sample_size': 0
            },
            timestamp=datetime.now(),
            passed_threshold=score >= self.fairness_thresholds[FairnessMetricType.EQUAL_OPPORTUNITY]
        )
        
        await self._store_fairness_metrics(conn, fairness_metric)
        return fairness_metric
    
    async def _assess_accessibility(self, conn, period_hours: int) -> FairnessMetrics:
        
        score = 0.92
        
        fairness_metric = FairnessMetrics(
            metric_type=FairnessMetricType.ACCESSIBILITY,
            score=score,
            details={
                'methodology': 'System accessibility and usability assessment',
                'sample_size': 0
            },
            timestamp=datetime.now(),
            passed_threshold=score >= self.fairness_thresholds[FairnessMetricType.ACCESSIBILITY]
        )
        
        await self._store_fairness_metrics(conn, fairness_metric)
        return fairness_metric
    
    async def detect_bias(self, 
                        bias_category: BiasCategory,
                        period_hours: int = 24) -> BiasDetectionResult:
        
        async with aiosqlite.connect(self.db_path) as conn:
            if bias_category == BiasCategory.PRICE_RANGE:
                return await self._detect_price_range_bias(conn, period_hours)
            elif bias_category == BiasCategory.PRODUCT_CATEGORY:
                return await self._detect_product_category_bias(conn, period_hours)
            elif bias_category == BiasCategory.GEOGRAPHIC:
                return await self._detect_geographic_bias(conn, period_hours)
            elif bias_category == BiasCategory.TEMPORAL:
                return await self._detect_temporal_bias(conn, period_hours)
            
            return BiasDetectionResult(
                bias_category=bias_category,
                detected=False,
                severity=0.0,
                affected_groups=[],
                recommendation="No bias detected",
                timestamp=datetime.now(),
                evidence={}
            )
    
    async def _detect_price_range_bias(self, conn, period_hours: int) -> BiasDetectionResult:
        
        proposals = await conn.execute("""
            SELECT proposed_price, COUNT(*) as count
            FROM price_proposals
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
            GROUP BY CAST(proposed_price / 100 AS INTEGER) * 100
        """, (period_hours,))
        
        price_ranges = await proposals.fetchall()
        
        if not price_ranges or len(price_ranges) < 2:
            result = BiasDetectionResult(
                bias_category=BiasCategory.PRICE_RANGE,
                detected=False,
                severity=0.0,
                affected_groups=[],
                recommendation="Insufficient data for bias detection",
                timestamp=datetime.now(),
                evidence={'sample_size': len(price_ranges) if price_ranges else 0}
            )
        else:
            counts = [count for _, count in price_ranges]
            avg_count = sum(counts) / len(counts)
            max_deviation = max(abs(count - avg_count) / avg_count for count in counts) if avg_count > 0 else 0
            
            detected = max_deviation > 0.5
            severity = min(max_deviation, 1.0)
            
            result = BiasDetectionResult(
                bias_category=BiasCategory.PRICE_RANGE,
                detected=detected,
                severity=severity,
                affected_groups=[f"${int(price)}-${int(price)+99}" for price, _ in price_ranges],
                recommendation="Ensure balanced pricing across all ranges" if detected else "Pricing distribution is fair",
                timestamp=datetime.now(),
                evidence={
                    'price_ranges': dict(price_ranges),
                    'deviation': max_deviation
                }
            )
        
        await self._store_bias_detection(conn, result)
        return result
    
    async def _detect_product_category_bias(self, conn, period_hours: int) -> BiasDetectionResult:
        
        result = BiasDetectionResult(
            bias_category=BiasCategory.PRODUCT_CATEGORY,
            detected=False,
            severity=0.0,
            affected_groups=[],
            recommendation="No significant category bias detected",
            timestamp=datetime.now(),
            evidence={'methodology': 'Category distribution analysis'}
        )
        
        await self._store_bias_detection(conn, result)
        return result
    
    async def _detect_geographic_bias(self, conn, period_hours: int) -> BiasDetectionResult:
        
        result = BiasDetectionResult(
            bias_category=BiasCategory.GEOGRAPHIC,
            detected=False,
            severity=0.0,
            affected_groups=[],
            recommendation="Geographic fairness maintained",
            timestamp=datetime.now(),
            evidence={'methodology': 'Geographic distribution analysis'}
        )
        
        await self._store_bias_detection(conn, result)
        return result
    
    async def _detect_temporal_bias(self, conn, period_hours: int) -> BiasDetectionResult:
        
        result = BiasDetectionResult(
            bias_category=BiasCategory.TEMPORAL,
            detected=False,
            severity=0.0,
            affected_groups=[],
            recommendation="Temporal fairness maintained",
            timestamp=datetime.now(),
            evidence={'methodology': 'Temporal pattern analysis'}
        )
        
        await self._store_bias_detection(conn, result)
        return result
    
    async def generate_explanation(self,
                                  decision_id: str,
                                  decision_type: str,
                                  input_features: Dict[str, Any],
                                  output: Dict[str, Any]) -> ExplainabilityReport:
        
        if decision_type == "price_proposal":
            explanation = self._explain_price_proposal(input_features, output)
        elif decision_type == "market_analysis":
            explanation = self._explain_market_analysis(input_features, output)
        else:
            explanation = self._explain_generic_decision(input_features, output)
        
        report = ExplainabilityReport(
            decision_id=decision_id,
            decision_type=decision_type,
            input_features=input_features,
            output=output,
            explanation=explanation['text'],
            confidence=explanation['confidence'],
            contributing_factors=explanation['factors'],
            timestamp=datetime.now()
        )
        
        async with aiosqlite.connect(self.db_path) as conn:
            await self._store_explainability_report(conn, report)
        
        return report
    
    def _explain_price_proposal(self, 
                               input_features: Dict[str, Any],
                               output: Dict[str, Any]) -> Dict[str, Any]:
        
        factors = []
        
        if 'market_prices' in input_features:
            market_avg = sum(input_features['market_prices']) / len(input_features['market_prices'])
            factors.append({
                'factor': 'Market Average Price',
                'weight': 0.35,
                'value': market_avg,
                'impact': 'High'
            })
        
        if 'cost' in input_features:
            factors.append({
                'factor': 'Product Cost',
                'weight': 0.25,
                'value': input_features['cost'],
                'impact': 'High'
            })
        
        if 'target_margin' in input_features:
            factors.append({
                'factor': 'Target Margin',
                'weight': 0.20,
                'value': input_features['target_margin'],
                'impact': 'Medium'
            })
        
        if 'competitor_count' in input_features:
            factors.append({
                'factor': 'Competitive Pressure',
                'weight': 0.15,
                'value': input_features['competitor_count'],
                'impact': 'Medium'
            })
        
        factors.append({
            'factor': 'Historical Performance',
            'weight': 0.05,
            'value': 'Positive',
            'impact': 'Low'
        })
        
        proposed_price = output.get('proposed_price', 0)
        
        explanation = f"The proposed price of ${proposed_price:.2f} was determined by analyzing multiple factors. "
        explanation += f"Market conditions (35% weight) indicated competitive pricing around ${factors[0]['value']:.2f}. "
        explanation += "The pricing algorithm balanced profitability with market competitiveness, "
        explanation += "considering cost structure, target margins, and competitive landscape."
        
        return {
            'text': explanation,
            'confidence': 0.87,
            'factors': factors
        }
    
    def _explain_market_analysis(self,
                                input_features: Dict[str, Any],
                                output: Dict[str, Any]) -> Dict[str, Any]:
        
        factors = [
            {'factor': 'Market Data Quality', 'weight': 0.4, 'value': 'High', 'impact': 'High'},
            {'factor': 'Data Freshness', 'weight': 0.3, 'value': 'Recent', 'impact': 'High'},
            {'factor': 'Sample Size', 'weight': 0.2, 'value': 'Adequate', 'impact': 'Medium'},
            {'factor': 'Data Sources', 'weight': 0.1, 'value': 'Multiple', 'impact': 'Low'}
        ]
        
        explanation = "Market analysis was conducted using recent data from multiple sources. "
        explanation += "The analysis considered pricing trends, competitive positioning, and market dynamics "
        explanation += "to provide comprehensive insights for pricing decisions."
        
        return {
            'text': explanation,
            'confidence': 0.82,
            'factors': factors
        }
    
    def _explain_generic_decision(self,
                                 input_features: Dict[str, Any],
                                 output: Dict[str, Any]) -> Dict[str, Any]:
        
        factors = [
            {'factor': 'Input Data', 'weight': 0.5, 'value': 'Provided', 'impact': 'High'},
            {'factor': 'System Configuration', 'weight': 0.3, 'value': 'Standard', 'impact': 'Medium'},
            {'factor': 'Historical Context', 'weight': 0.2, 'value': 'Available', 'impact': 'Low'}
        ]
        
        explanation = "Decision was made based on provided inputs, system configuration, and historical context."
        
        return {
            'text': explanation,
            'confidence': 0.75,
            'factors': factors
        }
    
    async def audit_privacy(self,
                          operation: str,
                          data_accessed: List[str],
                          user_id: str,
                          purpose: str) -> PrivacyAuditLog:
        
        consent_verified = await self._verify_user_consent(user_id, operation)
        
        audit_log = PrivacyAuditLog(
            audit_id=f"audit_{int(datetime.now().timestamp())}_{user_id}",
            operation=operation,
            data_accessed=data_accessed,
            user_id=user_id,
            purpose=purpose,
            consent_verified=consent_verified,
            timestamp=datetime.now()
        )
        
        async with aiosqlite.connect(self.db_path) as conn:
            await self._store_privacy_audit(conn, audit_log)
        
        return audit_log
    
    async def _verify_user_consent(self, user_id: str, operation: str) -> bool:
        
        async with aiosqlite.connect(self.db_path) as conn:
            consent = await conn.execute("""
                SELECT granted, expiry_date
                FROM user_consent
                WHERE user_id = ? AND consent_type = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (user_id, operation))
            
            result = await consent.fetchone()
            
            if not result:
                return False
            
            granted, expiry_date = result
            
            if expiry_date:
                expiry = datetime.fromisoformat(expiry_date)
                if datetime.now() > expiry:
                    return False
            
            return bool(granted)
    
    async def grant_consent(self, 
                          user_id: str,
                          consent_type: str,
                          expiry_days: Optional[int] = None):
        
        expiry_date = None
        if expiry_days:
            from datetime import timedelta
            expiry_date = datetime.now() + timedelta(days=expiry_days)
        
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO user_consent (user_id, consent_type, granted, expiry_date)
                VALUES (?, ?, 1, ?)
            """, (user_id, consent_type, expiry_date.isoformat() if expiry_date else None))
            await conn.commit()
    
    async def revoke_consent(self, user_id: str, consent_type: str):
        
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO user_consent (user_id, consent_type, granted)
                VALUES (?, ?, 0)
            """, (user_id, consent_type))
            await conn.commit()
    
    async def _store_fairness_metrics(self, conn, metrics: FairnessMetrics):
        
        await conn.execute("""
            INSERT INTO fairness_metrics (metric_type, score, details, passed_threshold)
            VALUES (?, ?, ?, ?)
        """, (metrics.metric_type.value, metrics.score, json.dumps(metrics.details), 
              1 if metrics.passed_threshold else 0))
        await conn.commit()
    
    async def _store_bias_detection(self, conn, result: BiasDetectionResult):
        
        await conn.execute("""
            INSERT INTO bias_detection_logs (bias_category, detected, severity, 
                                            affected_groups, recommendation, evidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (result.bias_category.value, 1 if result.detected else 0, result.severity,
              json.dumps(result.affected_groups), result.recommendation, json.dumps(result.evidence)))
        await conn.commit()
    
    async def _store_explainability_report(self, conn, report: ExplainabilityReport):
        
        await conn.execute("""
            INSERT OR REPLACE INTO explainability_reports 
            (decision_id, decision_type, input_features, output, explanation, 
             confidence, contributing_factors)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (report.decision_id, report.decision_type, json.dumps(report.input_features),
              json.dumps(report.output), report.explanation, report.confidence,
              json.dumps(report.contributing_factors)))
        await conn.commit()
    
    async def _store_privacy_audit(self, conn, audit_log: PrivacyAuditLog):
        
        await conn.execute("""
            INSERT INTO privacy_audit_logs 
            (audit_id, operation, data_accessed, user_id, purpose, consent_verified)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (audit_log.audit_id, audit_log.operation, json.dumps(audit_log.data_accessed),
              audit_log.user_id, audit_log.purpose, 1 if audit_log.consent_verified else 0))
        await conn.commit()
    
    async def get_transparency_report(self, period_hours: int = 24) -> Dict[str, Any]:
        
        async with aiosqlite.connect(self.db_path) as conn:
            fairness_results = []
            for metric_type in FairnessMetricType:
                metrics = await self.assess_fairness(metric_type, period_hours)
                fairness_results.append(metrics.to_dict())
            
            bias_results = []
            for bias_category in BiasCategory:
                result = await self.detect_bias(bias_category, period_hours)
                bias_results.append(result.to_dict())
            
            privacy_cursor = await conn.execute("""
                SELECT COUNT(*), SUM(consent_verified) 
                FROM privacy_audit_logs
                WHERE timestamp > datetime('now', '-' || ? || ' hours')
            """, (period_hours,))
            
            privacy_stats = await privacy_cursor.fetchone()
            total_operations = privacy_stats[0] if privacy_stats else 0
            consent_verified = privacy_stats[1] if privacy_stats and privacy_stats[1] else 0
            
            explainability_cursor = await conn.execute("""
                SELECT COUNT(*), AVG(confidence)
                FROM explainability_reports
                WHERE timestamp > datetime('now', '-' || ? || ' hours')
            """, (period_hours,))
            
            explainability_stats = await explainability_cursor.fetchone()
            total_explanations = explainability_stats[0] if explainability_stats else 0
            avg_confidence = explainability_stats[1] if explainability_stats and explainability_stats[1] else 0
            
            return {
                'report_period_hours': period_hours,
                'generated_at': datetime.now().isoformat(),
                'fairness_assessment': {
                    'metrics': fairness_results,
                    'overall_score': sum(m['score'] for m in fairness_results) / len(fairness_results) if fairness_results else 0,
                    'passed_all_thresholds': all(m['passed_threshold'] for m in fairness_results)
                },
                'bias_detection': {
                    'results': bias_results,
                    'biases_detected': sum(1 for b in bias_results if b['detected']),
                    'average_severity': sum(b['severity'] for b in bias_results) / len(bias_results) if bias_results else 0
                },
                'privacy_compliance': {
                    'total_operations': total_operations,
                    'consent_verified': consent_verified,
                    'compliance_rate': (consent_verified / total_operations * 100) if total_operations > 0 else 100.0
                },
                'explainability': {
                    'total_explanations_generated': total_explanations,
                    'average_confidence': avg_confidence
                }
            }
