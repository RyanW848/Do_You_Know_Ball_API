import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from core.auth import auth_bp
from core.api_keys import api_keys_bp, api_keys_collection
from core.db import players_collection
from services.mlb_service import get_player_bio, get_player_stats, get_team_details, get_all_teams, get_team_roster, get_transactions

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://www.citrus-kit.com"])
app.json.sort_keys = False
app.register_blueprint(auth_bp)
app.register_blueprint(api_keys_bp)

# Require API key for all routes 
@app.before_request
def require_api_key():
    if request.method == "OPTIONS":
        return None
    if request.path in ["/register", "/login", "/api-keys/generate", "/", "/license"]:
        return None
    
    # api_key = request.headers.get("X-API-Key")
    # if not api_key:
    #     return jsonify({"error": "API key required"}), 401

    # key = api_keys_collection.find_one({"api_key": api_key})
    # if not key:
    #     return jsonify({"error": "Invalid API key"}), 401

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Licensing page
@app.route("/license")
def license_page():
    return render_template("license.html")

@app.route("/get-player-id")
def get_player_id():
    name_query = request.args.get("name")
    dob_query = request.args.get("dob")

    if not name_query:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    search_name = name_query.lower().strip()
    query = {"searchName": search_name}
    if dob_query:
        query["birthDate"] = dob_query
        
    def check_initial_match(query_name, players_collection, dob_query=None):
        # Clean the query name (remove periods and extra spaces)
        clean_name = query_name.replace(".", "").strip()
        parts = clean_name.split()

        if len(parts) < 2:
            return []

        first_part = parts[0]
        last_name = " ".join(parts[1:])

        # Check if the first part is an initial 
        if len(first_part) <= 2:
            regex_pattern = f"^{first_part[0]}.* {last_name}$"
            fallback_query = {"fullName": {"$regex": regex_pattern, "$options": "i"}}
            
            if dob_query:
                fallback_query["birthDate"] = dob_query
                
            return list(players_collection.find(fallback_query, {"_id": 0}))
        
        return []

    try:
        # --- Attempt 1: Exact searchName Match ---
        matches = list(players_collection.find(query, {"_id": 0}))

        # --- Attempt 2: Initial Fallback (if no matches found) ---
        if not matches:
            matches = check_initial_match(name_query, players_collection, dob_query)

        if not matches:
            return jsonify({"error": f"No player found for '{name_query}'"}), 404
        
        # --- Disambiguation / Results logic remains the same ---
        if len(matches) > 1 and not dob_query:
            return jsonify({
                "error": "Multiple players found with that name.",
                "message": "Please provide a 'dob' parameter (YYYY-MM-DD) to disambiguate.",
                "options": [
                    {"fullName": p["fullName"], "birthDate": p.get("birthDate")} 
                    for p in matches
                ]
            }), 300

        player = matches[0]
        return jsonify({
            "fullName": player["fullName"],
            "mlbId": player["mlbId"],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Returns all player names and their IDs
@app.route("/players")
def all_players():
    try:
        cursor = players_collection.find({}, {"_id": 0, "fullName": 1, "mlbId": 1, "headshotUrl": 1, "positions": 1})

        player_list = []
        for p in cursor:
            player_list.append({
                "name": p.get("fullName"),
                "id": p.get("mlbId"),
                "headshotUrl": p.get("headshotUrl"),
                "positions": p.get("positions")
            })
            
        player_list.sort(key=lambda x: x["name"])

        return jsonify({
            "count": len(player_list),
            "players": player_list
        })

    except Exception as e:
        print(f"Error fetching all players: {e}")
        return jsonify({"error": "Internal server error"}), 500

# This endpoint takes a comma-separated list of player IDs and an optional year, and returns their stats
@app.route("/player-stats")
def player_stats():
    ids_param = request.args.get("ids")
    year = request.args.get("year", "2025")

    if not ids_param:
        return jsonify({"error": "Missing 'ids' parameter"}), 400

    player_ids = [pid.strip() for pid in ids_param.split(",")]
    
    all_players_data = []
    team_cache = {}

    try:
        for player_id in player_ids:
            # 1. Bio for Position
            person = get_player_bio(player_id)
            if not person:
                continue # Skip if ID is invalid
                
            position = person.get("primaryPosition", {}).get("name", "Unknown")
            full_name = person.get("fullName")

            # 2. Stats (Hitting & Pitching)
            stats_json = get_player_stats(player_id, year)
            if not stats_json:
                continue

            merged_stats = {}
            player_team_info = {}

            for group_data in stats_json.get("stats", []):
                splits = group_data.get("splits", [])
                if not splits:
                    continue
                
                s = splits[0]
                current_stats = s.get("stat", {})
                t_id = s["team"]["id"]

                # 3. Handle Team Info & Abbreviation 
                if not player_team_info:
                    if t_id not in team_cache:
                        t_data = get_team_details(t_id)
                        team_cache[t_id] = {
                            "id": t_id,
                            "name": s["team"]["name"],
                            "abbreviation": t_data.get("abbreviation") if t_data else "N/A"
                        }
                    player_team_info = team_cache[t_id]

                # 4. Merging Logic
                for key, value in current_stats.items():
                    if key == "age": 
                        merged_stats[key] = value 
                        continue   
                    if isinstance(value, (int, float)):
                        merged_stats[key] = merged_stats.get(key, 0) + value
                    else:
                        merged_stats[key] = value

            # Append this player's compiled data to our main list
            all_players_data.append({
                "player": {
                    "id": player_id,
                    "name": full_name,
                    "position": position
                },
                "team": player_team_info,
                "year": year,
                "stats": merged_stats
            })

        return jsonify({
            "count": len(all_players_data),
            "results": all_players_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Returns a list of all 30 AL/NL teams with their IDs
@app.route("/teams")
def get_mlb_teams():
    try:
        data = get_all_teams()
        if not data or "teams" not in data:
            return jsonify({"error": "Failed to fetch teams"}), 502

        teams_list = []
        for team in data.get("teams", []):
            teams_list.append({
                "id": team.get("id"),
                "name": team.get("name"),
                "abbreviation": team.get("abbreviation"),
            })

        teams_list.sort(key=lambda x: x["name"])

        return jsonify({
            "count": len(teams_list),
            "teams": teams_list
        })

    except Exception as e:
        print(f"Error fetching teams: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Also gets injuries
@app.route("/depth-chart")
def get_depth_chart():
    team_id = request.args.get("teamId")
    
    if not team_id:
        return jsonify({"error": "Missing teamId parameter"}), 400

    data = get_team_roster(team_id)

    if "roster" not in data:
        return jsonify({"error": f"No roster data found for team {team_id}"}), 404

    organized_depth_chart = {}

    for entry in data["roster"]:
        pos_name = entry["position"]["name"]
        
        player_entry = {
            "id": entry["person"]["id"],
            "name": entry["person"]["fullName"],
            "status": entry["status"]["description"]
        }

        if pos_name not in organized_depth_chart:
            organized_depth_chart[pos_name] = []
        
        organized_depth_chart[pos_name].append(player_entry)

    return jsonify({
        "teamId": team_id,
        "positions": organized_depth_chart
    })

   
@app.route("/transactions")
def get_daily_transactions():
    today_iso = datetime.now().strftime("%Y-%m-05")
    
    data = get_transactions(today_iso)

    if not data:
        return jsonify({"error": "Failed to fetch data from MLB"}), 502
        
    raw_transactions = data.get("transactions", [])

    results = []
    for tx in raw_transactions:
        results.append({
            "playerId": tx.get("person", {}).get("id"),
            "playerName": tx.get("person", {}).get("fullName"),
            "fromTeam": tx.get("fromTeam", {}).get("name"),
            "fromTeamId": tx.get("fromTeam", {}).get("id"),
            "toTeam": tx.get("toTeam", {}).get("name"),
            "toTeamId": tx.get("toTeam", {}).get("id"),
            "description": tx.get("description")
        })

    return jsonify({
        "date": today_iso,
        "count": len(results),
        "transactions": results
    })
    

@app.route('/value', methods=['POST'])
def value_players():
    def get_age_multiplier(age):
        if age > 35:
            return 0.9
        elif 25 <= age <= 30:
            return 1.05
        else:
            return 1

    def get_versatility_multiplier(pos_count):
        return 0.05 * pos_count + 0.95
    
    def get_injury_multiplier(inj):
        injury_map = {
            'D7': 0.9, '7D': 0.9, 'D10': 0.8, '10D': 0.8,
            'D15': 0.7, '15D': 0.7, 'D60': 0.3, '60D': 0.3
        }
        return injury_map.get(inj, 1.0)
    
    def get_depth_multiplier(depth_map):
        if not depth_map:
            return 0.5
        multiplier = max(
            1.3 * (0.9 ** (x_rank - 1)) 
            for x_rank in depth_map.values()
        )
        return multiplier
    
    def get_scaled_score(avg_rank, total_players):
        avg_players = total_players / 2
        return 0.25 + (avg_players - avg_rank) / avg_players
            
    data = request.get_json()
    budget = data.get('budget', 0)
    players_left = data.get('players_left_to_draft', 1)
    avg_player_budget = budget / players_left if players_left > 0 else 0
    unavailable_ids = data.get('unavailable_player_ids', [])
    target_player_ids = data.get('player_ids', [])
    raw_stats = data.get('relevant_stats', "")
    relevant_stats = [s.strip() for s in raw_stats.split(',') if s.strip()]

    if not relevant_stats:
        return jsonify({"error": "No relevant_stats provided"}), 400

    all_players = list(players_collection.find({}))
    available_players = [p for p in all_players if p.get("mlbId") not in unavailable_ids]
    results = []
    
    if target_player_ids:
        players_to_calculate = [p for p in available_players if p.get("mlbId") in target_player_ids]
    else:
        players_to_calculate = available_players

    total_in_db = len(available_players)

    for p in players_to_calculate:
        depth_map = p.get('depthRanks', {})
        
        # --- 1. CALCULATE BASE SCORE ---
        rank_sum = 0
        stat_count = 0
        for stat in relevant_stats:
            rank = p.get('statRanks', {}).get(stat)
            if rank:
                rank_sum += rank
                stat_count += 1
        
        # FALLBACK: If they have NO stats, give them the worst possible average rank
        if stat_count == 0:
            avg_rank = total_in_db 
        else:
            avg_rank = rank_sum / stat_count

        # Scale
        scaled_base = get_scaled_score(avg_rank, total_in_db)

        # DEPTH CHART LOGIC 
        depth_chart_multiplier = get_depth_multiplier(depth_map)

        # Age Multipliers
        age = p.get('currentAge', 20)
        age_multiplier = get_age_multiplier(age) 
        
        # Versatility: Use 1 as default if not in depth chart
        pos_count = len(depth_map) if depth_map else 1
        versatility_multiplier = get_versatility_multiplier(pos_count)

        # Injury Multiplier
        inj = p.get('injuryStatus', 'A')
        injury_multiplier = get_injury_multiplier(inj)

        final_score = scaled_base * depth_chart_multiplier * age_multiplier * versatility_multiplier * injury_multiplier
        
        player_value = final_score * avg_player_budget

        results.append({
            "mlbId": p.get("mlbId"),
            "fullName": p.get("fullName"),
            "score": round(final_score, 4),
            "value": round(player_value, 0),
        })

    results.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        "budget": budget,
        "relevant_stats": relevant_stats,
        "player_count": len(results),
        "results": results
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host="0.0.0.0", port=port)