# 🔍 Debug API Guide

**Purpose:** Complete database visibility and inspection for prototype debugging

**Security:** ⚠️ NO AUTHENTICATION REQUIRED - These endpoints are completely open for debugging

---

## 📊 Quick Start

All endpoints are accessible at `http://localhost:8000/api/debug/`

**Base URL:** `http://localhost:8000`

---

## 🗄️ Database Query Endpoints

### 1. Execute Raw SQL Query (POST)

**Endpoint:** `POST /api/debug/database/query`

**Description:** Execute any SQL query on chat or market database

**Request Body:**
```json
{
  "sql": "SELECT * FROM threads WHERE user_id = 1",
  "database": "chat"
}
```

**Parameters:**
- `sql` (string, required) - SQL query to execute
- `database` (string, optional) - Database name: `chat` or `market` (default: `chat`)

**Response:**
```json
{
  "columns": ["id", "user_id", "title", "created_at"],
  "rows": [
    {"id": 1, "user_id": 1, "title": "My Thread", "created_at": "2025-10-31T10:00:00"},
    {"id": 2, "user_id": 1, "title": "Another Thread", "created_at": "2025-10-31T11:00:00"}
  ],
  "row_count": 2
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/debug/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users LIMIT 5", "database": "chat"}'
```

---

### 2. Execute Raw SQL Query (GET)

**Endpoint:** `GET /api/debug/database/query?sql=<query>&database=<db>`

**Description:** Same as POST but via query parameters (easier for browser testing)

**Example:**
```
http://localhost:8000/api/debug/database/query?sql=SELECT * FROM threads&database=chat
```

---

### 3. List All Tables and Schemas

**Endpoint:** `GET /api/debug/database/tables?database=<db>`

**Description:** Get complete database schema with all tables and columns

**Parameters:**
- `database` (string, optional) - `chat` or `market` (default: `chat`)

**Response:**
```json
{
  "database": "chat",
  "tables": [
    {
      "name": "users",
      "type": "table",
      "sql": "CREATE TABLE users (...)",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "nullable": false,
          "primary_key": true
        },
        {
          "name": "email",
          "type": "TEXT",
          "nullable": false,
          "primary_key": false
        }
      ]
    }
  ]
}
```

**Example:**
```
http://localhost:8000/api/debug/database/tables?database=chat
```

---

## 👥 User Inspection Endpoints

### 4. Get All Users

**Endpoint:** `GET /api/debug/users?limit=<n>&offset=<n>`

**Description:** View all registered users (passwords excluded)

**Parameters:**
- `limit` (int, optional) - Max results (default: 100)
- `offset` (int, optional) - Pagination offset (default: 0)

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "demo@example.com",
      "created_at": "2025-10-30T15:00:00"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**Example:**
```
http://localhost:8000/api/debug/users?limit=50
```

---

## 💬 Thread Inspection Endpoints

### 5. Get All Threads (All Users)

**Endpoint:** `GET /api/debug/threads?user_id=<id>&limit=<n>&offset=<n>`

**Description:** View ALL threads from ALL users (complete visibility)

**Parameters:**
- `user_id` (int, optional) - Filter by specific user
- `limit` (int, optional) - Max results (default: 100)
- `offset` (int, optional) - Pagination offset (default: 0)

**Response:**
```json
{
  "threads": [
    {
      "id": 658,
      "user_id": 1,
      "title": "Retrieve All Inventory Items",
      "created_at": "2025-10-30T10:00:00",
      "updated_at": "2025-10-30T12:00:00",
      "is_draft": false,
      "user_email": "demo@example.com"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**Examples:**
```
# All threads from all users
http://localhost:8000/api/debug/threads

# Threads for specific user
http://localhost:8000/api/debug/threads?user_id=1

# Paginated results
http://localhost:8000/api/debug/threads?limit=20&offset=40
```

---

### 6. Get Thread Details with All Messages

**Endpoint:** `GET /api/debug/threads/{thread_id}`

**Description:** Get complete thread with ALL messages (including private conversations)

**Response:**
```json
{
  "thread": {
    "id": 658,
    "user_id": 1,
    "title": "Retrieve All Inventory Items",
    "created_at": "2025-10-30T10:00:00",
    "updated_at": "2025-10-30T12:00:00",
    "is_draft": false,
    "user_email": "demo@example.com"
  },
  "messages": [
    {
      "id": 1,
      "thread_id": 658,
      "role": "user",
      "content": "Show me all products",
      "created_at": "2025-10-30T10:01:00",
      "workflow_type": null,
      "tool_name": null
    },
    {
      "id": 2,
      "thread_id": 658,
      "role": "assistant",
      "content": "Here are all the products...",
      "created_at": "2025-10-30T10:01:05",
      "workflow_type": "catalog_query",
      "tool_name": "get_all_products"
    }
  ],
  "message_count": 2
}
```

**Example:**
```
http://localhost:8000/api/debug/threads/658
```

---

## 📨 Message Inspection Endpoints

### 7. Get All Messages (Across All Threads)

**Endpoint:** `GET /api/debug/messages?thread_id=<id>&role=<role>&limit=<n>&offset=<n>`

**Description:** View ALL messages from ALL threads and ALL users

**Parameters:**
- `thread_id` (int, optional) - Filter by thread
- `role` (string, optional) - Filter by role: `user` or `assistant`
- `limit` (int, optional) - Max results (default: 100)
- `offset` (int, optional) - Pagination offset (default: 0)

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "thread_id": 658,
      "role": "user",
      "content": "Show me all products",
      "created_at": "2025-10-30T10:01:00",
      "workflow_type": null,
      "tool_name": null,
      "thread_title": "Retrieve All Inventory Items",
      "user_email": "demo@example.com"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**Examples:**
```
# All messages
http://localhost:8000/api/debug/messages

# Only user messages
http://localhost:8000/api/debug/messages?role=user

# Messages from specific thread
http://localhost:8000/api/debug/messages?thread_id=658

# Recent 50 assistant messages
http://localhost:8000/api/debug/messages?role=assistant&limit=50
```

---

### 8. Search Messages by Content

**Endpoint:** `GET /api/debug/search/messages?query=<term>&limit=<n>`

**Description:** Full-text search across ALL messages from ALL users

**Parameters:**
- `query` (string, required) - Search term
- `limit` (int, optional) - Max results (default: 50)

**Response:**
```json
{
  "query": "pricing",
  "matches": [
    {
      "id": 42,
      "thread_id": 10,
      "role": "user",
      "content": "What's the pricing strategy?",
      "created_at": "2025-10-30T14:00:00",
      "thread_title": "Pricing Discussion",
      "user_email": "user@example.com"
    }
  ],
  "count": 1
}
```

**Example:**
```
http://localhost:8000/api/debug/search/messages?query=pricing&limit=20
```

---

## 🛍️ Catalog & Product Endpoints

### 9. Get All Catalog Products

**Endpoint:** `GET /api/debug/catalog?limit=<n>&offset=<n>`

**Description:** View all products in catalog

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Gaming Laptop",
      "current_price": 1299.99,
      "cost": 900.00,
      "stock_quantity": 15,
      "created_at": "2025-10-01T00:00:00",
      "updated_at": "2025-10-30T10:00:00"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**Example:**
```
http://localhost:8000/api/debug/catalog?limit=50
```

---

### 10. Get Product Details with Price History

**Endpoint:** `GET /api/debug/catalog/{product_id}`

**Description:** Get complete product information including all historical prices

**Response:**
```json
{
  "product": {
    "id": 1,
    "name": "Gaming Laptop",
    "current_price": 1299.99,
    "cost": 900.00,
    "stock_quantity": 15
  },
  "price_history": [
    {
      "id": 1,
      "product_id": 1,
      "old_price": 1199.99,
      "new_price": 1299.99,
      "reason": "Market demand increase",
      "timestamp": "2025-10-30T10:00:00"
    }
  ],
  "history_count": 1
}
```

**Example:**
```
http://localhost:8000/api/debug/catalog/1
```

---

## 📈 Market Data Endpoints

### 11. Get Market Data

**Endpoint:** `GET /api/debug/market?product_id=<id>&limit=<n>&offset=<n>`

**Description:** View competitor market data

**Parameters:**
- `product_id` (int, optional) - Filter by product
- `limit` (int, optional) - Max results (default: 100)
- `offset` (int, optional) - Pagination offset (default: 0)

**Response:**
```json
{
  "market_data": [
    {
      "id": 1,
      "product_id": 1,
      "competitor_name": "TechStore",
      "competitor_price": 1199.99,
      "source_url": "https://techstore.com/laptop",
      "created_at": "2025-10-30T09:00:00"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**Example:**
```
# All market data
http://localhost:8000/api/debug/market

# Market data for specific product
http://localhost:8000/api/debug/market?product_id=1
```

---

## 📊 Statistics Endpoint

### 12. Get Database Statistics

**Endpoint:** `GET /api/debug/stats`

**Description:** Get row counts for all tables in both databases

**Response:**
```json
{
  "chat_database": {
    "users": 5,
    "threads": 123,
    "messages": 1456,
    "products": 42,
    "price_history": 89,
    "session_tokens": 12
  },
  "market_database": {
    "market_data": 256
  }
}
```

**Example:**
```
http://localhost:8000/api/debug/stats
```

---

## 🗑️ Deletion Endpoints

### 13. Delete Thread (and All Messages)

**Endpoint:** `DELETE /api/debug/threads/{thread_id}`

**Description:** Permanently delete a thread and all its messages

**Response:**
```json
{
  "message": "Thread 658 and its messages deleted successfully"
}
```

**Example (curl):**
```bash
curl -X DELETE http://localhost:8000/api/debug/threads/658
```

---

### 14. Delete Single Message

**Endpoint:** `DELETE /api/debug/messages/{message_id}`

**Description:** Permanently delete a single message

**Response:**
```json
{
  "message": "Message 42 deleted successfully"
}
```

**Example (curl):**
```bash
curl -X DELETE http://localhost:8000/api/debug/messages/42
```

---

## 🎯 Common Use Cases

### Use Case 1: View All Private Messages for a User

```bash
# Step 1: Find user ID
curl http://localhost:8000/api/debug/users

# Step 2: Get all their threads
curl http://localhost:8000/api/debug/threads?user_id=1

# Step 3: View specific thread with all messages
curl http://localhost:8000/api/debug/threads/658
```

---

### Use Case 2: Debug a Specific Conversation

```bash
# Search for keyword in messages
curl "http://localhost:8000/api/debug/search/messages?query=error&limit=10"

# Get thread details
curl http://localhost:8000/api/debug/threads/123

# View all messages in that thread
curl "http://localhost:8000/api/debug/messages?thread_id=123"
```

---

### Use Case 3: Inspect Database Structure

```bash
# Get all tables in chat database
curl http://localhost:8000/api/debug/database/tables?database=chat

# Get all tables in market database
curl http://localhost:8000/api/debug/database/tables?database=market

# Custom query
curl -X POST http://localhost:8000/api/debug/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "PRAGMA table_info(users)", "database": "chat"}'
```

---

### Use Case 4: Analyze User Activity

```bash
# Get statistics
curl http://localhost:8000/api/debug/stats

# Get all users
curl http://localhost:8000/api/debug/users

# Count messages per user
curl -X POST http://localhost:8000/api/debug/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT t.user_id, u.email, COUNT(m.id) as message_count FROM messages m JOIN threads t ON m.thread_id = t.id JOIN users u ON t.user_id = u.id GROUP BY t.user_id ORDER BY message_count DESC", "database": "chat"}'
```

---

### Use Case 5: Clean Up Test Data

```bash
# Delete specific thread
curl -X DELETE http://localhost:8000/api/debug/threads/999

# Delete specific message
curl -X DELETE http://localhost:8000/api/debug/messages/1234

# Delete all draft threads (via SQL)
curl -X POST http://localhost:8000/api/debug/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "DELETE FROM threads WHERE is_draft = 1", "database": "chat"}'
```

---

## 🔐 Security Notes

⚠️ **IMPORTANT:** These endpoints have NO authentication whatsoever

**Development Only:**
- ✅ Use freely during prototype development
- ✅ Complete database visibility
- ✅ No permission barriers

**Before Production:**
- ❌ Remove or disable debug router
- ❌ Add authentication if keeping endpoints
- ❌ Restrict to admin users only

---

## 💡 Tips

1. **Use Browser for GET requests** - Just paste URLs directly
2. **Use Postman/Insomnia for POST/DELETE** - Easier than curl
3. **Bookmark common queries** - Save frequently used SQL queries
4. **Check stats first** - Use `/api/debug/stats` to understand data size
5. **Start with tables** - Use `/api/debug/database/tables` to see schema

---

## 🚀 Next Steps

**To use these endpoints:**

1. Restart the application: `run_full_app.bat`
2. Open browser to: `http://localhost:8000/api/debug/stats`
3. Try querying users: `http://localhost:8000/api/debug/users`
4. Explore threads: `http://localhost:8000/api/debug/threads`

**Interactive API Docs:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All debug endpoints are listed under the "debug" tag.

---

## 📝 Example SQL Queries

**Find threads with most messages:**
```sql
SELECT t.id, t.title, COUNT(m.id) as msg_count 
FROM threads t 
LEFT JOIN messages m ON t.id = m.thread_id 
GROUP BY t.id 
ORDER BY msg_count DESC 
LIMIT 10
```

**Find users with no threads:**
```sql
SELECT u.id, u.email 
FROM users u 
LEFT JOIN threads t ON u.id = t.user_id 
WHERE t.id IS NULL
```

**Recent assistant messages:**
```sql
SELECT m.content, t.title, m.created_at 
FROM messages m 
JOIN threads t ON m.thread_id = t.id 
WHERE m.role = 'assistant' 
ORDER BY m.created_at DESC 
LIMIT 20
```

**Product pricing analysis:**
```sql
SELECT p.name, p.current_price, p.cost, 
       (p.current_price - p.cost) as profit,
       ((p.current_price - p.cost) / p.cost * 100) as margin_pct
FROM products p
ORDER BY margin_pct DESC
```

---

**End of Debug API Guide** 🎉
