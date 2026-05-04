from flask import Blueprint, request, jsonify, g
from core.db import get_db
import jwt
import os
import secrets
from datetime import datetime, timedelta
import time

api_keys_bp = Blueprint("api_keys", __name__)

def get_api_keys_collection():
    return get_db()["api_keys"]

def get_username_from_token(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None
    try:
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
        return decoded.get("username")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@api_keys_bp.route("/api-keys/generate", methods=["POST"])
def generate_api_key():
    username = get_username_from_token(request)
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    api_keys_collection = get_api_keys_collection()
    
    existing_key = api_keys_collection.find_one({"username": username})
    if existing_key:
        return jsonify({"error": "User already has an API key"}), 409

    api_key = secrets.token_hex(32)

    api_keys_collection.insert_one({
        "username": username,
        "api_key": api_key,
        "daily_requests": 0,
        "balance": 0.0,
        "last_reset": datetime.now().strftime("%Y-%m-%d")
    })

    return jsonify({"api_key": api_key}), 201

@api_keys_bp.route("/api-keys/status", methods=["GET"])
def get_api_key_status():
    username = request.cookies.get("username")
    if not username:
        return jsonify({"error": "Unauthorized"}), 401

    api_keys_collection = get_api_keys_collection()
    key_data = api_keys_collection.find_one({"username": username})

    if not key_data:
        return jsonify({"has_key": False}), 200

    return jsonify({
        "has_key": True,
        "username": key_data.get("username"),
        "daily_requests": key_data.get("daily_requests", 0),
        "requests_left": max(0, 100 - key_data.get("daily_requests", 0)),
        "balance": key_data.get("balance", 0.0)
    }), 200
    
def calculate_billing_info(key_doc, api_key):
    api_keys_collection = get_api_keys_collection()
  
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
    
def check_valid(api_key):
    if not api_key:
        return None, "API key required"
    
    api_keys_collection = get_api_keys_collection()
    key_doc = api_keys_collection.find_one({"api_key": api_key})
    
    if not key_doc:
        return None, "Invalid API key"
    
    return key_doc, None

def check_rate_limit(key_doc, api_key, max_requests=100, window_seconds=60):
    api_keys_collection = get_api_keys_collection()
    
    now = time.time()
    cutoff = now - window_seconds
    
    # Get requests from the last X seconds
    request_times = key_doc.get("request_times", [])
    recent_requests = [t for t in request_times if t > cutoff]
    
    # Check if over limit
    if len(recent_requests) >= max_requests:
        return False, f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds"
    
    # Add current request timestamp
    recent_requests.append(now)
    
    api_keys_collection.update_one(
        {"api_key": api_key},
        {"$set": {"request_times": recent_requests}}
    )
    
    return True, None