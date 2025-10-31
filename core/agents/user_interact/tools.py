import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from .context import get_owner_id
except Exception:
    def get_owner_id():
        return None


def get_db_paths():
    root = Path(__file__).resolve().parents[3]
    return {
        "app": root / "app" / "data.db",
        "market": root / "app" / "data.db"
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        return cur.fetchone() is not None
    except Exception:
        return False


def list_inventory_items(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["app"])
    owner_id = get_owner_id()
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "product_catalog"):
                return {"items": [], "total": 0, "note": "product_catalog missing"}
            
            q = "SELECT sku, title, currency, current_price, cost, stock, updated_at FROM product_catalog"
            params: List[Any] = []
            
            conditions = []
            if owner_id:
                conditions.append("owner_id = ?")
                params.append(owner_id)
            
            if search:
                conditions.append("(sku LIKE ? OR title LIKE ?)")
                like = f"%{search}%"
                params.extend([like, like])
            
            if conditions:
                q += " WHERE " + " AND ".join(conditions)
            
            q += " ORDER BY updated_at DESC LIMIT ?"
            params.append(int(limit))
            rows = [dict(r) for r in conn.execute(q, params).fetchall()]
            return {"items": rows, "total": len(rows)}
    except Exception as e:
        return {"error": str(e)}


def get_inventory_item(sku: str) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["app"])
    owner_id = get_owner_id()
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "product_catalog"):
                return {"item": None, "note": "product_catalog missing"}
            
            q = "SELECT sku, title, currency, current_price, cost, stock, updated_at FROM product_catalog WHERE sku=?"
            params = [sku]
            
            if owner_id:
                q += " AND owner_id=?"
                params.append(owner_id)
            
            q += " LIMIT 1"
            row = conn.execute(q, params).fetchone()
            return {"item": dict(row) if row else None}
    except Exception as e:
        return {"error": str(e)}


def list_pricing_list(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["market"])
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "pricing_list"):
                return {"items": [], "total": 0, "note": "pricing_list missing"}
            q = "SELECT product_name, optimized_price, last_update, reason FROM pricing_list"
            params: List[Any] = []
            if search:
                q += " WHERE product_name LIKE ?"
                params.append(f"%{search}%")
            q += " ORDER BY last_update DESC LIMIT ?"
            params.append(int(limit))
            rows = [dict(r) for r in conn.execute(q, params).fetchall()]
            return {"items": rows, "total": len(rows)}
    except Exception as e:
        return {"error": str(e)}


def list_price_proposals(sku: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["app"])
    owner_id = get_owner_id()
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "price_proposals"):
                return {"items": [], "total": 0, "note": "price_proposals missing"}
            
            if owner_id:
                q = """
                    SELECT pp.id, pp.sku, pp.proposed_price, pp.current_price, pp.margin, pp.algorithm, pp.ts 
                    FROM price_proposals pp
                    INNER JOIN product_catalog pc ON pp.sku = pc.sku
                    WHERE pc.owner_id = ?
                """
                params: List[Any] = [owner_id]
                
                if sku:
                    q += " AND pp.sku = ?"
                    params.append(sku)
            else:
                q = "SELECT id, sku, proposed_price, current_price, margin, algorithm, ts FROM price_proposals"
                params: List[Any] = []
                if sku:
                    q += " WHERE sku = ?"
                    params.append(sku)
            
            q += " ORDER BY pp.ts DESC LIMIT ?" if owner_id else " ORDER BY ts DESC LIMIT ?"
            params.append(int(limit))
            rows = [dict(r) for r in conn.execute(q, params).fetchall()]
            return {"items": rows, "total": len(rows)}
    except Exception as e:
        return {"error": str(e)}


def list_market_data(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["market"])
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "market_data"):
                return {"items": [], "total": 0, "note": "market_data missing"}
            q = "SELECT id, product_name, price, features, update_time FROM market_data"
            params: List[Any] = []
            if search:
                q += " WHERE product_name LIKE ?"
                params.append(f"%{search}%")
            q += " ORDER BY update_time DESC LIMIT ?"
            params.append(int(limit))
            rows = [dict(r) for r in conn.execute(q, params).fetchall()]
            return {"items": rows, "total": len(rows)}
    except Exception as e:
        return {"error": str(e)}


def list_inventory(search: str = "", limit: int = 100) -> Dict[str, Any]:
    return list_inventory_items(search=search or None, limit=limit)


def list_market_prices(search: str = "", limit: int = 10) -> Dict[str, Any]:
    return list_pricing_list(search=search or None, limit=limit)


def list_proposals(sku: str = "", limit: int = 10) -> Dict[str, Any]:
    return list_price_proposals(sku=sku or None, limit=limit)


def optimize_price(sku: str) -> Dict[str, Any]:
    owner_id = get_owner_id()
    
    if owner_id:
        item_check = get_inventory_item(sku)
        if item_check.get("error"):
            return {"ok": False, "error": f"Failed to verify SKU ownership: {item_check['error']}"}
        if not item_check.get("item"):
            return {"ok": False, "error": f"SKU '{sku}' not found in your inventory"}
    
    try:
        from core.agents.price_optimizer.agent import PricingOptimizerAgent
        import asyncio
        
        agent = PricingOptimizerAgent()
        
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(agent.process_full_workflow(f"Optimize price for {sku}", sku))
            return {
                "ok": True,
                "message": f"Price optimization started for {sku}. Processing in background.",
                "sku": sku
            }
        except RuntimeError:
            result = asyncio.run(agent.process_full_workflow(f"Optimize price for {sku}", sku))
            return {
                "ok": result.get("status") == "ok",
                "message": result.get("message") or result.get("reason") or f"Optimization completed for {sku}",
                "sku": sku,
                "result": result
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_pricing_workflow(sku: str) -> Dict[str, Any]:
    return optimize_price(sku)


def collect_market_data() -> Dict[str, Any]:
    return {"info": "Market data collection would trigger the data collection agent"}


def check_stale_market_data(threshold_minutes: int = 60) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["market"])
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "market_data"):
                return {"stale_items": [], "count": 0, "note": "market_data missing"}
            
            query = """
                SELECT id, product_name, price, update_time,
                       CAST((julianday('now') - julianday(update_time)) * 24 * 60 AS INTEGER) as age_minutes
                FROM market_data
                WHERE age_minutes > ?
                ORDER BY age_minutes DESC
            """
            rows = conn.execute(query, (threshold_minutes,)).fetchall()
            stale_items = [dict(r) for r in rows]
            
            total_query = "SELECT COUNT(*) as total FROM market_data"
            total_count = conn.execute(total_query).fetchone()["total"]
            
            return {
                "ok": True,
                "stale_items": stale_items,
                "stale_count": len(stale_items),
                "total_count": total_count,
                "threshold_minutes": threshold_minutes,
                "message": f"Found {len(stale_items)} stale items out of {total_count} total (>{threshold_minutes} min old)"
            }
    except Exception as e:
        return {"error": str(e)}


def scan_for_alerts() -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_path = str(db_paths["app"])
    owner_id = get_owner_id()
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "incidents"):
                return {"alerts": [], "total": 0, "note": "incidents table missing"}
            
            if owner_id:
                rows = conn.execute(
                    """SELECT i.id, i.sku, i.title, i.severity, i.status, i.created_at, i.details 
                       FROM incidents i
                       INNER JOIN product_catalog pc ON i.sku = pc.sku
                       WHERE pc.owner_id = ?
                       ORDER BY i.created_at DESC 
                       LIMIT 50""",
                    (owner_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT id, sku, title, severity, status, created_at, details 
                       FROM incidents 
                       ORDER BY created_at DESC 
                       LIMIT 50"""
                ).fetchall()
            
            alerts = [dict(r) for r in rows]
            open_count = sum(1 for a in alerts if a.get("status") == "OPEN")
            
            return {
                "ok": True,
                "alerts": alerts,
                "total": len(alerts),
                "open_count": open_count,
                "message": f"Found {len(alerts)} alerts ({open_count} open)"
            }
    except Exception as e:
        return {"error": str(e)}


def request_market_fetch() -> Dict[str, Any]:
    return {"info": "Market fetch request would trigger the market collector"}


def execute_sql(database: str, query: str) -> Dict[str, Any]:
    db_paths = get_db_paths()
    db_key = database.lower().strip()
    
    if db_key not in db_paths:
        return {"error": f"Unknown database: {database}. Available: {list(db_paths.keys())}"}
    
    try:
        db_path = db_paths[db_key]
        if not db_path.exists():
            return {"error": f"Database file not found: {db_path}"}
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        
        return {"ok": True, "rows": result, "count": len(result)}
    except Exception as e:
        return {"error": str(e)}


TOOLS_MAP = {
    "list_inventory_items": list_inventory_items,
    "get_inventory_item": get_inventory_item,
    "list_pricing_list": list_pricing_list,
    "list_price_proposals": list_price_proposals,
    "list_market_data": list_market_data,
    "check_stale_market_data": check_stale_market_data,
    "list_inventory": list_inventory,
    "list_market_prices": list_market_prices,
    "list_proposals": list_proposals,
    "optimize_price": optimize_price,
    "run_pricing_workflow": run_pricing_workflow,
    "collect_market_data": collect_market_data,
    "scan_for_alerts": scan_for_alerts,
    "request_market_fetch": request_market_fetch,
    "execute_sql": execute_sql,
}
