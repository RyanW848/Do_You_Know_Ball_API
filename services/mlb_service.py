import requests

BASE_URL = "https://statsapi.mlb.com/api/v1"

def mlb_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=10)
        
        response.raise_for_status() 
        
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"MLB API Error: {e}")
        return None

def get_player_bio(player_id):
    data = mlb_get(f"people/{player_id}")
    return data["people"][0] if data and data.get("people") else None

def get_player_stats(player_id, year, groups="hitting,pitching"):
    params = {"stats": "season", "season": year, "group": groups}
    return mlb_get(f"people/{player_id}/stats", params=params)

def get_team_details(team_id):
    data = mlb_get(f"teams/{team_id}")
    return data["teams"][0] if data and data.get("teams") else None

def get_all_teams():
    return mlb_get("teams", params={"sportId": 1})
  
def get_team_roster(team_id, roster_type="depthChart"):
    params = {
        "rosterType": roster_type,
        "season": "2026"
    }
    return mlb_get(f"teams/{team_id}/roster", params=params)
  
def get_transactions(date_str):
  return mlb_get("transactions", params={"date": date_str, "sportId": 1})

# services/mlb_service.py

def get_players_with_stats(player_ids_str, groups="hitting,pitching,fielding", stat_type="yearByYear"):
    params = {
        "personIds": player_ids_str,
        "hydrate": f"stats(group=[{groups}],type=[{stat_type}])"
    }
    return mlb_get("people", params=params) or {}