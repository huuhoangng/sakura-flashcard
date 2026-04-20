import requests
import json
import random
import string

BASE_URL = "http://127.0.0.1:5000/api"

def make_request(method, endpoint, payload=None, token=None, show_response=False):
    """
    Helper function to execute an HTTP request.
    If show_response is False, it only prints the status code.
    If show_response is True, it prints the full JSON response.
    """
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
        
    url = f"{BASE_URL}{endpoint}"
    
    # Execute Request
    if method.upper() == "GET":
        res = requests.get(url, headers=headers, params=payload)
    elif method.upper() == "POST":
        res = requests.post(url, headers=headers, json=payload)
    elif method.upper() == "PUT":
        res = requests.put(url, headers=headers, json=payload)
    elif method.upper() == "DELETE":
        res = requests.delete(url, headers=headers)
        
    try:
        res_body = res.json()
    except:
        res_body = res.text
        
    # Print Output
    print(f"[{method.upper()}] {endpoint:<40} -> Status: {res.status_code}")
    
    if show_response:
        print("-" * 60)
        if isinstance(res_body, (dict, list)):
            print(json.dumps(res_body, indent=2))
        else:
            print(res_body)
        print("-" * 60)
    
    return res, res_body

def generate_random_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_tests():
    print("="*80)
    print("🚀 STARTING API INTEGRATION TESTS")
    print("="*80)
    
    # Generate random credentials to avoid conflicts
    test_user = f"user_{generate_random_string()}"
    test_admin = f"admin_{generate_random_string()}"
    password = "password123"

    print("\n" + "#"*20 + " 1. AUTH APIs " + "#"*20)
    # Signup standard user
    make_request("POST", "/auth/signup", payload={"username": test_user, "password": password})
    # Signup admin user
    make_request("POST", "/auth/signup", payload={"username": test_admin, "password": password, "role": "admin"})
    
    # Login standard user
    _, auth_res = make_request("POST", "/auth/login", payload={"username": test_user, "password": password})
    user_token = auth_res.get("access_token") if isinstance(auth_res, dict) else None
    
    # Login admin user
    _, admin_auth_res = make_request("POST", "/auth/login", payload={"username": test_admin, "password": password})
    admin_token = admin_auth_res.get("access_token") if isinstance(admin_auth_res, dict) else None

    if not user_token or not admin_token:
        print("❌ Authentication failed. Cannot proceed with tests.")
        return

    print("\n" + "#"*20 + " 2. COLLECTION APIs " + "#"*20)
    # Create Collection
    # Note: If you still get a 404 here, try removing the trailing slash: "/collection" instead of "/collection/"
    _, col_res = make_request("POST", "/collections/", payload={"name": "Test Deck", "status": "public"}, token=user_token)
    
    # Safety check to prevent AttributeError
    col_id = col_res.get("id") if isinstance(col_res, dict) else None
    
    if not col_id:
        print(f"❌ Failed to create collection. Server responded with: \n{col_res}")
    else:
        # Get my collections
        make_request("GET", "/collections/", token=user_token)
        # Get specific collection
        make_request("GET", f"/collections/{col_id}", token=user_token)
        # Edit collection
        make_request("PUT", f"/collections/{col_id}", payload={"name": "Updated Test Deck"}, token=user_token)
        # Search public collections
        make_request("GET", "/collections/search?q=Test", token=user_token)
        # Get user's public collections (using arbitrary ID 1, assuming fast_learner_1 exists)
        make_request("GET", "/collections/user/1", token=user_token)


    print("\n" + "#"*20 + " 3. FLASHCARD APIs " + "#"*20)
    card_id = None
    if col_id:
        # Create Flashcard
        # Note: If you still get a 404 here, try removing the trailing slash: "/flashcard" instead of "/flashcard/"
        _, card_res = make_request("POST", "/flashcards/", payload={"collection_id": col_id, "front": "Test Front", "back": "Test Back"}, token=user_token)
        
        # Safety check to prevent AttributeError
        card_id = card_res.get("id") if isinstance(card_res, dict) else None
        
        if not card_id:
            print(f"❌ Failed to create flashcard. Server responded with: \n{card_res}")
        else:
            # Get specific flashcard
            make_request("GET", f"/flashcards/{card_id}", token=user_token)
            # Get collection's flashcards
            make_request("GET", f"/flashcards/collection/{col_id}", token=user_token)
            # Edit flashcard
            make_request("PUT", f"/flashcards/{card_id}", payload={"front": "Updated Front"}, token=user_token)
            # Search public flashcards
            make_request("GET", "/flashcards/search/public?q=Updated", token=user_token)
            # Search user's public flashcards
            make_request("GET", "/flashcards/search/public/user/1?q=a", token=user_token)
            
            # Study/Review routes
            make_request("GET", f"/flashcards/collection/{col_id}/study", token=user_token)
            review_payload = {"reviews": [{"card_id": card_id, "quality": 4}]}
            make_request("POST", f"/flashcards/collection/{col_id}/review", payload=review_payload, token=user_token)


    print("\n" + "#"*20 + " 4. RECOMMENDATION APIs (SHOWING RESPONSES) " + "#"*20)
    # Using the primary testing user (fast_learner_1) for recommendations since they have data
    _, fallback_auth = make_request("POST", "/auth/login", payload={"username": "fast_learner_1", "password": "password123"})
    rec_token = fallback_auth.get("access_token", user_token) if isinstance(fallback_auth, dict) else user_token

    print("\n>>> Testing Collaborative Filtering (Similar Users) <<<")
    _, similar_users_res = make_request("POST", "/recommendations/users", payload={"top_n": 20}, token=rec_token, show_response=True)
    
    sim_user_ids = []
    if isinstance(similar_users_res, dict) and "recommendations" in similar_users_res:
        sim_user_ids = [u["user_id"] for u in similar_users_res.get("recommendations", [])]
    
    print("\n>>> Testing Content-Based Filtering (Semantic Flashcards) <<<")
    make_request("POST", "/recommendations/flashcards", payload={"top_n": 5, "similar_user_ids": sim_user_ids}, token=rec_token, show_response=True)

    print("\n>>> Testing Content-Based Filtering (Semantic Collections) <<<")
    make_request("POST", "/recommendations/collections", payload={"top_n": 5, "similar_user_ids": sim_user_ids}, token=rec_token, show_response=True)
    
    print("\n>>> Testing Discovery (Difficulty-based Flashcards) <<<")
    make_request("POST", "/recommendations/discovery/flashcards", payload={"top_n": 5, "similar_user_ids": sim_user_ids}, token=rec_token, show_response=True)

    print("\n>>> Testing Discovery (Difficulty-based Collections) <<<")
    make_request("POST", "/recommendations/discovery/collections", payload={"top_n": 5, "similar_user_ids": sim_user_ids}, token=rec_token, show_response=True)


    print("\n" + "#"*20 + " 5. ADMIN APIs & CLEANUP " + "#"*20)
    # Get Logs
    make_request("GET", "/admin/logs", token=admin_token)
    # Search Users
    make_request("GET", "/admin/users/search?q=test", token=admin_token)
    # Admin Get Collections
    make_request("GET", "/admin/collections", token=admin_token)
    # Admin Get Flashcards
    make_request("GET", "/admin/flashcards", token=admin_token)
    # Admin Search Flashcards
    make_request("GET", "/admin/flashcards/search?q=Updated", token=admin_token)
    
    if col_id:
        # Admin Update Collection Status
        make_request("PUT", f"/admin/collections/{col_id}/status", payload={"status": "private"}, token=admin_token)
        # Admin Get specific user's collections
        make_request("GET", "/admin/user/1/collections", token=admin_token)
    
    print("\n>>> Cleaning up test data <<<")
    if card_id:
        # Delete flashcard as normal user
        make_request("DELETE", f"/flashcard/{card_id}", token=user_token)
        
    if col_id:
        # Admin delete collection
        make_request("DELETE", f"/admin/collections/{col_id}", token=admin_token)

    print("\n" + "="*80)
    print("✅ ALL API TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    # Disable warnings for unverified HTTPS requests if testing locally on HTTPS
    requests.packages.urllib3.disable_warnings() 
    run_tests()