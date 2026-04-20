from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.collection import Collection
from models.flashcard import Flashcard

search_bp = Blueprint('search', __name__)

@search_bp.route('/', methods=['POST'])
@jwt_required()
def global_search():
    user_id = int(get_jwt_identity())
    current_user = User.query.get(user_id)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
        
    role = current_user.role

    data = request.get_json() or {}
    text = data.get('text', '')
    # Default to returning all if not specified
    objects_search_list = data.get('objects_search_list', ['users', 'collections', 'flashcards'])

    result = {}

    # Users Search
    if 'users' in objects_search_list:
        users_query = User.query.filter(
            User.username.ilike(f'%{text}%')
        )
        users = users_query.all()
        result['users'] = [
            {"id": u.id, "username": u.username, "role": u.role} 
            for u in users
        ]

    # Collections Search
    if 'collections' in objects_search_list:
        cols_query = Collection.query.filter(Collection.name.ilike(f'%{text}%'))
        if role != 'admin':
            cols_query = cols_query.filter(
                (Collection.status == 'public') | (Collection.user_id == user_id)
            )
        collections = cols_query.all()
        result['collections'] = [
            {
                "id": c.id, 
                "name": c.name, 
                "user_id": c.user_id, 
                "owner_username": c.user.username, 
                "status": c.status,
                "flashcard_count": len(c.flashcards)
            } for c in collections
        ]

    # Flashcards Search
    if 'flashcards' in objects_search_list:
        cards_query = Flashcard.query.join(Collection).filter(
            (Flashcard.front.ilike(f'%{text}%')) | (Flashcard.back.ilike(f'%{text}%'))
        )
        if role != 'admin':
            cards_query = cards_query.filter(
                (Collection.status == 'public') | (Collection.user_id == user_id)
            )
        cards = cards_query.all()
        result['flashcards'] = [
            {
                "id": c.id, 
                "front": c.front, 
                "back": c.back, 
                "status": c.status, 
                "collection_id": c.collection_id
            } for c in cards
        ]

    return jsonify(result), 200
