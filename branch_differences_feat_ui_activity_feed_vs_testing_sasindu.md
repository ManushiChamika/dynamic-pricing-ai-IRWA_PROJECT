# Branch Differences: feat/ui-activity-feed vs testing-sasindu

**Generated on:** September 13, 2025  
**Base Branch:** origin/testing-sasindu  
**Compare Branch:** origin/feat/ui-activity-feed  
**Current Repository:** dynamic-pricing-ai-IRWA_PROJECT  

## Summary of Changes

```
 app/pages/dashboard.py                | 28 ++++++++++++++++-
 core/agents/agent_sdk/activity_log.py | 55 ++++++++++++++++++++++++++++++++
 core/agents/pricing_optimizer.py      | 23 ++++++++++++
 user_data.json                        | 10 ++++++
 4 files changed, 115 insertions(+), 1 deletion(-)
```

## Key Differences Analysis

### 1. Activity Feed Feature
The main difference is the addition of an **Activity Feed** feature in `feat/ui-activity-feed` that allows users to see real-time activity from various agents in the system.

### 2. Agent Logging Integration
`feat/ui-activity-feed` includes comprehensive logging throughout the pricing optimizer workflow, while `testing-sasindu` has these features removed.

### 3. New File: Activity Logger
A new file `core/agents/agent_sdk/activity_log.py` is present in `feat/ui-activity-feed` but missing in `testing-sasindu`.

---

## Detailed File-by-File Differences

### 1. app/pages/dashboard.py
**Status:** Modified  
**Changes:** 28 insertions, 1 deletion  

**What Changed:**
- Added a new "Activity Feed" section at the bottom of the dashboard
- Imports and uses the activity_log module
- Displays recent agent activities with status badges
- Shows timestamps, agent names, actions, and details
- Includes error handling for when the activity logger is unavailable

**Diff:**
```diff
@@ -276,4 +276,30 @@ if alerts:
             st.info("No incidents yet — go to Alerts & Notifications and trigger a Demo scenario.")
         else:
     with st.expander("🔔 Incidents (live — extras)", expanded=False):
-        st.info("Alerts service not available. Ensure core/agents/alert_service exists and dependencies are installed.")
+        st.info("Alerts service not available. Ensure core/agents/alert_service exists and dependencies are installed.")

+# =============================
+# 🔎 Activity Feed (High-Level)
+# =============================
+st.markdown("---")
+st.subheader("🧠 Under-the-hood Activity")
+try:
+    from core.agents.agent_sdk.activity_log import activity_log
+    items = activity_log.recent(50)
+    if not items:
+        st.info("No recent activity yet. Ask a pricing question to see the steps here.")
+    else:
+        for ev in items:
+            status = ev.get("status", "info")
+            badge = "🟢" if status == "completed" else ("🟡" if status == "in_progress" else ("🔴" if status == "failed" else "🔵"))
+            with st.container():
+                st.markdown(f"{badge} [{ev.get('ts')}] <b>{ev.get('agent')}</b> — {ev.get('action')} ", unsafe_allow_html=True)
+                msg = ev.get("message")
+                if msg:
+                    st.caption(msg)
+                details = ev.get("details")
+                if details:
+                    with st.expander("Details", expanded=False):
+                        st.json(details)
+except Exception:
+    st.info("Activity feed unavailable. It will appear once the activity logger module is loaded.")
```

---

### 2. core/agents/agent_sdk/activity_log.py
**Status:** Added (new file)  
**Changes:** 55 insertions  

**What Changed:**
- New file that implements an activity logging system
- Thread-safe logging with a global singleton instance
- Stores activities in a deque with configurable max length
- Each activity has: timestamp, agent, action, status, message, and optional details
- Provides methods to log activities and retrieve recent ones

**Full File Content:**
```python
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from threading import Lock
from typing import Any, Deque, Dict, List, Optional

@dataclass
class Activity:
    ts: str
    agent: str
    action: str
    status: str  # in_progress | completed | failed | info
    message: str = ""
    details: Optional[Dict[str, Any]] = None

class _ActivityLog:
    def __init__(self, maxlen: int = 200) -> None:
        self._items: Deque[Activity] = deque(maxlen=maxlen)
        self._lock = Lock()

    def log(
        self,
        agent: str,
        action: str,
        status: str = "info",
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        rec = Activity(
            ts=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            agent=agent,
            action=action,
            status=status,
            message=message,
            details=details,
        )
        with self._lock:
            self._items.append(rec)

    def recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            it = list(self._items)[-limit:]
        return [asdict(x) for x in reversed(it)]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

# Global singleton instance
activity_log = _ActivityLog()
```

---

### 3. core/agents/pricing_optimizer.py
**Status:** Modified  
**Changes:** 23 insertions  

**What Changed:**
- Added activity logging throughout the pricing optimization workflow
- Logs workflow start/end events
- Logs market data update requests
- Logs tool decisions and executions
- Logs web scraper activities (success/failure)
- Logs price computation results
- Logs alert notifications
- All logging is optional and wrapped in try/except blocks

**Diff:**
```diff
@@ -263,6 +263,15 @@ class LLMBrain:
                                except Exception:
                                        return None

               # Optional: activity log (best-effort)
               try:
                       from core.agents.agent_sdk.activity_log import activity_log as _act
               except Exception:
                       _act = None  # type: ignore

               if _act:
                       _act.log("pricing_optimizer", "workflow.start", "in_progress", message=f"request='{user_request}' sku='{product_name}'")

                # Step 1 & 2: Check data freshness and request update if needed
                records = fetch_records()
                stale = False
@@ -282,6 +291,8 @@ class LLMBrain:
                        # send market data collect request (simulated)
                        msg = f"UPDATE market_data for {product_name}"
                        print(msg)
+                       if _act:
+                               _act.log("pricing_optimizer", "market.request_update", "info", message=msg)

                        # Poll DB for confirmation (simulated) up to max_wait_attempts
                        attempt = 0
                        while attempt < max_wait_attempts:
@@ -310,6 +321,8 @@ class LLMBrain:
                selection = self.decide_tool(user_request, TOOLS)
                tool_name = selection.get("tool_name") if isinstance(selection, dict) else None
                arguments = selection.get("arguments", {}) if isinstance(selection, dict) else {}
+               if _act:
+                       _act.log("llm_brain", "decide_tool", "completed", message=f"tool={tool_name}", details={"args": arguments})

                # Optional pre-step: run scraper to augment data
                if tool_name == "fetch_competitor_price" and TOOLS.get("fetch_competitor_price"):
@@ -333,8 +346,12 @@ class LLMBrain:
                                                conn.commit()
                                        except Exception:
                                                pass
+                                       if _act:
+                                               _act.log("web_scraper", "fetch_competitor_price", "completed", message=f"price={res['price']}", details={"url": url})

                                except Exception as e_scrape:
                                        print(f"[pricing_optimizer] scraper tool failed: {e_scrape}")
+                                       if _act:
+                                               _act.log("web_scraper", "fetch_competitor_price", "failed", message=str(e_scrape), details={"url": url})

                # Ensure we have some data before pricing
@@ -362,6 +379,8 @@ class LLMBrain:
                        return err(f"calculation failed: {e}")
                        if price is None:
                        return err("calculation returned no price")
+               if _act:
+                       _act.log("pricing_optimizer", "compute_price", "completed", message=f"algo={algo} price={price}")

                # Hybrid publish + persist of PriceProposal (non-blocking)
                # - Read current_price and cost from app/data.db product_catalog if available
@@ -515,6 +534,8 @@ class LLMBrain:
                                print("Failed to call notify_alert_fn")
                        else:
                        print(notify_msg)
+               if _act:
+                       _act.log("alert_notifier", "notify", "info", message=notify_msg)

                result = {"product": product_name, "price": price, "algorithm": algo, "status": "success"}
@@ -538,6 +559,8 @@ class LLMBrain:
                                        # re-run once
                                        return self.process_full_workflow(user_request, product_name, db_path=db_path, notify_alert_fn=notify_alert_fn, wait_seconds=wait_seconds, max_wait_attempts=max_wait_attempts, monitor_timeout=0)

+               if _act:
+                       _act.log("pricing_optimizer", "workflow.end", "completed", message=f"sku='{product_name}' status=success")

                return result
```

---

### 4. user_data.json
**Status:** Modified  
**Changes:** 10 insertions  

**What Changed:**
- Added new chat history entries
- Includes a user query about competitor pricing for iPhone 15
- Includes an assistant response (empty content)
- Added corresponding metrics data

**Diff:**
```diff
@@ -148,6 +148,16 @@
                 "role": "assistant",
                 "content": "I notice your message appears to contain random characters. As a specialized assistant for dynamic pricing systems, I can only provide responses related to pricing strategies, discounts, offers, demand/supply, and related financial metrics.\n\nDo you have a question about any of these topics? I'd be happy to help with pricing optimization, discount structures, or other financial aspects of your business.",
                 "time": "02:02:52"
+            },
+            {
+                "role": "user",
+                "content": "\"What is the competitor price for iPhone 15 on https://smartmobile.lk/apple-iphone-price-list-in-sri-lanka/apple-iphone-16-plus-128gb Please optimize our price for maximum profit.\"",
+                "time": "13:54:26"
+            },
+            {
+                "role": "assistant",
+                "content": "",
+                "time": "13:54:39"
             }
         ],
         "metrics": {
```

---

## Merge Implications

### Easy Merge Scenario
- **Base Branch:** `testing-sasindu` (cleaner, no activity features)
- **Feature Branch:** `feat/ui-activity-feed` (includes activity feed and logging)
- **Merge Strategy:** Manual merge required for feature reconciliation

### Key Decisions Needed
1. **Activity Feed:** Keep the dashboard activity feed section?
2. **Agent Logging:** Keep the logging integration in pricing_optimizer.py?
3. **Activity Logger:** Keep the activity_log.py file?
4. **User Data:** Keep the additional chat history entries?

### Recommended Approach
1. Start with `testing-sasindu` as base
2. Cherry-pick activity features if desired
3. Test dashboard and pricing functionality
4. Commit resolved merge

### Files Requiring Manual Attention
- `app/pages/dashboard.py`: Activity feed UI section
- `core/agents/pricing_optimizer.py`: Logging integration
- `core/agents/agent_sdk/activity_log.py`: New file (keep or remove)
- `user_data.json`: Additional chat history

---

## Conclusion

The branches differ primarily in the presence of an **Activity Feed** feature in `feat/ui-activity-feed`. This feature includes:
- Real-time activity logging throughout the pricing optimization workflow
- Dashboard UI to display agent activities
- Thread-safe activity storage and retrieval
- Integration with existing pricing optimizer

**Merge Complexity:** Low to Medium  
**Files Affected:** 4 files  
**New Features:** Activity logging and dashboard feed  
**Breaking Changes:** None detected</content>
<filePath>c:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\branch_differences_feat_ui_activity_feed_vs_testing_sasindu.md