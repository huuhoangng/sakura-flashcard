# demo1/controllers/collection.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.collection import Collection
from extensions import db
from utils.logger import log_action

collection_bp = Blueprint('collection', __name__)

@collection_bp.route('/', methods=['GET'])
@jwt_required()
def get_my_collections():
    """Fetch all collections owned by the authenticated user."""
    user_id = int(get_jwt_identity())
    
    collections = Collection.query.filter_by(user_id=user_id).all()
    
    result = [
        {
            "id": c.id, 
            "name": c.name, 
            "user_id": c.user_id, 
            "owner_username": c.user.username, 
            "status": c.status,
            "flashcard_count": len(c.flashcards)
        } 
        for c in collections
    ]
    
    return jsonify(result), 200

@collection_bp.route('/<int:col_id>', methods=['GET'])
@jwt_required()
def get_collection(col_id):
    """Fetch a single collection by its ID."""
    user_id = int(get_jwt_identity())
    col = Collection.query.get_or_404(col_id)
    
    from models.user import User
    user = User.query.get(user_id)
    is_admin = user and user.role == 'admin'
    
    # Authorization check: Deny if it's private AND the user is not the owner
    if not is_admin and col.status != 'public' and col.user_id != user_id:
        return jsonify({"msg": "Unauthorized to view this collection."}), 403
        
    return jsonify({
        "id": col.id,
        "name": col.name,
        "user_id": col.user_id,
        "owner_username": col.user.username,
        "status": col.status,
        "flashcard_count": len(col.flashcards)
    }), 200

@collection_bp.route('/', methods=['POST'])
@jwt_required()
def create_collection():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    new_col = Collection(
        name=data['name'],
        user_id=user_id,
        status=data.get('status', 'private')
    )
    db.session.add(new_col)
    db.session.commit()
    
    log_action(user_id, f"Created collection {new_col.id} - {new_col.name}")
    return jsonify({"msg": "Collection created", "id": new_col.id}), 201

@collection_bp.route('/<int:col_id>', methods=['PUT'])
@jwt_required()
def edit_collection(col_id):
    user_id = str(get_jwt_identity())
    col = Collection.query.get_or_404(col_id)
    
    from models.user import User
    user = User.query.get(int(user_id))
    is_admin = user and user.role == 'admin'
    
    if not is_admin and str(col.user_id) != user_id:
        return jsonify({"msg": "Unauthorized. You can only edit your own collections."}), 403
    
    data = request.get_json()
    if 'name' in data:
        col.name = data['name']
    if 'status' in data:
        col.status = data['status']
        
    db.session.commit()
    log_action(user_id, f"Edited collection {col.id} - {col.name}")
    return jsonify({"msg": "Collection updated"}), 200


@collection_bp.route('/user/<int:target_user_id>', methods=['GET'])
@jwt_required()
def get_user_public_collections(target_user_id):
    collections = Collection.query.filter_by(
        user_id=target_user_id, 
        status='public'
    ).all()
    
    result = [
        {
            "id": c.id, 
            "name": c.name, 
            "user_id": c.user_id, 
            "owner_username": c.user.username, 
            "status": c.status,
            "flashcard_count": len(c.flashcards)
        } 
        for c in collections
    ]
    return jsonify(result), 200

@collection_bp.route('/user/<string:username>', methods=['GET'])
@jwt_required()
def get_user_public_collections_by_username(username):
    from models.user import User
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    collections = Collection.query.filter_by(
        user_id=user.id, 
        status='public'
    ).all()
    
    result = [
        {
            "id": c.id, 
            "name": c.name, 
            "user_id": c.user_id, 
            "owner_username": c.user.username, 
            "status": c.status,
            "flashcard_count": len(c.flashcards)
        } 
        for c in collections
    ]
    return jsonify(result), 200