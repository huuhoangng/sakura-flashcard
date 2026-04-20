from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.flashcard import Flashcard
from models.collection import Collection
from models.user import User
from extensions import db
from utils.logger import log_action
from utils.sm2 import calculate_sm2
from datetime import datetime
import random
from utils.loadDistilBERTModel import SemanticClassifier

try:
    classifier = SemanticClassifier()
except Exception as e:
    print(f"Warning: Failed to load SemanticClassifier: {e}")
    classifier = None

flashcard_bp = Blueprint('flashcard', __name__)

@flashcard_bp.route('/collection/<int:col_id>', methods=['GET'])
@jwt_required()
def get_collection_flashcards(col_id):
    user_id = int(get_jwt_identity())
    col = Collection.query.get_or_404(col_id)
    
    user = User.query.get(user_id)
    is_admin = user and user.role == 'admin'
    
    # Blocks access if the collection is private AND the requester is not the owner
    if not is_admin and col.status != 'public' and col.user_id != user_id:
        return jsonify({"msg": "Unauthorized to view this collection"}), 403
        
    cards = Flashcard.query.filter_by(collection_id=col.id).all()
    result = [{"id": c.id, "front": c.front, "back": c.back, "status": c.status} for c in cards]
    return jsonify(result), 200

@flashcard_bp.route('/', methods=['POST'])
@jwt_required()
def create_flashcard():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    col = Collection.query.get_or_404(data['collection_id'])
    user = User.query.get(user_id)
    is_admin = user and user.role == 'admin'
    
    if not is_admin and col.user_id != user_id:
        return jsonify({"msg": "Unauthorized. You don't own this collection."}), 403
        
    new_card = Flashcard(
        collection_id=col.id,
        front=data['front'],
        back=data['back'],
        status=data.get('status', 'not learn')
    )
    db.session.add(new_card)
    db.session.commit()
    log_action(user_id, f"Created flashcard {new_card.id} - {new_card.front} in collection {col.id} - {col.name}")
    return jsonify({"msg": "Flashcard created", "id": new_card.id}), 201

@flashcard_bp.route('/<int:card_id>', methods=['PUT'])
@jwt_required()
def edit_flashcard(card_id):
    user_id = int(get_jwt_identity())
    card = Flashcard.query.get_or_404(card_id)
    
    user = User.query.get(user_id)
    is_admin = user and user.role == 'admin'
    
    if not is_admin and card.collection.user_id != user_id:
        return jsonify({"msg": "Unauthorized. You don't own this flashcard."}), 403
        
    data = request.get_json()
    if 'front' in data: card.front = data['front']
    if 'back' in data: card.back = data['back']
        
    db.session.commit()
    log_action(user_id, f"Edited flashcard {card.id} - {card.front}")
    return jsonify({"msg": "Flashcard updated"}), 200

@flashcard_bp.route('/<int:card_id>', methods=['DELETE'])
@jwt_required()
def delete_flashcard(card_id):
    user_id = int(get_jwt_identity())
    card = Flashcard.query.get_or_404(card_id)
    
    user = User.query.get(user_id)
    is_admin = user and user.role == 'admin'
    
    if not is_admin and card.collection.user_id != user_id:
        return jsonify({"msg": "Unauthorized."}), 403
        
    db.session.delete(card)
    db.session.commit()
    log_action(user_id, f"Deleted flashcard {card.id} - {card.front}")
    return jsonify({"msg": "Flashcard deleted"}), 200


@flashcard_bp.route('/collection/<int:collection_id>/study', methods=['GET'])
@jwt_required()
def get_study_cards(collection_id):
    user_id = int(get_jwt_identity())
    col = Collection.query.get_or_404(collection_id)
    
    if col.status != 'public' and col.user_id != user_id:
        return jsonify({"msg": "Unauthorized to view this collection"}), 403
        
    now = datetime.utcnow()
    
    # Logic: Card needs review if it's new, currently learning, or if its next review date has passed
    due_cards = Flashcard.query.filter(
        Flashcard.collection_id == collection_id,
        (Flashcard.status == 'not learn') | 
        (Flashcard.status == 'learning') | 
        ((Flashcard.status == 'learnt') & (Flashcard.next_review_date <= now))
    ).all()
    
    result = [{
        "id": c.id, 
        "front": c.front, 
        "back": c.back, 
        "status": c.status,
        "next_review_date": c.next_review_date
    } for c in due_cards]
    
    return jsonify({
        "total_due": len(result),
        "cards": result
    }), 200


@flashcard_bp.route('/collection/<int:collection_id>/review', methods=['POST'])
@jwt_required()
def review_flashcards(collection_id):
    user_id = int(get_jwt_identity())
    col = Collection.query.get_or_404(collection_id)
    
    # 1. Verify ownership of the collection
    if col.user_id != user_id:
        return jsonify({"msg": "Unauthorized to review this collection."}), 403
        
    data = request.get_json()
    reviews = data.get('reviews', [])
    
    if not isinstance(reviews, list) or not reviews:
        return jsonify({"msg": "Please provide a valid list of 'reviews'."}), 400
        
    results = []
    
    for review in reviews:
        card_id = review.get('card_id')
        quality = review.get('quality')
        
        if card_id is None or quality is None or not (0 <= quality <= 5):
            return jsonify({"msg": f"Invalid data for card {card_id}. Quality must be 0-5."}), 400
            
        card = Flashcard.query.get(card_id)

        if not card or card.collection_id != collection_id:
            return jsonify({"msg": f"Card {card_id} not found in this collection."}), 404
            
        rep, ef, interval, next_date = calculate_sm2(
            quality, card.repetition, card.easiness_factor, card.interval
        )
        
        card.repetition = rep
        card.easiness_factor = ef
        card.interval = interval
        card.next_review_date = next_date
        
        # Update text status dynamically
        if quality >= 3:
            card.status = 'learnt' if rep >= 3 else 'learning'
        else:
            card.status = 'learning'

        results.append({
            "card_id": card.id,
            "next_review_date": card.next_review_date,
            "new_status": card.status
        })
        
    db.session.commit()
    log_action(user_id, f"Reviewed {len(results)} flashcards in collection {col.id} - {col.name}")
    
    now = datetime.utcnow()
    cards_left = Flashcard.query.filter(
        Flashcard.collection_id == collection_id,
        (Flashcard.status == 'not learn') | 
        (Flashcard.status == 'learning') | 
        ((Flashcard.status == 'learnt') & (Flashcard.next_review_date <= now))
    ).count()
    
    next_card = Flashcard.query.filter(
        Flashcard.collection_id == collection_id,
        (Flashcard.status == 'not learn') | 
        (Flashcard.status == 'learning') | 
        ((Flashcard.status == 'learnt') & (Flashcard.next_review_date <= now))
    ).first()
    
    next_card_data = None
    if next_card:
        next_card_data = {
            "id": next_card.id,
            "front": next_card.front,
            "back": next_card.back,
            "status": next_card.status
        }
    
    return jsonify({
        "msg": "Reviews recorded successfully",
        "results": results,
        "cards_left": cards_left,          # Remaining due cards count
        "next_card": next_card_data,       # Pass this to the frontend to continue study
        "is_complete": cards_left == 0     # If True, the user has finished all due cards
    }), 200

@flashcard_bp.route('/collection/<int:collection_id>/question', methods=['GET'])
@jwt_required()
def generate_question(collection_id):
    user_id = int(get_jwt_identity())
    
    # 1. Authorization check
    col = Collection.query.get_or_404(collection_id)
    if col.status != 'public' and col.user_id != user_id:
        return jsonify({"msg": "Unauthorized to access this collection"}), 403
        
    all_cards = Flashcard.query.filter_by(collection_id=collection_id).all()
    if len(all_cards) < 4:
        return jsonify({"msg": "not enough flashcards for create a question"}), 400
        
    target_card = None
    
    # 2. Check if the frontend requested a specific card
    requested_card_id = request.args.get('next_card_id', type=int)
    
    if requested_card_id:
        target_card = Flashcard.query.filter_by(id=requested_card_id, collection_id=collection_id).first()
        if not target_card:
            return jsonify({"msg": "Requested card not found in this collection."}), 404
    else:
        # Fallback: Pick a random 'learning' or 'not learn' card
        eligible_question_cards = [c for c in all_cards if c.status in ['learning', 'not learn']]
        if not eligible_question_cards:
            return jsonify({"msg": "All flashcard are learned"}), 404
        target_card = random.choice(eligible_question_cards)
    
    # 3. UNRESTRICTED POOL FOR CHOICES
    other_cards = [c for c in all_cards if c.id != target_card.id]
    
    best_synonym = None
    best_syn_score = -1
    best_antonym = None
    best_ant_score = -1
    
    # 4. Use DistilBERT to find the best synonym and antonym
    if classifier:
        for card in other_cards:
            try:
                _, _, _, _, label_rel, conf_rel = classifier.predict(
                    target_card.front, card.front, target_card.back, card.back
                )
                rel_lower = str(label_rel).lower()
                if 'synonym' in rel_lower and conf_rel > best_syn_score:
                    best_syn_score = conf_rel
                    best_synonym = card
                elif 'antonym' in rel_lower and conf_rel > best_ant_score:
                    best_ant_score = conf_rel
                    best_antonym = card
            except Exception as e:
                continue 
                
    # 5. Assemble the 3 distractor choices
    distractors_dict = {} 
    
    if best_synonym:
        distractors_dict[best_synonym.id] = best_synonym 
        
    if best_antonym and best_antonym.id not in distractors_dict:
        distractors_dict[best_antonym.id] = best_antonym 
        
    # 6. Fill the remaining slots with random distractors
    available_pool = [c for c in other_cards if c.id not in distractors_dict]
    random.shuffle(available_pool)
    
    while len(distractors_dict) < 3 and available_pool:
        c = available_pool.pop()
        distractors_dict[c.id] = c 
        
    distractors_list = list(distractors_dict.values())
    
    def serialize_card(card):
        return {
            "id": card.id,
            "collection_id": card.collection_id,
            "front": card.front,
            "back": card.back,
            "status": card.status,
            "repetition": card.repetition,
            "easiness_factor": card.easiness_factor,
            "interval": card.interval,
            "next_review_date": card.next_review_date.isoformat() if card.next_review_date else None
        }
    
    # 7. Return formatted JSON
    return jsonify({
        "choices": [serialize_card(c) for c in distractors_list],
        "answer": serialize_card(target_card)
    }), 200