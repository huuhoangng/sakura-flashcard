import os
import time
from app import create_app
from extensions import db
from models.user import User
from models.collection import Collection
from models.flashcard import Flashcard
from models.recommendation import (
    SemanticRecommendCollection, SemanticRecommendFlashcard,
    DiscoverRecommendCollection, DiscoverRecommendFlashcard
)
from utils.recommendation import (
    get_similar_users,
    get_cbf_collection_recommendations,
    get_cbf_flashcard_recommendations,
    clear_caches,
    get_cache_stats
)

# 2. Instantiate the Flask application
app = create_app()

def populate_recommendations():
    """
    Background job to fill the recommendation tables for all users.
    """
    # 3. Use the instantiated app context
    with app.app_context():
        # Clear prediction caches for a fresh run
        clear_caches()
        
        print("Clearing all existing recommendations from the database...")
        SemanticRecommendCollection.query.delete()
        DiscoverRecommendCollection.query.delete()
        SemanticRecommendFlashcard.query.delete()
        DiscoverRecommendFlashcard.query.delete()
        db.session.commit()
        print("Existing data cleared. Starting fresh population...")

        users = User.query.all()
        total_users = len(users)
        print(f"Found {total_users} users. Starting recommendation population...")
        
        batch_start = time.time()

        for idx, user in enumerate(users):
            user_id = user.id
            user_start = time.time()
            print(f"\n--- [{idx+1}/{total_users}] Processing User ID: {user_id} ---")
            
            target_cols = Collection.query.filter_by(user_id=user_id).order_by(Collection.id.desc()).limit(5).all()
            target_cards = Flashcard.query.join(Collection).filter(
                Collection.user_id == user_id
            ).order_by(Flashcard.id.desc()).limit(10).all()

            if not target_cols and not target_cards:
                print(f"  User {user_id} has no data. Skipping.")
                continue

            print(f"  Targets: {len(target_cols)} collections, {len(target_cards)} flashcards")

            # 2. Get similar users
            t = time.time()
            similar_users_data = get_similar_users(target_user_id=user_id, top_n=15)
            similar_user_ids = [u['user_id'] for u in similar_users_data]
            print(f"  Similar users found: {len(similar_user_ids)} ({time.time()-t:.1f}s)")

            restricted_col_ids = [c.id for c in target_cols]
            restricted_card_ids = [c.id for c in target_cards]

            # ==========================================
            # 3. PROCESS COLLECTIONS (top_n=20 per target → keep best 20 Sem, 20 Disc)
            # ==========================================
            sem_col_pool = {}
            disc_col_pool = {}

            t = time.time()
            for i, col in enumerate(target_cols):
                # Semantic Collections
                raw_sem_cols = get_cbf_collection_recommendations(
                    user_id=user_id, target_collection_id=col.id, top_n=20,
                    restricted_collection_ids=restricted_col_ids, similar_user_ids=similar_user_ids, is_discovery=False
                )
                if isinstance(raw_sem_cols, list):
                    for r in raw_sem_cols:
                        rec_id = r["collection_id"]
                        if rec_id not in sem_col_pool or r["total_similarity_score"] > sem_col_pool[rec_id]["score"]:
                            sem_col_pool[rec_id] = {
                                "target": col.id, "recom": rec_id, "owner": r["owner_id"], "score": r["total_similarity_score"]
                            }

                # Discover Collections
                raw_disc_cols = get_cbf_collection_recommendations(
                    user_id=user_id, target_collection_id=col.id, top_n=20,
                    restricted_collection_ids=restricted_col_ids, similar_user_ids=similar_user_ids, is_discovery=True
                )
                if isinstance(raw_disc_cols, list):
                    for r in raw_disc_cols:
                        rec_id = r["collection_id"]
                        if rec_id not in disc_col_pool or r["total_similarity_score"] > disc_col_pool[rec_id]["score"]:
                            disc_col_pool[rec_id] = {
                                "target": col.id, "recom": rec_id, "owner": r["owner_id"], "score": r["total_similarity_score"]
                            }
                print(f"    Collection {i+1}/{len(target_cols)} done")
            
            col_time = time.time() - t
            print(f"  Collections done: {len(sem_col_pool)} sem, {len(disc_col_pool)} disc ({col_time:.1f}s)")

            # ==========================================
            # 4. PROCESS FLASHCARDS (top_n=40 per target → keep best 40 Sem, 40 Disc)
            # ==========================================
            sem_card_pool = {}
            disc_card_pool = {}

            t = time.time()
            for i, card in enumerate(target_cards):
                # Semantic Flashcards
                raw_sem_cards = get_cbf_flashcard_recommendations(
                    user_id=user_id, target_card_id=card.id, top_n=40,
                    restricted_card_ids=restricted_card_ids, similar_user_ids=similar_user_ids, is_discovery=False
                )
                if isinstance(raw_sem_cards, list):
                    for r in raw_sem_cards:
                        rec_id = r["card_id"]
                        if rec_id not in sem_card_pool or r["similarity_score"] > sem_card_pool[rec_id]["score"]:
                            sem_card_pool[rec_id] = {
                                "target": card.id, "recom": rec_id, "owner": r["owner_id"], "score": r["similarity_score"]
                            }

                # Discover Flashcards
                raw_disc_cards = get_cbf_flashcard_recommendations(
                    user_id=user_id, target_card_id=card.id, top_n=40,
                    restricted_card_ids=restricted_card_ids, similar_user_ids=similar_user_ids, is_discovery=True
                )
                if isinstance(raw_disc_cards, list):
                    for r in raw_disc_cards:
                        rec_id = r["card_id"]
                        if rec_id not in disc_card_pool or r["similarity_score"] > disc_card_pool[rec_id]["score"]:
                            disc_card_pool[rec_id] = {
                                "target": card.id, "recom": rec_id, "owner": r["owner_id"], "score": r["similarity_score"]
                            }
                
                if (i + 1) % 5 == 0 or i == len(target_cards) - 1:
                    print(f"    Flashcard {i+1}/{len(target_cards)} done")
            
            card_time = time.time() - t
            print(f"  Flashcards done: {len(sem_card_pool)} sem, {len(disc_card_pool)} disc ({card_time:.1f}s)")

            # ==========================================
            # 5. SORT, SLICE, AND SAVE TO DATABASE
            # ==========================================
            final_sem_cols = sorted(sem_col_pool.values(), key=lambda x: x["score"], reverse=True)[:20]
            final_disc_cols = sorted(disc_col_pool.values(), key=lambda x: x["score"], reverse=True)[:20]
            final_sem_cards = sorted(sem_card_pool.values(), key=lambda x: x["score"], reverse=True)[:40]
            final_disc_cards = sorted(disc_card_pool.values(), key=lambda x: x["score"], reverse=True)[:40]

            # Clear existing data for this user to prevent duplicates during batch runs
            SemanticRecommendCollection.query.filter_by(targetUserID=user_id).delete()
            DiscoverRecommendCollection.query.filter_by(targetUserID=user_id).delete()
            SemanticRecommendFlashcard.query.filter_by(targetUserID=user_id).delete()
            DiscoverRecommendFlashcard.query.filter_by(targetUserID=user_id).delete()

            # Insert Collections
            for item in final_sem_cols:
                db.session.add(SemanticRecommendCollection(
                    targetUserID=user_id, targetCollection=item["target"], recomCollectionID=item["recom"],
                    ownerUserID=item["owner"], similarScore=item["score"]
                ))
            
            for item in final_disc_cols:
                db.session.add(DiscoverRecommendCollection(
                    targetUserID=user_id, targetCollection=item["target"], recomCollectionID=item["recom"],
                    ownerUserID=item["owner"], discoverScore=item["score"]
                ))

            # Insert Flashcards
            for item in final_sem_cards:
                db.session.add(SemanticRecommendFlashcard(
                    targetUserID=user_id, targetFlashcard=item["target"], recomFlashcardID=item["recom"],
                    ownerUserID=item["owner"], similarScore=item["score"]
                ))

            for item in final_disc_cards:
                db.session.add(DiscoverRecommendFlashcard(
                    targetUserID=user_id, targetFlashcard=item["target"], recomFlashcardID=item["recom"],
                    ownerUserID=item["owner"], discoverScore=item["score"]
                ))

            db.session.commit()
            
            user_time = time.time() - user_start
            elapsed = time.time() - batch_start
            avg_per_user = elapsed / (idx + 1)
            eta = avg_per_user * (total_users - idx - 1)
            
            stats = get_cache_stats()
            print(f"  ✓ Saved: {len(final_sem_cols)} SemCols, {len(final_disc_cols)} DiscCols, "
                  f"{len(final_sem_cards)} SemCards, {len(final_disc_cards)} DiscCards")
            print(f"  ⏱ User: {user_time:.1f}s | Elapsed: {elapsed/60:.1f}min | ETA: {eta/60:.1f}min")
            print(f"  📦 Cache: {stats['predict_cache_size']} predictions, "
                  f"{stats['behavior_cache_size']} behaviors, {stats['cf_cache_size']} CF scores")

        total_time = time.time() - batch_start
        print(f"\n{'='*50}")
        print(f"Finished populating all {total_users} users in {total_time/60:.1f} minutes.")
        final_stats = get_cache_stats()
        print(f"Final cache: {final_stats['predict_cache_size']} unique predictions cached "
              f"(saved from recomputing)")

if __name__ == "__main__":
    populate_recommendations()