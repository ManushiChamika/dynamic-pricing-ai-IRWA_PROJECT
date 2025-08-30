# Branch: feat/improve-data-collector

## Purpose
Add product catalog, ingestion job, and price proposal persistence to DataRepo. Implement three MCP tools for product import, collection, and job status. All changes will be minimal, local, and well-commented.

## Scope
- Add product catalog + ingestion job + price proposal persistence to DataRepo.
- Add three MCP tools to Data Collector MCP server:
  1. import_product_catalog(rows: list[dict])
  2. start_collection(sku, market="DEFAULT", connector="mock", depth=1)
  3. get_job_status(job_id)
- Only edit:
  - core/agents/data_collector/repo.py
  - core/agents/data_collector/mcp_server.py

## Constraints & Style
- Python 3.10+ async style, aiosqlite, uuid for job ids.
- Job lifecycle: QUEUED → RUNNING → DONE → FAILED.
- Minimal, idiomatic changes, no new external deps.
- All DB changes additive, new tables only.
- Well-commented, small patch.

## Deliverables
1. Two unified-diff patches for repo.py and mcp_server.py
2. Tiny test snippet for basic verification
3. 3-line acceptance checklist

## Implementation Guidance
- See user prompt for full details and requirements.
