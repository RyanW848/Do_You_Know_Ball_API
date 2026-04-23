import os
from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from core.auth import auth_bp
from core.api_keys import api_keys_bp, get_api_keys_collection
from core.db import get_players_collection
from services.mlb_service import get_player_bio, get_player_stats, get_team_details, get_all_teams, get_team_roster, get_transactions
from services.valuation import compute_valuation
from services.helpers import find_player_id, convert_to_player_ids

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://www.citrus-kit.com"])
app.json.sort_keys = False
app.register_blueprint(auth_bp)
app.register_blueprint(api_keys_bp)

# Require API key for all routes 
@app.before_request
def require_api_key():
    if os.environ.get("ENVIRONMENT") != "production":
        return None
    if request.method == "OPTIONS":
        return None
    if request.path in ["/register", "/login", "/api-keys/generate", "/", "/license"] or request.path.startswith("/static"):
        return None
    
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "API key required"}), 401
    
    api_keys_collection = get_api_keys_collection()

    key_doc = api_keys_collection.find_one({"api_key": api_key})
    if not key_doc:
        return jsonify({"error": "Invalid API key"}), 401
    
    # --- BILLING CALCULATION ---
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Reset count if it's a new day
    if key_doc.get("last_reset") != today:
        api_keys_collection.update_one(
            {"api_key": api_key},
            {"$set": {"daily_requests": 0, "last_reset": today}}
        )
        key_doc["daily_requests"] = 0

    # 100 free, then $0.01 per request
    inc_query = {"daily_requests": 1}
    if key_doc["daily_requests"] >= 100:
        inc_query["balance"] = 0.01

    # Update DB
    updated_doc = api_keys_collection.find_one_and_update(
        {"api_key": api_key},
        {"$inc": inc_query},
        return_document=True
    )

    g.billing_info = {
        "remaining": max(0, 100 - updated_doc["daily_requests"]),
        "balance": updated_doc["balance"]
    }
    
@app.after_request
def add_billing_headers(response):
    if hasattr(g, 'billing_info'):
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(g.billing_info["remaining"])
        response.headers["X-Billing-Balance"] = f"${g.billing_info['balance']:.2f}"
    return response
    
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"!!! SERVER ERROR: {str(e)}")
    
    code = 500
    if hasattr(e, 'code'):
        code = e.code

    return jsonify({
        "error": "Internal Server Error",
        "message": str(e),
        "status": code
    }), code

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
    name = request.args.get("name")
    age = request.args.get("age")

    mlb_id_name, error = find_player_id(name, age)

    if error:
        status = error.pop("status")
        return jsonify(error), status

    return jsonify(mlb_id_name)

# Returns all player names and their IDs
@app.route("/players")
def all_players():
    players_collection = get_players_collection()
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

# This endpoint takes a comma-separated list of player IDs and an optional year, and returns their stats
@app.route("/stats")
def player_stats():
    players_param = request.args.get("players")
    year = request.args.get("year", "2025")

    if not players_param:
        return jsonify({"error": "Missing 'players' parameter"}), 400
    
    player_ids = convert_to_player_ids([player.strip() for player in players_param.split(",")])
    
    all_players_data = []
    team_cache = {}

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
    
# Returns a list of all 30 AL/NL teams with their IDs
@app.route("/teams")
def get_mlb_teams():
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
    today_iso = datetime.now().strftime("%Y-%m-%d")
    
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
    data = request.get_json()
    
    players_collection = get_players_collection()
    all_players = list(players_collection.find({}))
    
    results = compute_valuation(all_players, data)

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host="0.0.0.0", port=port)