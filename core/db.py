from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI"))
db = client.get_default_database()

users_collection = db["users"]
players_collection = db["players"]