import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv 

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)

def get_connection():
    CONNECTION_STRING = os.getenv("CONNECTION_STRING")
    if not CONNECTION_STRING:
        raise RuntimeError("CONNECTION_STRING not set")
    return psycopg2.connect(CONNECTION_STRING)