import psycopg2
import os
from dotenv import load_dotenv 

load_dotenv()

def get_connection():
    CONNECTION_STRING = os.getenv("CONNECTION_STRING")
    return psycopg2.connect(CONNECTION_STRING)