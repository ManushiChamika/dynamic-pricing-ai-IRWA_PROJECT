# core/agents/alert_service/rules.py
from __future__ import annotations

import ast
import logging
import operator as op
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from .schemas import RuleSpec
from .detectors import DetectorRegistry

log = logging.getLogger(__name__)

ALLOWED: Dict[str, Any] = {
    "min": min, "max": max, "abs": abs,
    "True": True, "False": False, "None": None,
}

OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Mod: op.mod, ast.Pow: op.pow,
    ast.Gt: op.gt, ast.Lt: op.lt, ast.GtE: op.ge, ast.LtE: op.le, ast.Eq: op.eq, ast.NotEq: op.ne,
}

def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None: return default
    if isinstance(obj, dict): return obj.get(name, default)
    return getattr(obj, name, default)

def _get_key(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict): return obj.get(name, default)
    return getattr(obj, name, default)

def _eval(node: ast.AST, env: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, ast.Num): return node.n
    if isinstance(node, ast.Name):
        if node.id in env: return env[node.id]
        if node.id in ALLOWED: return ALLOWED[node.id]
        raise ValueError(f"name '{node.id}' not allowed")
    if isinstance(node, ast.Attribute):
        base = _eval(node.value, env)
        return _get_attr(base, node.attr)
    if isinstance(node, ast.Subscript):
        container = _eval(node.value, env)
        sl = node.slice.value if hasattr(node.slice, "value") else node.slice
        key = _eval(sl, env)
        try: return container[key]
        except Exception: return None
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub): return -_eval(node.operand, env)
        if isinstance(node.op, ast.UAdd): return +_eval(node.operand, env)
        if isinstance(node.op, ast.Not): return not bool(_eval(node.operand, env))
        raise ValueError("unsupported unary op")
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, env); right = _eval(node.right, env)
        fn = OPS.get(type(node.op)); 
        if fn is None: raise ValueError("unsupported binary op")
        return fn(left, right)
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        for opnode, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, env)
            fn = OPS.get(type(opnode))
            if fn is None or not fn(left, right): return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for v in node.values:
                if not bool(_eval(v, env)): return False
            return True
        if isinstance(node.op, ast.Or):
            for v in node.values:
                if bool(_eval(v, env)): return True
            return False
        raise ValueError("unsupported bool op")
    if isinstance(node, ast.Call):
        func = _eval(node.func, env)
        if func not in (min, max, abs):
            raise ValueError("function not allowed")
        args = [_eval(a, env) for a in node.args]
        return func(*args)
    raise ValueError(f"unsupported node: {type(node).__name__}")

def compile_where(expr: str):
    tree = ast.parse(expr, mode="eval")
    def fn(env: Dict[str, Any]) -> bool:
        return bool(_eval(tree.body, env))
    return fn

def parse_duration(s: Optional[str]) -> timedelta:
    if not s: return timedelta(0)
    s = s.strip().lower()
    if len(s) < 2: raise ValueError(f"invalid duration '{s}'")
    unit = s[-1]
    n = int(s[:-1].strip())
    table = {"s": timedelta(seconds=n), "m": timedelta(minutes=n),
             "h": timedelta(hours=n), "d": timedelta(days=n)}
    if unit not in table:
        raise ValueError(f"unsupported duration unit '{unit}' in '{s}' (use s/m/h/d)")
    return table[unit]

class RuleRuntime:
    """Compiled predicate + hold_for logic."""
    def __init__(self, spec: RuleSpec):
        self.spec = spec
        self.where = compile_where(spec.where) if spec.where else None
        self.hold = parse_duration(spec.hold_for) if spec.hold_for else None
        self._last_true: Dict[str, datetime] = {}

    async def evaluate(self, payload: Any, now: datetime,
                       detectors: DetectorRegistry, alias: Optional[str] = None) -> bool:
        if not self.spec.enabled: return False

        env: Dict[str, Any] = {**ALLOWED, "tick": payload, "pp": payload}
        if alias: env[alias] = payload

        ok = False
        if self.where:
            try:
                ok = bool(self.where(env))
                log.debug("rule %s eval where=%s alias=%s sku=%s => %s",
                          self.spec.id, self.spec.where, alias, _get_key(payload, "sku"), ok)
            except Exception as e:
                log.debug("rule %s evaluation error: %s", self.spec.id, e)
                return False
        elif self.spec.detector:
            key = _get_key(payload, "sku", "GLOBAL")
            val = _get_attr(payload, self.spec.field) if self.spec.field else None
            ok = await detectors.eval(self.spec.detector, key=key, field=self.spec.field,
                                      value=val, ts=now, params=self.spec.params)
        else:
            return False

        sku = _get_key(payload, "sku", "")
        if not ok:
            self._last_true.pop(sku, None)
            return False

        if not self.hold or self.hold == timedelta(0):
            return True

        last = self._last_true.get(sku)
        if not last:
            self._last_true[sku] = now
            return False

        return (now - last) >= self.hold
