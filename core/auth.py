from flask import Blueprint, request, jsonify, render_template, make_response
from core.db import get_users_collection
import bcrypt
import jwt
import datetime
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
 
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
 
    users_collection = get_users_collection()
    user = users_collection.find_one({"username": username})
 
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
 
    token = jwt.encode({
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, os.environ.get("JWT_SECRET"), algorithm="HS256")
 
    response = make_response(jsonify({"message": "Login successful", "username": username, "token": token}), 200)
    
    response.set_cookie("token", token, max_age=7*24*60*60, httponly=True, path="/")
    response.set_cookie("username", username, max_age=7*24*60*60, httponly=False, path="/")
    
    return response
 
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
 
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    users_collection = get_users_collection()
 
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 409
 
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
 
    users_collection.insert_one({
        "username": username,
        "password": hashed,
    })
 
    return jsonify({"message": "User created successfully"}), 201