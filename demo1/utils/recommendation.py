import os
import time
from collections import defaultdict, OrderedDict
from functools import lru_cache
import numpy as np
from sqlalchemy import func
from extensions import db
from models.user import User
from models.flashcard import Flashcard #
from models.collection import Collection #
from utils.averageEF import get_weighted_average_ef #
from utils.loadDistilBERTModel import SemanticClassifier #


# Safely resolve the absolute path to the model regardless of the python execution directory
_base_dir = os.path.dirname(os.path.abspath(__file__))
_model_path = os.path.join(_base_dir, "distilBERTModel")

# Initialize the classifier once globally to avoid reloading the model on every request
classifier = SemanticClassifier(model_dir=_model_path)

# Map string relationships to numeric weights
RELATIONSHIP_WEIGHTS = {
    "synonym": 1.0,
    "antonym": 0.8,
    "neuter": 0.0
}

# ADDED: Flipped weights for Discovery Matching (Prioritize unrelated topics)
DISCOVERY_RELATIONSHIP_WEIGHTS = {
    "synonym": 0.0,
    "antonym": 0.2,
    "neuter": 1.0
}

# Map CEFR levels to a numeric scale (1.0 to 6.0) to align with EF difficulty ranges
CEFR_NUMERIC = {
    "A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0
}

# ===============================
# SIZE-BOUNDED LRU CACHES
# ===============================
# Max sizes prevent unbounded RAM growth in long-running Flask server.
# Oldest entries are evicted when the cache is full.
# Budget: ~2 GB total. Per-entry sizes: predict ~780B, behavior ~256B, vocab ~5KB, cf ~240B.

_PREDICT_CACHE_MAX = 2_000_000   # ~1.56 GB — dominates budget, holds most word-pair results
_BEHAVIOR_CACHE_MAX = 1_000      # ~0.25 MB — covers 1k users (2× current 450)
_VOCAB_CACHE_MAX = 1_000         # ~5 MB   — covers 1k users (2× current 450)
_CF_CACHE_MAX = 200_000          # ~48 MB  — covers all 450² user pairs with headroom


class LRUCache:
    """Simple size-bounded LRU cache using OrderedDict."""
    def __init__(self, max_size):
        self._cache = OrderedDict()
        self._max_size = max_size
    
    def get(self, key, default=None):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return default
    
    def put(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)  # Evict oldest
    
    def __contains__(self, key):
        return key in self._cache
    
    def __len__(self):
        return len(self._cache)
    
    def clear(self):
        self._cache.clear()


_predict_cache = LRUCache(_PREDICT_CACHE_MAX)
_behavior_cache = LRUCache(_BEHAVIOR_CACHE_MAX)
_vocab_cache = LRUCache(_VOCAB_CACHE_MAX)
_cf_cache = LRUCache(_CF_CACHE_MAX)

def clear_caches():
    """Clear all caches. Call at the start of a batch run."""
    _predict_cache.clear()
    _behavior_cache.clear()
    _vocab_cache.clear()
    _cf_cache.clear()

def get_cache_stats():
    """Return cache size statistics for logging."""
    return {
        "predict_cache_size": len(_predict_cache),
        "behavior_cache_size": len(_behavior_cache),
        "vocab_cache_size": len(_vocab_cache),
        "cf_cache_size": len(_cf_cache),
    }

def _cached_predict(input1, input2, def1, def2):
    """Cached wrapper around classifier.predict(). Identical word pairs are only computed once."""
    key = (input1, input2, def1, def2)
    result = _predict_cache.get(key)
    if result is None:
        result = classifier.predict(
            input1=input1, input2=input2, def1=def1, def2=def2
        )
        _predict_cache.put(key, result)
    return result


def get_card_difficulty_level(word, cefr_label, min_reviews_threshold=5):
    """
    Calculates the difficulty level of a word.
    Uses empirical Average EF if enough users have reviewed it.
    Falls back to the DistilBERT CEFR prediction if it's a new or rarely studied word.
    """
    weighted_sum, total_reps = get_weighted_average_ef(word) #
    
    # Check if we have enough historical review data across the platform
    if total_reps >= min_reviews_threshold:
        average_ef = weighted_sum / total_reps
        # Lower EF means harder. We invert it so a higher number = higher difficulty level
        return 5.0 - average_ef
    else:
        # Fallback to the Neural Network's CEFR prediction
        return CEFR_NUMERIC.get(cefr_label, 1.0)
    

def get_cbf_flashcard_recommendations(user_id, target_card_id, top_n=5, alpha=0.9, beta=0.1, min_reps=5, restricted_card_ids=None, similar_user_ids=None, is_discovery=False):
    """
    Generates Content-Based Filtering recommendations based on Semantic Classification 
    and hybrid Difficulty Comparison.
    Optionally restricts the search pool to flashcards owned by specific similar users.
    """
    if restricted_card_ids is None:
        restricted_card_ids = []
    if similar_user_ids is None:
        similar_user_ids = []

    # 1. Fetch the target flashcard
    target_card = Flashcard.query.get(target_card_id) #
    if not target_card or target_card.collection.user_id != user_id:
        return {"error": "Invalid or unauthorized target card."}

    # 2. Fetch all public candidate flashcards, excluding restricted IDs
    query = Flashcard.query.join(Collection).filter(
        Collection.status == 'public',
        Collection.user_id != user_id
    ) #
    
    # Filter OUT specific cards
    if restricted_card_ids:
        query = query.filter(~Flashcard.id.in_(restricted_card_ids))
        
    # Filter IN only collections owned by similar users
    if similar_user_ids:
        query = query.filter(Collection.user_id.in_(similar_user_ids))
        
    public_candidates = query.all()

    target_behavior = get_user_behavior_vector(user_id)
    target_vocab = get_user_vocab_dict(user_id)
    cf_scores_cache = {}

    recommendations = []

    # 3. Process each candidate
    for candidate in public_candidates:
        # A. Run DistilBERT inference (CACHED)
        (
            label_cefr_target, conf_cefr_target, 
            label_cefr_cand, conf_cefr_cand, 
            label_rel, conf_rel
        ) = _cached_predict(
            input1=target_card.front, 
            input2=candidate.front, 
            def1=target_card.back, 
            def2=candidate.back
        )

        if is_discovery:
            semantic_weight = DISCOVERY_RELATIONSHIP_WEIGHTS.get(label_rel, 1.0)
        else:
            semantic_weight = RELATIONSHIP_WEIGHTS.get(label_rel, 0.0)

        # Optimization: Skip irrelevant relationships early
        if semantic_weight <= 0.0 and alpha > 0.0:
            continue

        # B. Calculate hybrid difficulty levels for both cards
        target_level = get_card_difficulty_level(target_card.front, label_cefr_target, min_reps) #
        candidate_level = get_card_difficulty_level(candidate.front, label_cefr_cand, min_reps)

        # C. Calculate the Difficulty Delta
        delta_level = abs(target_level - candidate_level)
        
        difficulty_similarity = 1 / (1 + delta_level)
        owner_id = candidate.collection.user_id
        if owner_id not in cf_scores_cache:
            cf_scores_cache[owner_id] = calculate_cf_similarity(user_id, owner_id, target_vocab, target_behavior)
        owner_cf_score = cf_scores_cache[owner_id]
        similarity_score = (alpha * semantic_weight) + (beta * difficulty_similarity * owner_cf_score)

        recommendations.append({
            "flashcard": candidate,
            "card_id": candidate.id,
            "front": candidate.front,
            "back": candidate.back,
            "collection_id": candidate.collection_id,
            "owner_id": candidate.collection.user_id, # Included to show which similar user owns it
            "relationship": label_rel,
            "difficulty_delta": round(delta_level, 4),
            "similarity_score": round(similarity_score, 4)
        })

    # 4. Sort by the highest similarity score
    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True) #
    
    return recommendations[:top_n]


def get_cbf_collection_recommendations(user_id, target_collection_id, top_n=5, alpha=0.9, beta=0.1, min_reps=5, restricted_collection_ids=None, similar_user_ids=None, is_discovery=False):
    """
    Generates Content-Based Filtering recommendations by comparing a target collection
    against public collections.
    Optionally restricts the search pool to collections owned by specific similar users.
    """
    if restricted_collection_ids is None:
        restricted_collection_ids = []
    if similar_user_ids is None:
        similar_user_ids = []

    # 1. Fetch the target collection and its flashcards
    target_collection = Collection.query.get(target_collection_id) #
    if not target_collection or target_collection.user_id != user_id: 
        return {"error": "Invalid or unauthorized target collection."}

    target_cards = target_collection.flashcards #
    if not target_cards:
        return {"error": "Target collection is empty."}

    # 2. Fetch all public collections NOT owned by the user
    query = Collection.query.filter(
        Collection.status == 'public', 
        Collection.user_id != user_id 
    ) #
    
    # Filter OUT specific collections
    if restricted_collection_ids:
        query = query.filter(~Collection.id.in_(restricted_collection_ids))
        
    # Filter IN only collections owned by similar users
    if similar_user_ids:
        query = query.filter(Collection.user_id.in_(similar_user_ids))
        
    public_collections = query.all()

    target_behavior = get_user_behavior_vector(user_id)
    target_vocab = get_user_vocab_dict(user_id)
    cf_scores_cache = {}

    collection_scores = defaultdict(list)

    # 3. Process each public candidate collection
    for pub_col in public_collections:
        owner_id = pub_col.user_id
        if owner_id not in cf_scores_cache:
            cf_scores_cache[owner_id] = calculate_cf_similarity(user_id, owner_id, target_vocab, target_behavior)
        owner_cf_score = cf_scores_cache[owner_id]
        for candidate_card in pub_col.flashcards: 
            best_sim_for_candidate = 0.0
            
            # Compare candidate card against EVERY card in the user's target collection
            for target_card in target_cards:
                # A. Run DistilBERT inference (CACHED)
                (
                    label_cefr_target, conf_cefr_target, 
                    label_cefr_cand, conf_cefr_cand, 
                    label_rel, conf_rel
                ) = _cached_predict(
                    input1=target_card.front, 
                    input2=candidate_card.front, 
                    def1=target_card.back, 
                    def2=candidate_card.back
                )

                if is_discovery:
                    semantic_weight = DISCOVERY_RELATIONSHIP_WEIGHTS.get(label_rel, 1.0)
                else:
                    semantic_weight = RELATIONSHIP_WEIGHTS.get(label_rel, 0.0)

                # Optimization: Skip neutral words ONLY IF we are doing Semantic Matching (alpha > 0.0)
                if semantic_weight <= 0.0 and alpha > 0.0:
                    continue

                # B. Calculate hybrid difficulty levels
                target_level = get_card_difficulty_level(target_card.front, label_cefr_target, min_reps) #
                candidate_level = get_card_difficulty_level(candidate_card.front, label_cefr_cand, min_reps)

                # C. Calculate the Difficulty Delta and Similarity Score
                delta_level = abs(target_level - candidate_level)
                
                difficulty_similarity = 1 / (1 + delta_level)
                similarity_score = (alpha * semantic_weight) + (beta * difficulty_similarity * owner_cf_score)

                # Track the highest similarity this candidate card has with the target deck
                if similarity_score > best_sim_for_candidate:
                    best_sim_for_candidate = similarity_score

            # D. If this candidate card matched well with the target deck, add its score
            if best_sim_for_candidate > 0:
                collection_scores[pub_col.id].append(best_sim_for_candidate)

    # 4. Aggregate scores to rank Collections
    recommendations = []
    for col_id, scores in collection_scores.items():
        if not scores:
            continue
            
        collection = Collection.query.get(col_id) #
        
        # Rank by the total accumulated similarity of its cards
        total_score = sum(scores)
        avg_score = total_score / len(scores)
        
        recommendations.append({
            "collection": collection,
            "collection_id": col_id,
            "collection_name": collection.name, 
            "owner_id": collection.user_id, # Included to show which similar user owns it
            "total_similarity_score": round(total_score, 4),
            "average_card_similarity": round(avg_score, 4),
            "highly_similar_cards_count": len(scores)
        })

    # 5. Sort by the highest aggregate similarity score
    recommendations.sort(key=lambda x: x["total_similarity_score"], reverse=True) #
    
    return recommendations[:top_n]

def get_user_behavior_vector(user_id):
    """
    Extracts the Global Learning Pacing vector for a user.
    Returns: [avg_ef, avg_interval, avg_repetition, retention_rate]
    Uses cache to avoid redundant DB queries during batch runs.
    """
    cached = _behavior_cache.get(user_id)
    if cached is not None:
        return cached

    stats = db.session.query(
        func.avg(Flashcard.easiness_factor).label('avg_ef'),
        func.avg(Flashcard.interval).label('avg_interval'),
        func.avg(Flashcard.repetition).label('avg_rep'),
        func.count(Flashcard.id).label('total_cards')
    ).join(Collection).filter(Collection.user_id == user_id).first()

    total_cards = stats.total_cards or 0
    if total_cards == 0:
        result = np.array([2.5, 0.0, 0.0, 0.0]) # Default state
        _behavior_cache.put(user_id, result)
        return result

    learnt_cards = db.session.query(func.count(Flashcard.id)).join(Collection).filter(
        Collection.user_id == user_id,
        Flashcard.status == 'learnt'
    ).scalar()

    retention_rate = learnt_cards / total_cards

    result = np.array([
        float(stats.avg_ef or 2.5),
        float(stats.avg_interval or 0) * 0.1,  # Scaled down
        float(stats.avg_rep or 0) * 0.1,       # Scaled down
        float(retention_rate)
    ])
    _behavior_cache.put(user_id, result)
    return result

def get_user_vocab_dict(user_id):
    """
    Returns a dictionary of {front_text: easiness_factor} for a user.
    Uses cache to avoid redundant DB queries during batch runs.
    """
    cached = _vocab_cache.get(user_id)
    if cached is not None:
        return cached

    cards = db.session.query(Flashcard.front, Flashcard.easiness_factor).join(Collection).filter(
        Collection.user_id == user_id
    ).all()
    
    # Lowercase to ensure accurate matching
    result = {card.front.lower(): card.easiness_factor for card in cards}
    _vocab_cache.put(user_id, result)
    return result

def calculate_cf_similarity(target_user_id, candidate_user_id, target_vocab, target_behavior):
    """
    Calculates the combined CF score between two users.
    Uses cache for the symmetric relationship.
    """
    # Check cache (symmetric: similarity(A,B) == similarity(B,A) for behavior, 
    # but not exactly for item overlap since it depends on target_vocab)
    cache_key = (target_user_id, candidate_user_id)
    cached = _cf_cache.get(cache_key)
    if cached is not None:
        return cached

    # 1. Behavioral Similarity (Euclidean Distance converted to similarity)
    cand_behavior = get_user_behavior_vector(candidate_user_id)
    distance = np.linalg.norm(target_behavior - cand_behavior)
    sim_behavior = 1 / (1 + distance)

    # 2. Item-Based Overlap (Cosine Similarity on shared vocabularies)
    cand_vocab = get_user_vocab_dict(candidate_user_id)
    shared_words = set(target_vocab.keys()).intersection(set(cand_vocab.keys()))
    
    sim_item = 0.0
    if shared_words:
        target_vec = np.array([target_vocab[w] for w in shared_words])
        cand_vec = np.array([cand_vocab[w] for w in shared_words])
        
        # Cosine Similarity
        dot_product = np.dot(target_vec, cand_vec)
        norm_t = np.linalg.norm(target_vec)
        norm_c = np.linalg.norm(cand_vec)
        
        if norm_t > 0 and norm_c > 0:
            sim_item = dot_product / (norm_t * norm_c)

    # 3. Hybrid Calculation (e.g., 60% behavior, 40% item overlap)
    w_behavior = 0.6
    w_item = 0.4
    
    total_sim = (w_behavior * sim_behavior) + (w_item * sim_item)
    _cf_cache.put(cache_key, total_sim)
    return total_sim

def get_similar_users(target_user_id, top_n=5, restricted_user_ids=None):
    """
    Finds the most similar peers to the target user.
    Excludes any user IDs provided in the restricted_user_ids list.
    """
    if restricted_user_ids is None:
        restricted_user_ids = []

    # Pre-calculate target user data to avoid redundant DB queries
    target_behavior = get_user_behavior_vector(target_user_id) #
    target_vocab = get_user_vocab_dict(target_user_id) #
    
    # Get all other users, excluding restricted ones
    query = User.query.filter(User.id != target_user_id) #
    if restricted_user_ids:
        query = query.filter(~User.id.in_(restricted_user_ids))
        
    other_users = query.all()
    
    peer_scores = []
    for user in other_users:
        score = calculate_cf_similarity(target_user_id, user.id, target_vocab, target_behavior) #
        peer_scores.append({
            "user_id": user.id,
            "username": user.username,
            "similarity_score": round(score, 4)
        })
        
    # Sort by highest similarity
    peer_scores.sort(key=lambda x: x["similarity_score"], reverse=True) #
    return peer_scores[:top_n]