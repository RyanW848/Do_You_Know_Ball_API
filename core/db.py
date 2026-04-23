from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.environ.get("MONGO_URI"))
    return _client["doyouknowball"]

def get_users_collection():
    return get_db()["users"]

def get_players_collection():
    return get_db()["players"]