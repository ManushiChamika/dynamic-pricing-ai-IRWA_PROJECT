from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime

from core.responsible_ai import (
    ResponsibleAIFramework,
    FairnessMetricType,
    BiasCategory
)

router = APIRouter(prefix="/api/responsible-ai", tags=["Responsible AI"])

rai_framework = ResponsibleAIFramework()


@router.get("/fairness/{metric_type}")
async def assess_fairness(
    metric_type: str,
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    try:
        metric_enum = FairnessMetricType(metric_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric type. Must be one of: {[m.value for m in FairnessMetricType]}"
        )
    
    metrics = await rai_framework.assess_fairness(metric_enum, period_hours)
    return metrics.to_dict()


@router.get("/fairness")
async def assess_all_fairness(
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    results = {}
    for metric_type in FairnessMetricType:
        metrics = await rai_framework.assess_fairness(metric_type, period_hours)
        results[metric_type.value] = metrics.to_dict()
    
    overall_score = sum(m['score'] for m in results.values()) / len(results)
    passed_all = all(m['passed_threshold'] for m in results.values())
    
    return {
        'metrics': results,
        'overall_score': overall_score,
        'passed_all_thresholds': passed_all,
        'timestamp': datetime.now().isoformat()
    }


@router.get("/bias/{bias_category}")
async def detect_bias(
    bias_category: str,
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    try:
        category_enum = BiasCategory(bias_category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bias category. Must be one of: {[b.value for b in BiasCategory]}"
        )
    
    result = await rai_framework.detect_bias(category_enum, period_hours)
    return result.to_dict()


@router.get("/bias")
async def detect_all_bias(
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    results = {}
    for bias_category in BiasCategory:
        result = await rai_framework.detect_bias(bias_category, period_hours)
        results[bias_category.value] = result.to_dict()
    
    detected_count = sum(1 for r in results.values() if r['detected'])
    avg_severity = sum(r['severity'] for r in results.values()) / len(results) if results else 0
    
    return {
        'results': results,
        'biases_detected': detected_count,
        'average_severity': avg_severity,
        'timestamp': datetime.now().isoformat()
    }


@router.get("/explain/{decision_id}")
async def get_explanation(decision_id: str) -> Dict[str, Any]:
    
    from core.responsible_ai import ExplainabilityReport
    import aiosqlite
    import json
    
    async with aiosqlite.connect(rai_framework.db_path) as conn:
        cursor = await conn.execute("""
            SELECT decision_id, decision_type, input_features, output, 
                   explanation, confidence, contributing_factors, timestamp
            FROM explainability_reports
            WHERE decision_id = ?
        """, (decision_id,))
        
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Explanation not found")
        
        return {
            'decision_id': row[0],
            'decision_type': row[1],
            'input_features': json.loads(row[2]),
            'output': json.loads(row[3]),
            'explanation': row[4],
            'confidence': row[5],
            'contributing_factors': json.loads(row[6]),
            'timestamp': row[7]
        }


@router.post("/explain")
async def create_explanation(
    decision_id: str,
    decision_type: str,
    input_features: Dict[str, Any],
    output: Dict[str, Any]
) -> Dict[str, Any]:
    
    report = await rai_framework.generate_explanation(
        decision_id=decision_id,
        decision_type=decision_type,
        input_features=input_features,
        output=output
    )
    
    return report.to_dict()


@router.post("/privacy/audit")
async def audit_privacy_operation(
    operation: str,
    data_accessed: list[str],
    user_id: str,
    purpose: str
) -> Dict[str, Any]:
    
    audit_log = await rai_framework.audit_privacy(
        operation=operation,
        data_accessed=data_accessed,
        user_id=user_id,
        purpose=purpose
    )
    
    return audit_log.to_dict()


@router.post("/privacy/consent")
async def grant_user_consent(
    user_id: str,
    consent_type: str,
    expiry_days: Optional[int] = None
):
    
    await rai_framework.grant_consent(user_id, consent_type, expiry_days)
    return {"message": "Consent granted", "user_id": user_id, "consent_type": consent_type}


@router.delete("/privacy/consent")
async def revoke_user_consent(
    user_id: str,
    consent_type: str
):
    
    await rai_framework.revoke_consent(user_id, consent_type)
    return {"message": "Consent revoked", "user_id": user_id, "consent_type": consent_type}


@router.get("/privacy/audit/logs")
async def get_privacy_audit_logs(
    user_id: Optional[str] = None,
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    import aiosqlite
    import json
    
    async with aiosqlite.connect(rai_framework.db_path) as conn:
        if user_id:
            cursor = await conn.execute("""
                SELECT audit_id, operation, data_accessed, user_id, 
                       purpose, consent_verified, timestamp
                FROM privacy_audit_logs
                WHERE user_id = ? AND timestamp > datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
            """, (user_id, period_hours))
        else:
            cursor = await conn.execute("""
                SELECT audit_id, operation, data_accessed, user_id, 
                       purpose, consent_verified, timestamp
                FROM privacy_audit_logs
                WHERE timestamp > datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
            """, (period_hours,))
        
        rows = await cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append({
                'audit_id': row[0],
                'operation': row[1],
                'data_accessed': json.loads(row[2]),
                'user_id': row[3],
                'purpose': row[4],
                'consent_verified': bool(row[5]),
                'timestamp': row[6]
            })
        
        return {
            'logs': logs,
            'total_count': len(logs),
            'period_hours': period_hours
        }


@router.get("/transparency/report")
async def get_transparency_report(
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    report = await rai_framework.get_transparency_report(period_hours)
    return report


@router.get("/dashboard")
async def get_responsible_ai_dashboard(
    period_hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    
    fairness_results = {}
    for metric_type in FairnessMetricType:
        metrics = await rai_framework.assess_fairness(metric_type, period_hours)
        fairness_results[metric_type.value] = metrics.to_dict()
    
    bias_results = {}
    for bias_category in BiasCategory:
        result = await rai_framework.detect_bias(bias_category, period_hours)
        bias_results[bias_category.value] = result.to_dict()
    
    import aiosqlite
    
    async with aiosqlite.connect(rai_framework.db_path) as conn:
        privacy_cursor = await conn.execute("""
            SELECT COUNT(*), SUM(consent_verified)
            FROM privacy_audit_logs
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
        """, (period_hours,))
        
        privacy_stats = await privacy_cursor.fetchone()
        total_operations = privacy_stats[0] if privacy_stats else 0
        consent_verified = privacy_stats[1] if privacy_stats and privacy_stats[1] else 0
        
        explainability_cursor = await conn.execute("""
            SELECT COUNT(*)
            FROM explainability_reports
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
        """, (period_hours,))
        
        explainability_stats = await explainability_cursor.fetchone()
        total_explanations = explainability_stats[0] if explainability_stats else 0
    
    return {
        'period_hours': period_hours,
        'generated_at': datetime.now().isoformat(),
        'fairness': {
            'metrics': fairness_results,
            'overall_score': sum(m['score'] for m in fairness_results.values()) / len(fairness_results) if fairness_results else 0,
            'all_passed': all(m['passed_threshold'] for m in fairness_results.values())
        },
        'bias_detection': {
            'results': bias_results,
            'detected_count': sum(1 for b in bias_results.values() if b['detected']),
            'average_severity': sum(b['severity'] for b in bias_results.values()) / len(bias_results) if bias_results else 0
        },
        'privacy': {
            'total_operations': total_operations,
            'consent_verified': consent_verified,
            'compliance_rate': (consent_verified / total_operations * 100) if total_operations > 0 else 100.0
        },
        'explainability': {
            'total_explanations': total_explanations
        }
    }
