import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import case, func
from extensions import db
from models.flashcard import Flashcard
from models.collection import Collection
from models.recommendation import (
    SemanticRecommendFlashcard, SemanticRecommendCollection,
    DiscoverRecommendFlashcard, DiscoverRecommendCollection,
    TimeoutFlashcards, TimeoutCollections
)
from utils.decorators import admin_required
from utils.recommendation import (
    get_similar_users,
    get_cbf_flashcard_recommendations,
    get_cbf_collection_recommendations
)

recommendation_bp = Blueprint('recommendation', __name__)

# ===============================
# HELPER FUNCTIONS
# ===============================

def _weighted_sample(items, weight_func, k):
    """Returns random items based on distribution of their scores."""
    if not items: return []
    items_copy = list(items)
    # Ensure all weights are strictly positive for random.choices
    weights = [max(weight_func(i), 0.01) for i in items_copy]
    results = []
    for _ in range(min(k, len(items_copy))):
        chosen = random.choices(items_copy, weights=weights, k=1)[0]
        results.append(chosen)
        idx = items_copy.index(chosen)
        items_copy.pop(idx)
        weights.pop(idx)
        if sum(weights) <= 0: break
    return results

def _refill_flashcards(user_id, needed=30):
    """Refills Semantic and Discover flashcards when count drops."""
    restricted_users = []
    total_added_sem = 0
    total_added_disc = 0

    # 1. Gather Restricted Objects (all recs + timeout)
    sem = db.session.query(SemanticRecommendFlashcard.recomFlashcardID).filter_by(targetUserID=user_id).all()
    disc = db.session.query(DiscoverRecommendFlashcard.recomFlashcardID).filter_by(targetUserID=user_id).all()
    tout = db.session.query(TimeoutFlashcards.recomFlashcardID).filter_by(targetUserID=user_id).all()
    restricted_card_ids = list(set([x[0] for x in sem + disc + tout]))

    # 2. Gather Restricted Targets (targets that yielded the most objects)
    target_counts = db.session.query(
        SemanticRecommendFlashcard.targetFlashcard, func.count(SemanticRecommendFlashcard.id).label('cnt')
    ).filter_by(targetUserID=user_id).group_by(SemanticRecommendFlashcard.targetFlashcard).order_by(db.desc('cnt')).limit(5).all()
    restricted_target_ids = [x[0] for x in target_counts]

    # 3. Find New Target Flashcards
    status_priority = case(
        (Flashcard.status == 'learning', 1), (Flashcard.status == 'learnt', 2),
        (Flashcard.status == 'not learn', 3), else_=4
    )
    query = Flashcard.query.join(Collection).filter(Collection.user_id == user_id)
    if restricted_target_ids:
        query = query.filter(~Flashcard.id.in_(restricted_target_ids))

    target_cards = query.order_by(status_priority, Flashcard.easiness_factor.asc(), Flashcard.interval.asc()).limit(3).all()
    if not target_cards: return

    for card in target_cards:
        if card.id not in restricted_card_ids: restricted_card_ids.append(card.id)

    while total_added_sem < needed or total_added_disc < needed:
        similar_users = get_similar_users(target_user_id=user_id, top_n=10, restricted_user_ids=restricted_users)
        if not similar_users:
            break
            
        similar_user_ids = [u['user_id'] for u in similar_users]
        restricted_users.extend(similar_user_ids)

        for is_disc in [False, True]:
            if (not is_disc and total_added_sem >= needed) or (is_disc and total_added_disc >= needed):
                continue
                
            for target_card in target_cards:
                if (not is_disc and total_added_sem >= needed) or (is_disc and total_added_disc >= needed):
                    break
                    
                raw_recs = get_cbf_flashcard_recommendations(
                    user_id=user_id, target_card_id=target_card.id, top_n=needed, 
                    restricted_card_ids=restricted_card_ids, similar_user_ids=similar_user_ids, is_discovery=is_disc
                )
                if isinstance(raw_recs, dict) and "error" in raw_recs: continue
                
                for r in raw_recs:
                    restricted_card_ids.append(r["card_id"])
                    if is_disc:
                        db.session.add(DiscoverRecommendFlashcard(
                            targetUserID=user_id, targetFlashcard=target_card.id, recomFlashcardID=r["card_id"],
                            ownerUserID=r["owner_id"], discoverScore=r["similarity_score"]
                        ))
                        total_added_disc += 1
                        if total_added_disc >= needed: break
                    else:
                        db.session.add(SemanticRecommendFlashcard(
                            targetUserID=user_id, targetFlashcard=target_card.id, recomFlashcardID=r["card_id"],
                            ownerUserID=r["owner_id"], similarScore=r["similarity_score"]
                        ))
                        total_added_sem += 1
                        if total_added_sem >= needed: break
        db.session.commit()

def _refill_collections(user_id, needed=20):
    """Refills Semantic and Discover collections when count drops."""
    restricted_users = []
    total_added_sem = 0
    total_added_disc = 0

    sem = db.session.query(SemanticRecommendCollection.recomCollectionID).filter_by(targetUserID=user_id).all()
    disc = db.session.query(DiscoverRecommendCollection.recomCollectionID).filter_by(targetUserID=user_id).all()
    tout = db.session.query(TimeoutCollections.recomCollectionID).filter_by(targetUserID=user_id).all()
    restricted_collection_ids = list(set([x[0] for x in sem + disc + tout]))

    target_counts = db.session.query(
        SemanticRecommendCollection.targetCollection, func.count(SemanticRecommendCollection.id).label('cnt')
    ).filter_by(targetUserID=user_id).group_by(SemanticRecommendCollection.targetCollection).order_by(db.desc('cnt')).limit(5).all()
    restricted_target_ids = [x[0] for x in target_counts]

    query = Collection.query.filter(Collection.user_id == user_id)
    if restricted_target_ids: query = query.filter(~Collection.id.in_(restricted_target_ids))
    
    fetched = query.order_by(Collection.id.desc()).limit(10).all()
    target_collections = []
    for col in fetched:
        if col.flashcards:
            target_collections.append(col)
            if len(target_collections) == 3:
                break

    if not target_collections: return
    for col in target_collections:
        if col.id not in restricted_collection_ids: restricted_collection_ids.append(col.id)

    while total_added_sem < needed or total_added_disc < needed:
        similar_users = get_similar_users(target_user_id=user_id, top_n=10, restricted_user_ids=restricted_users)
        if not similar_users:
            break
            
        similar_user_ids = [u['user_id'] for u in similar_users]
        restricted_users.extend(similar_user_ids)

        for is_disc in [False, True]:
            if (not is_disc and total_added_sem >= needed) or (is_disc and total_added_disc >= needed):
                continue

            for target_col in target_collections:
                if (not is_disc and total_added_sem >= needed) or (is_disc and total_added_disc >= needed):
                    break

                raw_recs = get_cbf_collection_recommendations(
                    user_id=user_id, target_collection_id=target_col.id, top_n=needed, 
                    restricted_collection_ids=restricted_collection_ids, similar_user_ids=similar_user_ids, is_discovery=is_disc
                )
                if isinstance(raw_recs, dict) and "error" in raw_recs: continue

                for r in raw_recs:
                    restricted_collection_ids.append(r["collection_id"])
                    if is_disc:
                        db.session.add(DiscoverRecommendCollection(
                            targetUserID=user_id, targetCollection=target_col.id, recomCollectionID=r["collection_id"],
                            ownerUserID=r["owner_id"], discoverScore=r["total_similarity_score"]
                        ))
                        total_added_disc += 1
                        if total_added_disc >= needed: break
                    else:
                        db.session.add(SemanticRecommendCollection(
                            targetUserID=user_id, targetCollection=target_col.id, recomCollectionID=r["collection_id"],
                            ownerUserID=r["owner_id"], similarScore=r["total_similarity_score"]
                        ))
                        total_added_sem += 1
                        if total_added_sem >= needed: break
        db.session.commit()

# ===============================
# ENDPOINTS
# ===============================

@recommendation_bp.route('/flashcards', methods=['POST'])
@jwt_required()
def recommend_flashcards():
    user_id = int(get_jwt_identity())
    top_n = (request.get_json() or {}).get('top_n', 5)

    # Decay timeout entries so exhausted recs can eventually resurface
    timeout_recs = TimeoutFlashcards.query.filter_by(targetUserID=user_id).all()
    for t in timeout_recs:
        t.timeoutScore -= 0.02
        if t.timeoutScore <= 0:
            db.session.delete(t)
    db.session.commit()

    # Guard: insufficient user data for semantic recommendations
    user_col_count = Collection.query.filter_by(user_id=user_id).count()
    user_card_count = Flashcard.query.join(Collection).filter(Collection.user_id == user_id).count()
    if user_col_count < 2 and user_card_count < 6:
        return jsonify({"recommendations": [], "insufficient_data": True}), 200

    available_recs = SemanticRecommendFlashcard.query.filter_by(targetUserID=user_id).all()
    if len(available_recs) < top_n:
        _refill_flashcards(user_id, needed=30)
        available_recs = SemanticRecommendFlashcard.query.filter_by(targetUserID=user_id).all()

    selected = _weighted_sample(available_recs, lambda x: x.similarScore, top_n)
    results = []
    timeout_triggered = False

    for rec in selected:
        recom_card = Flashcard.query.get(rec.recomFlashcardID)
        target_card = Flashcard.query.get(rec.targetFlashcard)
        if not recom_card or not target_card: continue

        results.append({
            "target_card_id": target_card.id, "target_front": target_card.front,
            "recommended_card_id": recom_card.id, "id": recom_card.id, "front": recom_card.front, "back": recom_card.back, "collection_id": recom_card.collection_id,
            "owner_username": recom_card.collection.user.username,
            "similarity_score": rec.similarScore
        })

        # Decay Function
        rec.similarScore -= 0.1
        if rec.similarScore <= 0:
            timeout_triggered = True
            db.session.add(TimeoutFlashcards(
                targetUserID=rec.targetUserID, targetFlashcard=rec.targetFlashcard,
                recomFlashcardID=rec.recomFlashcardID, ownerUserID=rec.ownerUserID, timeoutScore=1.0
            ))
            db.session.delete(rec)
    db.session.commit()

    if timeout_triggered:
        c_sem = SemanticRecommendFlashcard.query.filter_by(targetUserID=user_id).count()
        c_disc = DiscoverRecommendFlashcard.query.filter_by(targetUserID=user_id).count()
        if (c_sem + c_disc) < 30: _refill_flashcards(user_id, needed=30)

    return jsonify({"recommendations": results}), 200

@recommendation_bp.route('/collections', methods=['POST'])
@jwt_required()
def recommend_collections():
    user_id = int(get_jwt_identity())
    top_n = (request.get_json() or {}).get('top_n', 5)

    # Decay timeout entries so exhausted recs can eventually resurface
    timeout_recs = TimeoutCollections.query.filter_by(targetUserID=user_id).all()
    for t in timeout_recs:
        t.timeoutScore -= 0.01
        if t.timeoutScore <= 0:
            db.session.delete(t)
    db.session.commit()

    # Guard: insufficient user data for semantic recommendations
    user_col_count = Collection.query.filter_by(user_id=user_id).count()
    user_card_count = Flashcard.query.join(Collection).filter(Collection.user_id == user_id).count()
    if user_col_count < 2 and user_card_count < 6:
        return jsonify({"recommendations": [], "insufficient_data": True}), 200

    available_recs = SemanticRecommendCollection.query.filter_by(targetUserID=user_id).all()
    if len(available_recs) < top_n:
        _refill_collections(user_id, needed=20)
        available_recs = SemanticRecommendCollection.query.filter_by(targetUserID=user_id).all()

    selected = _weighted_sample(available_recs, lambda x: x.similarScore, top_n)
    results = []
    timeout_triggered = False

    for rec in selected:
        recom_col = Collection.query.get(rec.recomCollectionID)
        target_col = Collection.query.get(rec.targetCollection)
        if not recom_col or not target_col: continue

        results.append({
            "target_collection_id": target_col.id, "target_collection_name": target_col.name,
            "recommended_collection_id": recom_col.id, "id": recom_col.id, "name": recom_col.name,
            "owner_username": recom_col.user.username,
            "total_similarity_score": rec.similarScore
        })

        # Decay Function
        rec.similarScore -= 0.05
        if rec.similarScore <= 0:
            timeout_triggered = True
            db.session.add(TimeoutCollections(
                targetUserID=rec.targetUserID, targetCollection=rec.targetCollection,
                recomCollectionID=rec.recomCollectionID, ownerUserID=rec.ownerUserID, timeoutScore=1.0
            ))
            db.session.delete(rec)
    db.session.commit()

    if timeout_triggered:
        c_sem = SemanticRecommendCollection.query.filter_by(targetUserID=user_id).count()
        c_disc = DiscoverRecommendCollection.query.filter_by(targetUserID=user_id).count()
        if (c_sem + c_disc) < 20: _refill_collections(user_id, needed=20)

    return jsonify({"recommendations": results}), 200

@recommendation_bp.route('/discovery/flashcards', methods=['POST'])
@jwt_required()
def discover_flashcards():
    user_id = int(get_jwt_identity())
    top_n = (request.get_json() or {}).get('top_n', 5)

    # Decay timeout entries so exhausted recs can eventually resurface
    timeout_recs = TimeoutFlashcards.query.filter_by(targetUserID=user_id).all()
    for t in timeout_recs:
        t.timeoutScore -= 0.02
        if t.timeoutScore <= 0:
            db.session.delete(t)
    db.session.commit()

    available_recs = DiscoverRecommendFlashcard.query.filter_by(targetUserID=user_id).all()
    if len(available_recs) < top_n:
        _refill_flashcards(user_id, needed=30)
        available_recs = DiscoverRecommendFlashcard.query.filter_by(targetUserID=user_id).all()

    selected = _weighted_sample(available_recs, lambda x: x.discoverScore, top_n)
    results = []
    timeout_triggered = False

    for rec in selected:
        recom_card = Flashcard.query.get(rec.recomFlashcardID)
        target_card = Flashcard.query.get(rec.targetFlashcard)
        if not recom_card or not target_card: continue

        results.append({
            "target_card_id": target_card.id, "target_front": target_card.front,
            "recommended_card_id": recom_card.id, "id": recom_card.id, "front": recom_card.front, "back": recom_card.back, "collection_id": recom_card.collection_id,
            "owner_username": recom_card.collection.user.username,
            "discovery_score": rec.discoverScore
        })

        rec.discoverScore -= 0.1
        if rec.discoverScore <= 0:
            timeout_triggered = True
            db.session.add(TimeoutFlashcards(
                targetUserID=rec.targetUserID, targetFlashcard=rec.targetFlashcard,
                recomFlashcardID=rec.recomFlashcardID, ownerUserID=rec.ownerUserID, timeoutScore=1.0
            ))
            db.session.delete(rec)
    db.session.commit()

    if timeout_triggered:
        c_sem = SemanticRecommendFlashcard.query.filter_by(targetUserID=user_id).count()
        c_disc = DiscoverRecommendFlashcard.query.filter_by(targetUserID=user_id).count()
        if (c_sem + c_disc) < 30: _refill_flashcards(user_id, needed=30)

    return jsonify({"discovery_recommendations": results}), 200

@recommendation_bp.route('/discovery/collections', methods=['POST'])
@jwt_required()
def discover_collections():
    user_id = int(get_jwt_identity())
    top_n = (request.get_json() or {}).get('top_n', 5)

    # Decay timeout entries so exhausted recs can eventually resurface
    timeout_recs = TimeoutCollections.query.filter_by(targetUserID=user_id).all()
    for t in timeout_recs:
        t.timeoutScore -= 0.01
        if t.timeoutScore <= 0:
            db.session.delete(t)
    db.session.commit()

    available_recs = DiscoverRecommendCollection.query.filter_by(targetUserID=user_id).all()
    if len(available_recs) < top_n:
        _refill_collections(user_id, needed=20)
        available_recs = DiscoverRecommendCollection.query.filter_by(targetUserID=user_id).all()

    selected = _weighted_sample(available_recs, lambda x: x.discoverScore, top_n)
    results = []
    timeout_triggered = False

    for rec in selected:
        recom_col = Collection.query.get(rec.recomCollectionID)
        target_col = Collection.query.get(rec.targetCollection)
        if not recom_col or not target_col: continue

        results.append({
            "target_collection_id": target_col.id, "target_collection_name": target_col.name,
            "recommended_collection_id": recom_col.id, "id": recom_col.id, "name": recom_col.name,
            "owner_username": recom_col.user.username,
            "total_discovery_score": rec.discoverScore
        })

        rec.discoverScore -= 0.05
        if rec.discoverScore <= 0:
            timeout_triggered = True
            db.session.add(TimeoutCollections(
                targetUserID=rec.targetUserID, targetCollection=rec.targetCollection,
                recomCollectionID=rec.recomCollectionID, ownerUserID=rec.ownerUserID, timeoutScore=1.0
            ))
            db.session.delete(rec)
    db.session.commit()

    if timeout_triggered:
        c_sem = SemanticRecommendCollection.query.filter_by(targetUserID=user_id).count()
        c_disc = DiscoverRecommendCollection.query.filter_by(targetUserID=user_id).count()
        if (c_sem + c_disc) < 20: _refill_collections(user_id, needed=20)

    return jsonify({"discovery_recommendations": results}), 200