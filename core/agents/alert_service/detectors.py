from typing import Dict
from datetime import datetime
from collections import defaultdict
import math

class EwmaZ:
    def __init__(self, alpha=0.3):
        self.mu = None
        self.var = None
        self.alpha = alpha
    def update(self, x):
        if self.mu is None:
            self.mu, self.var = x, 1e-6
        else:
            self.mu = self.alpha*x + (1-self.alpha)*self.mu
            self.var = self.alpha*(x-self.mu)**2 + (1-self.alpha)*self.var
        z = 0 if self.var == 0 else (x - self.mu) / math.sqrt(self.var)
        return z

class DetectorRegistry:
    def __init__(self):
        self.series: Dict[str, Dict[str, EwmaZ]] = defaultdict(dict)
    async def eval(self, name: str, key: str, field: str, value: float, ts: datetime, params: Dict):
        if name != "ewma_zscore": raise ValueError("unknown detector")
        s = self.series[key].setdefault(field, EwmaZ(alpha=params.get("alpha", 0.3)))
        z = s.update(value)
        return abs(z) >= params.get("z", 2.5)
