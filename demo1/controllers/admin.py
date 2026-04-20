from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.action_log import ActionLog
from models.collection import Collection
from models.flashcard import Flashcard
from extensions import db
from utils.decorators import admin_required
from utils.logger import log_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@admin_required()
def get_logs():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', '')
    order = request.args.get('order', 'asc')
    
    query = ActionLog.query
    if q:
        query = query.filter(ActionLog.action.ilike(f'%{q}%'))
        
    if sort_by == 'user_id':
        query = query.order_by(ActionLog.user_id.desc() if order == 'desc' else ActionLog.user_id.asc())
    elif sort_by == 'action':
        query = query.order_by(ActionLog.action.desc() if order == 'desc' else ActionLog.action.asc())
    elif sort_by == 'time':
        query = query.order_by(ActionLog.timestamp.desc() if order == 'desc' else ActionLog.timestamp.asc())
    elif sort_by == 'id':
        query = query.order_by(ActionLog.id.desc() if order == 'desc' else ActionLog.id.asc())
    else:
        query = query.order_by(ActionLog.timestamp.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [{"id": l.id, "user_id": l.user_id, "action": l.action, "time": l.timestamp} for l in paginated.items],
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": paginated.page
    }), 200

@admin_bp.route('/user/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(target_user_id):
    user = User.query.get_or_404(target_user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_action(get_jwt_identity(), f"Admin deleted user {target_user_id} - {username}")
    return jsonify({"msg": "User deleted"}), 200


@admin_bp.route('/users/search', methods=['GET'])
@jwt_required()
@admin_required()
def search_users():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f'%{q}%'))
        
    if sort_by == 'username':
        query = query.order_by(User.username.desc() if order == 'desc' else User.username.asc())
    elif sort_by == 'role':
        query = query.order_by(User.role.desc() if order == 'desc' else User.role.asc())
    else:
        query = query.order_by(User.id.desc() if order == 'desc' else User.id.asc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [{"id": u.id, "username": u.username, "role": u.role} for u in paginated.items],
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": paginated.page
    }), 200

@admin_bp.route('/collections', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_collections():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    query = Collection.query
    if q:
        query = query.filter(Collection.name.ilike(f'%{q}%'))
        
    if sort_by == 'name':
        query = query.order_by(Collection.name.desc() if order == 'desc' else Collection.name.asc())
    elif sort_by == 'user_id':
        query = query.order_by(Collection.user_id.desc() if order == 'desc' else Collection.user_id.asc())
    else:
        query = query.order_by(Collection.id.desc() if order == 'desc' else Collection.id.asc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [{"id": c.id, "name": c.name, "user_id": c.user_id, "status": c.status} for c in paginated.items],
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": paginated.page
    }), 200

@admin_bp.route('/collections/<int:col_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_collection(col_id):
    col = Collection.query.get_or_404(col_id)
    name = col.name
    db.session.delete(col)
    db.session.commit()
    
    log_action(get_jwt_identity(), f"Admin deleted collection {col_id} - {name}")
    return jsonify({"msg": "Collection deleted"}), 200

@admin_bp.route('/flashcards/search', methods=['GET'])
@jwt_required()
@admin_required()
def search_flashcards():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    query = Flashcard.query
    if q:
        query = query.filter(Flashcard.front.ilike(f'%{q}%'))
        
    if sort_by == 'front':
        query = query.order_by(Flashcard.front.desc() if order == 'desc' else Flashcard.front.asc())
    elif sort_by == 'collection_id':
        query = query.order_by(Flashcard.collection_id.desc() if order == 'desc' else Flashcard.collection_id.asc())
    else:
        query = query.order_by(Flashcard.id.desc() if order == 'desc' else Flashcard.id.asc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "items": [{"id": c.id, "front": c.front, "back": c.back, "status": c.status, "collection_id": c.collection_id} for c in paginated.items],
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": paginated.page
    }), 200

@admin_bp.route('/flashcards/<int:card_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def admin_delete_flashcard(card_id):
    card = Flashcard.query.get_or_404(card_id)
    front = card.front
    db.session.delete(card)
    db.session.commit()
    
    log_action(get_jwt_identity(), f"Admin deleted flashcard {card_id} - {front}")
    return jsonify({"msg": "Flashcard deleted by admin"}), 200
