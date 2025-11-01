# 🔍 Debug API Quick Reference Card

**Access:** `http://localhost:8000/api/debug/`

## Essential Endpoints

```bash
# Database Statistics (start here)
http://localhost:8000/api/debug/stats

# View All Users
http://localhost:8000/api/debug/users

# View All Threads (any user)
http://localhost:8000/api/debug/threads

# View Specific Thread + Messages
http://localhost:8000/api/debug/threads/658

# Search Messages
http://localhost:8000/api/debug/search/messages?query=pricing

# Execute SQL
curl -X POST http://localhost:8000/api/debug/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM threads LIMIT 10", "database": "chat"}'

# View Database Schema
http://localhost:8000/api/debug/database/tables?database=chat
```

## All 14 Endpoints

| # | Endpoint | What It Does |
|---|----------|--------------|
| 1 | `POST /api/debug/database/query` | Run SQL |
| 2 | `GET /api/debug/database/query` | Run SQL (URL) |
| 3 | `GET /api/debug/database/tables` | View schemas |
| 4 | `GET /api/debug/users` | List users |
| 5 | `GET /api/debug/threads` | All threads |
| 6 | `GET /api/debug/threads/{id}` | Thread detail |
| 7 | `GET /api/debug/messages` | All messages |
| 8 | `GET /api/debug/search/messages` | Search messages |
| 9 | `GET /api/debug/catalog` | All products |
| 10 | `GET /api/debug/catalog/{id}` | Product detail |
| 11 | `GET /api/debug/market` | Market data |
| 12 | `GET /api/debug/stats` | DB stats |
| 13 | `DELETE /api/debug/threads/{id}` | Delete thread |
| 14 | `DELETE /api/debug/messages/{id}` | Delete message |

## Key Features

✅ **No Auth** - Completely open  
✅ **Raw SQL** - Execute any query  
✅ **Full Visibility** - Read any user's data  
✅ **Browser Friendly** - Just paste URLs  
✅ **Swagger Docs** - http://localhost:8000/docs

## Quick Start

1. Restart app: `run_full_app.bat`
2. Open: `http://localhost:8000/api/debug/stats`
3. Explore: All endpoints work immediately

## Documentation

- **Full Guide:** `docs/DEBUG_API_GUIDE.md`
- **Security:** `docs/SECURITY_AUDIT_REPORT.md`
- **Summary:** `docs/DEBUGGABILITY_SUMMARY.md`

⚠️ **Remove before production!**
