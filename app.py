import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import statsapi
import pandas as pd
from dotenv import load_dotenv
from core.auth import auth_bp
from core.api_keys import api_keys_bp, api_keys_collection

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://www.citrus-kit.com"])
app.json.sort_keys = False
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

DATASETS = {
    '2025': 'data/2025-player-NL-stats.csv',
    '3year': 'data/3Year-average-NL-stats.csv',
    'projections': 'data/projections-NL.csv',
}

@app.route('/player', methods=['GET'])
def get_player():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'name is required'}), 400

    dataset = request.args.get('dataset', '2025')
    if dataset not in DATASETS:
        return jsonify({'error': f'dataset must be one of {list(DATASETS.keys())}'}), 400

    stats = request.args.get('stats')
    requested_cols = [s.strip() for s in stats.split(',')] if stats else None

    df = pd.read_csv(DATASETS[dataset])
    match = df[df['Player'].str.lower() == name.lower()]

    if match.empty:
        return jsonify({'error': f'Player "{name}" not found'}), 404

    if requested_cols:
        invalid = [c for c in requested_cols if c not in df.columns]
        if invalid:
            return jsonify({'error': f'Invalid stats: {invalid}', 'valid': list(df.columns)}), 400
        match = match[['Player'] + requested_cols]

    return jsonify(match.to_dict(orient='records')[0])

@app.route('/players', methods=['GET'])
def get_players():
    df = pd.read_csv(DATASETS['2025'])
    return jsonify(df['Player'].tolist())

# This is for outside api

# # Return all player names
# @app.route("/players")
# def all_players():
#     try:
#         search = request.args.get("search", "a") 
#         players = statsapi.lookup_player(search)
#         names = [p['firstLastName'] for p in players]
#         return jsonify({"players": names})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# # Return player stats by name
# @app.route("/player")
# def player():
#     player_name = request.args.get("name")
#     if not player_name:
#         return jsonify({"error": "Please provide ?name=Player Name"}), 400

#     try:
#         players = statsapi.lookup_player(player_name)
#         if not players:
#             return jsonify({"error": "Player not found"}), 404

#         selected_player = players[0]
#         player_id = selected_player["id"]

#         stats = statsapi.player_stat_data(player_id, group="[hitting,pitching]", type="career")
        
#         return jsonify({
#             "id": player_id,
#             "fullName": selected_player.get("fullName"),
#             "stats": stats
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host="0.0.0.0", port=port)