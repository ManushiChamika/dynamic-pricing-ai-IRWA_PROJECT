# bus_iface.py
# Interface for bus communication between UI and Pricing Optimizer Agent

class PricingOptimizerBusIface:
    def __init__(self):
        self._listeners = []

    def subscribe(self, callback):
        self._listeners.append(callback)

    def publish(self, message):
        for cb in self._listeners:
            cb(message)

# Singleton bus instance
bus = PricingOptimizerBusIface()
