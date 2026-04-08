import requests
from pymongo import MongoClient, UpdateOne, ASCENDING
import os
from dotenv import load_dotenv
import time

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "doyouknowball"
COLLECTION_NAME = "players"

def get_stats_for_years(stats_groups, target_years):
    results = {}
    positions_2025 = set()

    valid_pos = {"P", "C", "1B", "2B", "3B", "SS"}
    of_pos = {"LF", "CF", "RF", "OF"}

    for year in target_years:
        results[str(year)] = {
            "hitting": {"HR": 0, "R": 0, "RBI": 0, "SB": 0, "BA": ".000", "SLG": ".000", "OBP": ".000", "OPS": ".000", "PA": 0},
            "pitching": {"W": 0, "K": 0, "SV": 0, "ERA": "0.00", "WHIP": "0.00", "IP": "0.0"}
        }

    for group in stats_groups:
        group_name = group.get("group", {}).get("displayName")
        
        for split in group.get("splits", []):
            season = split.get("season")
            s = split.get("stat", {})
            
            # --- POSITIONS LOGIC (2025 Only) ---
            if group_name == "fielding" and season == "2025":
                raw_pos = split.get("position", {}).get("abbreviation")
                if raw_pos in of_pos:
                    positions_2025.add("OF")
                elif raw_pos in valid_pos:
                    positions_2025.add(raw_pos)
                elif raw_pos in ["DH", "TW"]:
                    positions_2025.add("UT")

            # --- STATS LOGIC ---
            if season in results:
                if group_name == "hitting":
                    results[season]["hitting"] = {
                        "HR": s.get("homeRuns", 0), "R": s.get("runs", 0), "RBI": s.get("rbi", 0),
                        "SB": s.get("stolenBases", 0), "BA": s.get("avg", ".000"), "SLG": s.get("slg", ".000"),
                        "OBP": s.get("obp", ".000"), "OPS": s.get("ops", ".000"), "PA": s.get("plateAppearances", 0)
                    }
                elif group_name == "pitching":
                    results[season]["pitching"] = {
                        "W": s.get("wins", 0), "K": s.get("strikeOuts", 0), "SV": s.get("saves", 0),
                        "ERA": s.get("era", "0.00"), "WHIP": s.get("whip", "0.00"), "IP": s.get("inningsPitched", "0.0")
                    }
                    
    return results, ", ".join(sorted(list(positions_2025)))

def sync_mlb_players():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        players_col = db[COLLECTION_NAME]
        
        players_col.delete_many({})
        
        target_years = ["2023", "2024", "2025"]
        all_players_metadata = {} 

        print("Gathering player list...")
        teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
        teams = requests.get(teams_url).json().get("teams", [])

        for team in teams:
            team_id = team.get("id")
            roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster/40Man"
            try:
                roster_data = requests.get(roster_url).json().get("roster", [])
                for p in roster_data:
                    all_players_metadata[p["person"]["id"]] = {
                        "fullName": p["person"]["fullName"],
                        "teamId": team_id
                    }
            except: continue

        pids = list(all_players_metadata.keys())
        batch_size = 160 
        all_operations = []

        print(f"Syncing {len(pids)} players with Positions and Stats...")
        
        for i in range(0, len(pids), batch_size):
            batch = pids[i : i + batch_size]
            ids_str = ",".join(map(str, batch))
            
            stats_url = (
                f"https://statsapi.mlb.com/api/v1/people?personIds={ids_str}"
                f"&hydrate=stats(group=[hitting,pitching,fielding],type=[yearByYear])"
            )
            
            try:
                response = requests.get(stats_url).json()
                people = response.get("people", [])

                for person in people:
                    player_id = person["id"]
                    meta = all_players_metadata.get(player_id, {})
                    
                    stats_groups = person.get("stats", [])
                    yearly_stats, pos_string = get_stats_for_years(stats_groups, target_years)
                    
                    # --- FALLBACK LOGIC ---
                    if not pos_string:
                        primary = person.get("primaryPosition", {})
                        raw_primary = primary.get("abbreviation")
                        
                        if raw_primary in ["LF", "CF", "RF", "OF"]:
                            pos_string = "OF"
                        elif raw_primary in ["P", "C", "1B", "2B", "3B", "SS"]:
                            pos_string = raw_primary
                        elif raw_primary in ["DH", "TW"]:
                            pos_string = "UT"

                    all_operations.append(UpdateOne(
                        {"mlbId": player_id},
                        {
                            "$set": {
                                "mlbId": player_id,
                                "fullName": meta.get("fullName"),
                                "searchName": meta.get("fullName", "").lower().strip(),
                                "currentTeamId": meta.get("teamId"),
                                "currentAge": person.get("currentAge"),
                                "positions": pos_string,
                                "headshotUrl": f"https://securea.mlb.com/mlb/images/players/head_shot/{player_id}.jpg",
                                "statsHistory": yearly_stats,
                                "lastUpdated": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                        },
                        upsert=True
                    ))
                print(f"Processed batch {i//batch_size + 1}")
            except Exception as e:
                print(f"Error in batch: {e}")

        if all_operations:
            players_col.bulk_write(all_operations)
            players_col.create_index([("searchName", ASCENDING)])
            print("Sync complete. Position data for 2025 is now live.")

        client.close()
    except Exception as e:
        print(f"Critical Failure: {e}")

if __name__ == "__main__":
    sync_mlb_players()