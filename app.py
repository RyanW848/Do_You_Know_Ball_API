import os
import json
from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from core.auth import auth_bp
from core.api_keys import api_keys_bp, check_valid, calculate_billing_info, check_rate_limit, get_api_keys_collection
from core.db import get_players_collection
from services.mlb_service import get_team_details, get_all_teams, get_team_roster, get_transactions
from services.valuation import compute_valuation
from services.helpers import find_player_id, convert_to_player_ids

load_dotenv()

app = Flask(__name__)
# CORS(app, supports_credentials=True, origins=["http://localhost:3000", "https://www.citrus-kit.com"])
CORS(app, origins="*")
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
    
    bypass_token = request.args.get("bypass")
    if bypass_token and bypass_token == os.environ.get("BYPASS_TOKEN"):
        return None
    
    exempt_paths = ["/register", "/login", "/", "/license"]
    exempt_prefixes = ["/static", "/api-keys"]
    if request.path in exempt_paths or any(request.path.startswith(prefix) for prefix in exempt_prefixes):
        return None
    
    api_key = request.headers.get("X-API-Key")
    
    key_doc, error = check_valid(api_key)
    if error:
        return jsonify({"error": error}), 401   
    
    valid, error = check_rate_limit(key_doc, api_key)
    if error:
        return jsonify({"error": error}), 429
    
    calculate_billing_info(key_doc, api_key)
    return None
    
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

@app.route("/api-keys")
def api_keys_page():
    return render_template("api-keys.html")

@app.route("/api/user-api-key", methods=["GET"])
def get_user_api_key():
    username = request.cookies.get("username")
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    api_keys_collection = get_api_keys_collection()
    key_doc = api_keys_collection.find_one({"username": username})
    
    if not key_doc:
        return jsonify({"error": "No API key found"}), 404
    
    return jsonify({"api_key": key_doc["api_key"]}), 200

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
    players_collection = get_players_collection()
    
    cache_path = os.path.join(app.root_path, "data", "stats_cache.json")

    # If asking for ALL players (no param), just serve the file
    if not players_param:
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({"error": "Cache not ready"}), 503
    else:
        names_or_ids = [p.strip() for p in players_param.split(",") if p.strip()]
        player_ids = convert_to_player_ids(names_or_ids)

    if not player_ids:
        return jsonify({"count": 0, "results": []})
    
    all_players_data = []
    team_cache = {}

    for player_id in player_ids:
        # 2. Fetch Bio and Pre-calculated Stats from MongoDB
        player_doc = players_collection.find_one({"mlbId": player_id})
        
        if not player_doc:
            continue
            
        full_name = player_doc.get("fullName")
        position = player_doc.get("positions", "Unknown")
        injury_status = player_doc.get("injuryStatus", "A")
        t_id = player_doc.get("currentTeamId")
        
        # Pull the stats we saved during the sync script
        # Using .get() for safety in case a player has no stats for that year
        merged_stats = player_doc.get("raw_2025", {})

        # 3. Handle Team Info & Abbreviation (The logic you wanted kept)
        player_team_info = {}
        if t_id:
            if t_id not in team_cache:
                t_data = get_team_details(t_id)
                team_cache[t_id] = {
                    "id": t_id,
                    "name": t_data.get("name") if t_data else "Unknown",
                    "abbreviation": t_data.get("abbreviation") if t_data else "N/A"
                }
            player_team_info = team_cache[t_id]
        else:
            player_team_info = {"id": None, "name": "Free Agent", "abbreviation": "FA"}

        # 4. Append to results in the exact same format as before
        all_players_data.append({
            "player": {
                "id": player_id,
                "name": full_name,
                "position": position,
                "injuryStatus": injury_status
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