import requests
from pymongo import MongoClient, UpdateOne, ASCENDING
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "doyouknowball"
COLLECTION_NAME = "players"

def sync_mlb_players():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        players_col = db[COLLECTION_NAME]

        all_operations = {}

        # 1. Get all 30 MLB Teams
        teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
        teams_res = requests.get(teams_url)
        teams_res.raise_for_status()
        teams = teams_res.json().get("teams", [])

        for team in teams:
            team_id = team.get("id")
            team_name = team.get("name")
            
            roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/40Man"
            
            try:
                roster_res = requests.get(roster_url)
                roster_res.raise_for_status()
                roster_data = roster_res.json().get("roster", [])
                
                print(f"Syncing {len(roster_data)} players from the {team_name}...")

                for p in roster_data:
                    person = p.get("person", {})
                    player_id = person.get("id")
                    full_name = person.get("fullName", "")

                    if not player_id:
                        continue

                    all_operations[player_id] = UpdateOne(
                        {"mlbId": player_id},
                        {
                            "$set": {
                                "mlbId": player_id,
                                "fullName": full_name,
                                "searchName": full_name.lower().strip(),
                                "currentTeamId": team_id,
                            }
                        },
                        upsert=True
                    )
            except Exception as e:
                print(f"Could not fetch roster for team {team_id}: {e}")

        if all_operations:
            print(f"Executing bulk write for {len(all_operations)} total players...")
            players_col.bulk_write(list(all_operations.values()))
            
            players_col.create_index([("searchName", ASCENDING), ("birthDate", ASCENDING)])
            print("Sync complete.")
        else:
            print("No players found to sync.")

        client.close()

    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync_mlb_players()