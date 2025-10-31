# It allows users to define alerting rules as either:

# Logical expressions — e.g. price < competitor_price * 0.95, or
# Statistical detectors — e.g. “flag anomaly if z-score > 2.5”

# The code then safely parses, validates, and evaluates these rules against incoming
# data (ticks, proposals, etc.), while enforcing optional “hold” durations before triggering alerts.


# core/agents/alert_service/rules.py
from __future__ import annotations              # Enable postponed evaluation of annotations

import ast                                     # Python AST to safely parse expressions
import logging
import operator as op                          # Operator functions for arithmetic/comparisons
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from .schemas import RuleSpec                   # Rule specification model
from .detectors import DetectorRegistry         # Detector manager (e.g., EWMA z-score)

log = logging.getLogger(__name__)               # Module-level logger

# Whitelisted names available to rule expressions
ALLOWED: Dict[str, Any] = {
    "min": min, "max": max, "abs": abs,
    "True": True, "False": False, "None": None,
}

# Mapping of AST operator nodes to real Python operator funcs
OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Mod: op.mod, ast.Pow: op.pow,
    ast.Gt: op.gt, ast.Lt: op.lt, ast.GtE: op.ge, ast.LtE: op.le, ast.Eq: op.eq, ast.NotEq: op.ne,
}

def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Safe attribute/dict access: obj.name or obj['name'] or default."""
    if obj is None: return default
    if isinstance(obj, dict): return obj.get(name, default)
    return getattr(obj, name, default)

def _get_key(obj: Any, name: str, default: Any = None) -> Any:
    """Same as _get_attr (kept for semantic clarity where key access is expected)."""
    if isinstance(obj, dict): return obj.get(name, default)
    return getattr(obj, name, default)

def _eval(node: ast.AST, env: Dict[str, Any]) -> Any:
    """Evaluate a restricted expression AST node against an environment."""
    if isinstance(node, ast.Constant): return node.value           # Python 3.8+: literals
    if isinstance(node, ast.Num): return node.n                    # Back-compat for older nodes
    if isinstance(node, ast.Name):
        if node.id in env: return env[node.id]                     # Variables from env
        if node.id in ALLOWED: return ALLOWED[node.id]             # Whitelisted names
        raise ValueError(f"name '{node.id}' not allowed")
    if isinstance(node, ast.Attribute):
        base = _eval(node.value, env)                              # Evaluate base object
        return _get_attr(base, node.attr)                          # Then get attribute
    if isinstance(node, ast.Subscript):
        container = _eval(node.value, env)                         # Evaluate container
        sl = node.slice.value if hasattr(node.slice, "value") else node.slice  # Py ver compat
        key = _eval(sl, env)                                       # Evaluate index key
        try: return container[key]                                 # Try item access
        except Exception: return None                              # Fallback to None on errors
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub): return -_eval(node.operand, env)
        if isinstance(node.op, ast.UAdd): return +_eval(node.operand, env)
        if isinstance(node.op, ast.Not):  return not bool(_eval(node.operand, env))
        raise ValueError("unsupported unary op")
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, env); right = _eval(node.right, env)
        fn = OPS.get(type(node.op)); 
        if fn is None: raise ValueError("unsupported binary op")
        return fn(left, right)                                     # Apply arithmetic op
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        for opnode, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, env)
            fn = OPS.get(type(opnode))
            if fn is None or not fn(left, right): return False     # Chain fails
            left = right                                           # Support chained comparisons
        return True
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for v in node.values:
                if not bool(_eval(v, env)): return False           # Short-circuit AND
            return True
        if isinstance(node.op, ast.Or):
            for v in node.values:
                if bool(_eval(v, env)): return True                # Short-circuit OR
            return False
        raise ValueError("unsupported bool op")
    if isinstance(node, ast.Call):
        func = _eval(node.func, env)                               # Function being called
        if func not in (min, max, abs):                            # Restrict callable surface
            raise ValueError("function not allowed")
        args = [_eval(a, env) for a in node.args]                  # Evaluate args
        return func(*args)
    raise ValueError(f"unsupported node: {type(node).__name__}")   # Any other node is blocked

def compile_where(expr: str):
    """Compile a safe boolean expression into a callable(env)->bool."""
    tree = ast.parse(expr, mode="eval")                            # Parse into AST
    def fn(env: Dict[str, Any]) -> bool:
        return bool(_eval(tree.body, env))                         # Evaluate at runtime
    return fn

def parse_duration(s: Optional[str]) -> timedelta:
    """Parse durations like '5s','10m','2h','1d' into timedelta."""
    if not s: return timedelta(0)
    s = s.strip().lower()
    if len(s) < 2: raise ValueError(f"invalid duration '{s}'")
    unit = s[-1]                                                   # Last char = unit
    n = int(s[:-1].strip())                                        # Leading digits = value
    table = {"s": timedelta(seconds=n), "m": timedelta(minutes=n),
             "h": timedelta(hours=n), "d": timedelta(days=n)}
    if unit not in table:
        raise ValueError(f"unsupported duration unit '{unit}' in '{s}' (use s/m/h/d)")
    return table[unit]

class RuleRuntime:
    """Compiled predicate + hold_for logic."""
    def __init__(self, spec: RuleSpec):
        self.spec = spec
        self.where = compile_where(spec.where) if spec.where else None  # Pre-compile filter
        self.hold = parse_duration(spec.hold_for) if spec.hold_for else None  # Hold window
        self._last_true: Dict[str, datetime] = {}                        # SKU → first-true time

    async def evaluate(self, payload: Any, now: datetime,
                       detectors: DetectorRegistry, alias: Optional[str] = None) -> bool:
        """Evaluate rule against a payload; respect detector/where and hold_for."""
        if not self.spec.enabled: return False                           # Skip disabled rules

        # Seed environment with whitelisted names and event aliases
        env: Dict[str, Any] = {**ALLOWED, "tick": payload, "pp": payload}
        if alias:
            env[alias] = payload

        # Flatten payload to top level for convenience (e.g., env['competitor_price'])
        try:
            if hasattr(payload, "model_dump") and callable(getattr(payload, "model_dump")):
                payload_dict = payload.model_dump()
            elif hasattr(payload, "dict") and callable(getattr(payload, "dict")):
                payload_dict = payload.dict()
            else:
                payload_dict = getattr(payload, "__dict__", {}) or {}
        except Exception:
            payload_dict = {}
        if isinstance(payload_dict, dict):
            for k, v in payload_dict.items():
                if isinstance(k, str) and k not in env and k not in ALLOWED:
                    env[k] = v

        ok = False
        if self.where:                                                  # Expression-based rule
            try:
                ok = bool(self.where(env))                              # Evaluate predicate
                log.debug("rule %s eval where=%s alias=%s sku=%s => %s",
                          self.spec.id, self.spec.where, alias, _get_key(payload, "sku"), ok)
            except Exception as e:
                log.debug("rule %s evaluation error: %s", self.spec.id, e)
                return False
        elif self.spec.detector:                                        # Detector-based rule
            key = _get_key(payload, "sku", "GLOBAL")                    # Series key
            val = _get_attr(payload, self.spec.field) if self.spec.field else None  # Observed value
            ok = await detectors.eval(self.spec.detector, key=key, field=self.spec.field,
                                      value=val, ts=now, params=self.spec.params)
        else:
            return False                                                # Neither where nor detector

        sku = _get_key(payload, "sku", "")                              # Group key for hold logic
        if not ok:
            self._last_true.pop(sku, None)                              # Reset hold window
            return False

        if not self.hold or self.hold == timedelta(0):                  # No hold → fire immediately
            return True

        last = self._last_true.get(sku)                                 # First time it became true?
        if not last:
            self._last_true[sku] = now                                  # Start hold window
            return False

        return (now - last) >= self.hold                                # True long enough?
