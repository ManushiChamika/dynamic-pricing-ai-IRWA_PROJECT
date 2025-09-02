import os
from core.agents.user_interact import user_interaction_agent as uia

print("ENV  DATA_DB       =", os.getenv("DATA_DB"))
print("ENV  MARKET_DB_PATH=", os.getenv("MARKET_DB_PATH"))
print("AGENT MARKET_DB_PATH (compiled default) =", getattr(uia, "MARKET_DB_PATH", "<not found>"))