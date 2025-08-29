# bus_events.py
# Event types for Pricing Optimizer workflow

class PricingOptimizerEvents:
    PROCESSING = "pricing_optimizer_processing"
    CHECKING_DB = "checking_database"
    DATA_STALE = "data_stale"
    UPDATING_DB = "updating_database"
    CALCULATING_PRICE = "calculating_price"
    UPDATING_PRICING_LIST = "updating_pricing_list"
    NOTIFY_ALERT = "notifying_alert_agent"
    DONE = "done"
    ERROR = "error"
