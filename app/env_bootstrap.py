# app/env_bootstrap.py
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)  # loads .env if present
