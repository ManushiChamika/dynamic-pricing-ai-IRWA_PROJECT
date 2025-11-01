from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import sqlite3
from pathlib import Path
from pydantic import BaseModel

router = APIRouter(prefix="/api/debug", tags=["debug"])


class QueryRequest(BaseModel):
    sql: str
    database: str = "chat"


class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int


def get_db_path(database: str) -> Path:
    if database == "chat":
        return Path("app/chat_threads/chat.db")
    elif database == "market":
        try:
            from core.config import resolve_market_db
            return resolve_market_db()
        except Exception:
            return Path("data/market.db")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown database: {database}")


def execute_query(sql: str, database: str = "chat") -> QueryResult:
    db_path = get_db_path(database)
    
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Database not found: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        if rows:
            columns = list(rows[0].keys())
            data = [dict(row) for row in rows]
        else:
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            data = []
        
        conn.commit()
        return QueryResult(columns=columns, rows=data, row_count=len(data))
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"SQL error: {str(e)}")
    
    finally:
        conn.close()


@router.post("/database/query", response_model=QueryResult)
def raw_sql_query(request: QueryRequest):
    return execute_query(request.sql, request.database)


@router.get("/database/query", response_model=QueryResult)
def raw_sql_query_get(
    sql: str = Query(..., description="SQL query to execute"),
    database: str = Query("chat", description="Database to query (chat or market)")
):
    return execute_query(sql, database)


@router.get("/database/tables")
def list_tables(database: str = Query("chat", description="Database to inspect")):
    sql = "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name"
    result = execute_query(sql, database)
    
    tables = []
    for row in result.rows:
        table_name = row["name"]
        table_info = execute_query(f"PRAGMA table_info({table_name})", database)
        
        columns = []
        for col in table_info.rows:
            columns.append({
                "name": col["name"],
                "type": col["type"],
                "nullable": not col["notnull"],
                "primary_key": bool(col["pk"])
            })
        
        tables.append({
            "name": table_name,
            "type": row["type"],
            "sql": row["sql"],
            "columns": columns
        })
    
    return {"database": database, "tables": tables}


@router.get("/users")
def get_all_users(
    limit: int = Query(100, description="Maximum number of users to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    sql = f"SELECT id, email, created_at FROM users ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
    result = execute_query(sql, "chat")
    return {
        "users": result.rows,
        "count": result.row_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/threads")
def get_all_threads(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, description="Maximum number of threads to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    if user_id:
        sql = f"""
            SELECT id, user_id, title, created_at, updated_at, is_draft 
            FROM threads 
            WHERE user_id = {user_id}
            ORDER BY updated_at DESC 
            LIMIT {limit} OFFSET {offset}
        """
    else:
        sql = f"""
            SELECT t.id, t.user_id, t.title, t.created_at, t.updated_at, t.is_draft,
                   u.email as user_email
            FROM threads t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.updated_at DESC 
            LIMIT {limit} OFFSET {offset}
        """
    
    result = execute_query(sql, "chat")
    return {
        "threads": result.rows,
        "count": result.row_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/threads/{thread_id}")
def get_thread_details(thread_id: int):
    thread_sql = f"""
        SELECT t.*, u.email as user_email
        FROM threads t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE t.id = {thread_id}
    """
    thread_result = execute_query(thread_sql, "chat")
    
    if not thread_result.rows:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages_sql = f"""
        SELECT id, thread_id, role, content, created_at, workflow_type, tool_name
        FROM messages
        WHERE thread_id = {thread_id}
        ORDER BY created_at ASC
    """
    messages_result = execute_query(messages_sql, "chat")
    
    return {
        "thread": thread_result.rows[0],
        "messages": messages_result.rows,
        "message_count": messages_result.row_count
    }


@router.get("/messages")
def get_all_messages(
    thread_id: Optional[int] = Query(None, description="Filter by thread ID"),
    role: Optional[str] = Query(None, description="Filter by role (user/assistant)"),
    limit: int = Query(100, description="Maximum number of messages to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    conditions = []
    if thread_id:
        conditions.append(f"thread_id = {thread_id}")
    if role:
        conditions.append(f"role = '{role}'")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    sql = f"""
        SELECT m.*, t.title as thread_title, u.email as user_email
        FROM messages m
        LEFT JOIN threads t ON m.thread_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        {where_clause}
        ORDER BY m.created_at DESC
        LIMIT {limit} OFFSET {offset}
    """
    
    result = execute_query(sql, "chat")
    return {
        "messages": result.rows,
        "count": result.row_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/catalog")
def get_catalog_data(
    limit: int = Query(100, description="Maximum number of products to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    products_sql = f"""
        SELECT * FROM products
        ORDER BY updated_at DESC
        LIMIT {limit} OFFSET {offset}
    """
    products_result = execute_query(products_sql, "chat")
    
    return {
        "products": products_result.rows,
        "count": products_result.row_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/catalog/{product_id}")
def get_product_details(product_id: int):
    product_sql = f"SELECT * FROM products WHERE id = {product_id}"
    product_result = execute_query(product_sql, "chat")
    
    if not product_result.rows:
        raise HTTPException(status_code=404, detail="Product not found")
    
    history_sql = f"""
        SELECT * FROM price_history
        WHERE product_id = {product_id}
        ORDER BY timestamp DESC
    """
    history_result = execute_query(history_sql, "chat")
    
    return {
        "product": product_result.rows[0],
        "price_history": history_result.rows,
        "history_count": history_result.row_count
    }


@router.get("/market")
def get_market_data(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    if product_id:
        sql = f"""
            SELECT * FROM market_data
            WHERE product_id = {product_id}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
    else:
        sql = f"""
            SELECT * FROM market_data
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
    
    result = execute_query(sql, "market")
    return {
        "market_data": result.rows,
        "count": result.row_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
def get_database_stats():
    chat_stats = {}
    market_stats = {}
    
    chat_tables = ["users", "threads", "messages", "products", "price_history", "session_tokens"]
    for table in chat_tables:
        try:
            result = execute_query(f"SELECT COUNT(*) as count FROM {table}", "chat")
            chat_stats[table] = result.rows[0]["count"] if result.rows else 0
        except:
            chat_stats[table] = "N/A"
    
    market_tables = ["market_data"]
    for table in market_tables:
        try:
            result = execute_query(f"SELECT COUNT(*) as count FROM {table}", "market")
            market_stats[table] = result.rows[0]["count"] if result.rows else 0
        except:
            market_stats[table] = "N/A"
    
    return {
        "chat_database": chat_stats,
        "market_database": market_stats
    }


@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: int):
    try:
        execute_query(f"DELETE FROM messages WHERE thread_id = {thread_id}", "chat")
        execute_query(f"DELETE FROM threads WHERE id = {thread_id}", "chat")
        return {"message": f"Thread {thread_id} and its messages deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}")
def delete_message(message_id: int):
    try:
        execute_query(f"DELETE FROM messages WHERE id = {message_id}", "chat")
        return {"message": f"Message {message_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/messages")
def search_messages(
    query: str = Query(..., description="Search term"),
    limit: int = Query(50, description="Maximum results")
):
    sql = f"""
        SELECT m.*, t.title as thread_title, u.email as user_email
        FROM messages m
        LEFT JOIN threads t ON m.thread_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE m.content LIKE '%{query}%'
        ORDER BY m.created_at DESC
        LIMIT {limit}
    """
    
    result = execute_query(sql, "chat")
    return {
        "query": query,
        "matches": result.rows,
        "count": result.row_count
    }
