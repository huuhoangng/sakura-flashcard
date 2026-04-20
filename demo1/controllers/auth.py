from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from extensions import db
from utils.logger import log_action

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/check', methods=['GET'])
@jwt_required()
def check_auth():
    """
    Checks if the currently authenticated user's token is valid.
    """
    return jsonify({"valid": True}), 200

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password_hash=hashed_pw, role=data.get('role', 'user'))
    db.session.add(new_user)
    db.session.commit()
    
    log_action(new_user.id, "User signed up")
    return jsonify({"msg": "User created"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        log_action(user.id, "User logged in")
        return jsonify({
            "access_token": access_token,
            "role": user.role
        }), 200
    return jsonify({"msg": "Bad credentials"}), 401

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({"msg": "Old password is incorrect"}), 400
    
    if len(new_password) < 4:
        return jsonify({"msg": "New password must be at least 4 characters"}), 400
    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    log_action(user_id, "User changed password")
    return jsonify({"msg": "Password changed successfully"}), 200