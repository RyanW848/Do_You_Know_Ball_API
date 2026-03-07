import os
from flask import Flask, jsonify, request, render_template
import statsapi
from dotenv import load_dotenv
from auth import auth_bp
from api_keys import api_keys_bp, api_keys_collection

load_dotenv()

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(api_keys_bp)

# Require API key for all routes 
@app.before_request
def require_api_key():
    if request.path in ["/register", "/login", "/api-keys/generate", "/", "/license"]:
        return None
    
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "API key required"}), 401

    key = api_keys_collection.find_one({"api_key": api_key})
    if not key:
        return jsonify({"error": "Invalid API key"}), 401

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Licensing page
@app.route("/license")
def license_page():
    return render_template("license.html")

# Return all player names
@app.route("/players")
def all_players():
    try:
        search = request.args.get("search", "a") 
        players = statsapi.lookup_player(search)
        names = [p['firstLastName'] for p in players]
        return jsonify({"players": names})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Return player stats by name
@app.route("/player")
def player():
    player_name = request.args.get("name")
    if not player_name:
        return jsonify({"error": "Please provide ?name=Player Name"}), 400

    try:
        players = statsapi.lookup_player(player_name)
        if not players:
            return jsonify({"error": "Player not found"}), 404

        selected_player = players[0]
        player_id = selected_player["id"]

        stats = statsapi.player_stat_data(player_id, group="[hitting,pitching]", type="career")
        
        return jsonify({
            "id": player_id,
            "fullName": selected_player.get("fullName"),
            "stats": stats
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host="0.0.0.0", port=port)