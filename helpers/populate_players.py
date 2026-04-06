import requests
from pymongo import MongoClient, UpdateOne, ASCENDING
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "doyouknowball"
COLLECTION_NAME = "players"

# This script fetches all MLB players for the 2025 and 2026 seasons and syncs them to MongoDB.
def sync_mlb_players():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        players_col = db[COLLECTION_NAME]

        seasons = 2026
        all_operations = {}

        for season in seasons:
            print(f"Fetching all MLB players for the {season} season...")
            
            url = f"https://statsapi.mlb.com/api/v1/sports/1/players?season={season}"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            players = data.get("people", [])
            print(f"Found {len(players)} players in {season}.")

            for p in players:
                player_id = p.get("id")
                full_name = p.get("fullName", "")
                
                all_operations[player_id] = UpdateOne(
                    {"mlbId": player_id},
                    {
                        "$set": {
                            "mlbId": player_id,
                            "fullName": full_name,
                            "searchName": full_name.lower().strip(),
                            "birthDate": p.get("birthDate", ""),
                            "lastSeasonActive": season 
                        }
                    },
                    upsert=True
                )

        players_col.create_index([("searchName", ASCENDING), ("birthDate", ASCENDING)])
        
        client.close()

    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync_mlb_players()