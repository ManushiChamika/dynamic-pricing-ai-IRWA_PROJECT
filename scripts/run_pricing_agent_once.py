#!/usr/bin/env python3
"""Run the Pricing Optimizer once and write results to app/ for inspection.

This script is intended to be executed with the project's venv Python.
"""
import json
import sqlite3
import os
import traceback

from core.agents.pricing_optimizer import PricingOptimizerAgent


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(repo_root, "app")
    os.makedirs(out_dir, exist_ok=True)
    result_path = os.path.join(out_dir, "pricing_agent_run.json")
    dbrows_path = os.path.join(out_dir, "pricing_agent_dbrows.json")

    try:
        agent = PricingOptimizerAgent()
        res = agent.process_full_workflow("maximize profit", "iphone15")
    except Exception as e:
        res = {"status": "error", "message": str(e), "trace": traceback.format_exc()}

    # write agent result
    try:
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({"agent_result": res}, f, default=str, indent=2)
    except Exception:
        print("failed to write agent result:\n", traceback.format_exc())

    # query DB for pricing_list row
    try:
        conn = sqlite3.connect(os.path.join(repo_root, "market.db"))
        cur = conn.cursor()
        cur.execute("SELECT product_name, optimized_price, last_update, reason FROM pricing_list WHERE product_name=?", ("iphone15",))
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        rows = {"status": "db_error", "message": str(e), "trace": traceback.format_exc()}

    try:
        with open(dbrows_path, "w", encoding="utf-8") as f:
            json.dump({"db_rows": rows}, f, default=str, indent=2)
    except Exception:
        print("failed to write db rows:\n", traceback.format_exc())

    print("WROTE", result_path, dbrows_path)


if __name__ == '__main__':
    main()
