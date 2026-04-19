from flask import Blueprint, request, jsonify
from core.db import db
import jwt
import os
import secrets
from datetime import datetime

api_keys_bp = Blueprint("api_keys", __name__)
api_keys_collection = db["api_keys"]

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

    api_key = secrets.token_hex(32)

    api_keys_collection.insert_one({
        "username": username,
        "api_key": api_key,
        "daily_requests": 0,
        "balance": 0.0,
        "last_reset": datetime.now().strftime("%Y-%m-%d")
    })

    return jsonify({"api_key": api_key}), 201