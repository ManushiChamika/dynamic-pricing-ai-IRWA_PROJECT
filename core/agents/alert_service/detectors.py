# This system continuously monitors numeric data (like prices, metrics, or KPIs) and detects when something behaves abnormally — for example, when a value suddenly spikes or drops compared to its recent trend.
# It’s commonly used for:

# detecting anomalies in time-series data,

# monitoring system metrics,

# alerting on price deviations, latency jumps, etc.


from typing import Dict                  # For type annotations of dictionaries
from datetime import datetime            # For timestamp handling
from collections import defaultdict      # For automatic nested dict creation
import math                              # For square root and math operations

# ---------------------------------------------------------------------
# EWMA-based (Exponentially Weighted Moving Average) Z-Score detector
# ---------------------------------------------------------------------
class EwmaZ:
    def __init__(self, alpha=0.3):
        # alpha: smoothing factor (how much weight new data has)
        self.mu = None                   # mean estimate
        self.var = None                  # variance estimate
        self.alpha = alpha               # smoothing constant (0 < alpha ≤ 1)

    def update(self, x):
        # First data point: initialize mean and variance
        if self.mu is None:
            self.mu, self.var = x, 1e-6  # start with tiny variance to avoid divide-by-zero
        else:
            # Update mean using EWMA formula
            self.mu = self.alpha * x + (1 - self.alpha) * self.mu
            # Update variance using EWMA of squared differences
            self.var = self.alpha * (x - self.mu)**2 + (1 - self.alpha) * self.var

        # Compute Z-score: how far the new value x is from the running mean
        z = 0 if self.var == 0 else (x - self.mu) / math.sqrt(self.var)
        return z                          # Return the standardized deviation

# ---------------------------------------------------------------------
# Detector registry — manages multiple time series anomaly detectors
# ---------------------------------------------------------------------
class DetectorRegistry:
    def __init__(self):
        # Nested dictionary structure:
        # self.series[key][field] → EwmaZ instance
        self.series: Dict[str, Dict[str, EwmaZ]] = defaultdict(dict)

    async def eval(self, name: str, key: str, field: str,
                   value: float, ts: datetime, params: Dict):
        # Check that the requested detector exists
        if name != "ewma_zscore":
            raise ValueError("unknown detector")

        # Retrieve existing EwmaZ object or create a new one for this key+field
        s = self.series[key].setdefault(
            field, EwmaZ(alpha=params.get("alpha", 0.3))
        )

        # Update detector with the new value and compute z-score
        z = s.update(value)

        # Return True if absolute z-score exceeds threshold (anomaly)
        return abs(z) >= params.get("z", 2.5)
