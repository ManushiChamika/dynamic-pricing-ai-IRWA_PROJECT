# core/agent_sdk/bus_factory.py
import os
from .bus_iface import BusIface
from .local_bus import bus as local_bus  # in-process fallback

_bus: BusIface | None = None

def get_bus() -> BusIface:
    """Return the selected bus implementation based on ALERT_BUS env var."""
    global _bus
    if _bus:
        return _bus

    impl = os.getenv("ALERT_BUS", "local").lower()

    if impl == "local":
        _bus = local_bus

    elif impl == "nats":
        # requires core/agent_sdk/transports/nats_bus.py
        from .transports.nats_bus import NatsBus
        _bus = NatsBus(os.getenv("NATS_URL", "nats://localhost:4222"))

    elif impl == "kafka":
        # if/when you add it at core/agent_sdk/transports/kafka_bus.py
        from .transports.kafka_bus import KafkaBus  # type: ignore
        _bus = KafkaBus(os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"))

    else:
        raise RuntimeError(f"Unknown ALERT_BUS={impl}")

    return _bus
