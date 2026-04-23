from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ.get("MONGO_URI"))
db = client["doyouknowball"]

users_collection = db["users"]
players_collection = db["players"]