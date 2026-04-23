from core.db import get_players_collection
import unicodedata

def normalize_text(text):
    if not text:
        return ""
    return "".join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

def find_player_id(name_query, age_query=None, players=None):
    if not name_query:
        return None, {"error": "Missing 'name' parameter", "status": 400}

    search_name = normalize_text(name_query)
    query = {"searchName": search_name}
    if age_query:
        query["currentAge"] = int(age_query)

    projection = {"mlbId": 1, "fullName": 1, "currentAge": 1, "_id": 0}

    # Attempt 1: Exact searchName Match
    if players is not None:
        matches = [
            {
                "mlbId": p.get("mlbId"),
                "fullName": p.get("fullName"),
                "currentAge": p.get("currentAge")
            }
            for p in players
            if normalize_text(p.get("fullName")) == search_name
            and (not age_query or p.get("currentAge") == int(age_query))
        ]
    else:
        players_collection = get_players_collection()
        matches = list(players_collection.find(query, projection))

    # Attempt 2: Initial Fallback
    if not matches:
        parts = search_name.split()

        if len(parts) >= 2:
            first_initial = parts[0][0]
            last_name = " ".join(parts[1:])
            
            regex_pattern = f"^{first_initial}.* {last_name}"
            
            fallback_query = {"searchName": {"$regex": regex_pattern}}
            if age_query:
                fallback_query["currentAge"] = int(age_query)
            
            if players is not None:
                matches = [
                    {
                        "mlbId": p.get("mlbId"),
                        "fullName": p.get("fullName"),
                        "currentAge": p.get("currentAge")
                    }
                    for p in players
                    if normalize_text(p.get("fullName")).startswith(f"{first_initial}")
                    and last_name in normalize_text(p.get("fullName"))
                ]
            else:
                matches = list(players_collection.find(fallback_query, projection))

    if not matches:
        return None, {"error": f"No player found for '{name_query}'", "status": 404}
    
    if len(matches) > 1 and not age_query:
        return None, {
            "error": "Multiple players found",
            "options": [{"fullName": p["fullName"], "mlbId": p["mlbId"], "currentAge": p.get("currentAge")} for p in matches],
            "status": 300
        }

    return matches[0], None
  
def convert_to_player_ids(player_list, players=None):
    resolved_ids = []

    for item in player_list:
        if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
            resolved_ids.append(int(item))
        
        elif isinstance(item, str):
            player_data, error = find_player_id(item, players=players)
            
            if player_data:
                resolved_ids.append(player_data['mlbId'])
            elif error and "options" in error:
                first_option_id = error['options'][0].get('mlbId')
                resolved_ids.append(first_option_id)
            # else:
            #     resolved_ids.append(item) 
                
    return resolved_ids
