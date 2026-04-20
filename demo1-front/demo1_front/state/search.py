import reflex as rx
import httpx
from .base import BaseState

class SearchState(BaseState):
    """The state for the global header search."""
    
    query: str = ""
    show_collection: bool = True
    show_flashcard: bool = True
    show_user: bool = True
    
    results: list[dict] = []
    is_searching: bool = False
    show_results: bool = False
    
    async def toggle_filter(self, filter_type: str):
        if filter_type == "collection":
            self.show_collection = not self.show_collection
        elif filter_type == "flashcard":
            self.show_flashcard = not self.show_flashcard
        elif filter_type == "user":
            self.show_user = not self.show_user
            
        await self.perform_search()
        
    async def handle_input(self, val: str):
        self.query = val
        if len(self.query.strip()) >= 2:
            self.show_results = True
            await self.perform_search()
        else:
            self.results = []
            self.show_results = False
        
    async def perform_search(self):
        if not self.query.strip():
            self.results = []
            self.show_results = False
            return
            
        self.show_results = True
        self.is_searching = True
        self.results = []
        
        # Build the objects_search_list based on active filters
        objects_search_list = []
        if self.show_collection:
            objects_search_list.append("collections")
        if self.show_flashcard:
            objects_search_list.append("flashcards")
        if self.show_user:
            objects_search_list.append("users")
        
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            try:
                res = await client.post(
                    f"{self.flask_api_url}/search/",
                    headers=headers,
                    json={
                        "text": self.query,
                        "objects_search_list": objects_search_list,
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    
                    # Map collections
                    for c in data.get("collections", []):
                        self.results.append({
                            "type": "Collection",
                            "title": c.get("name", ""),
                            "subtitle": f"by @{c.get('owner_username', '')} · {c.get('flashcard_count', 0)} cards",
                            "url": f"/collection/{c.get('id', '')}",
                        })
                    
                    # Map flashcards
                    for f in data.get("flashcards", []):
                        self.results.append({
                            "type": "Flashcard",
                            "title": f.get("front", ""),
                            "subtitle": f.get("back", ""),
                            "url": f"/collection/{f.get('collection_id', '')}",
                        })
                    
                    # Map users
                    for u in data.get("users", []):
                        self.results.append({
                            "type": "User",
                            "title": u.get("username", ""),
                            "subtitle": u.get("role", ""),
                            "url": f"/user/{u.get('username', '')}",
                        })
            
            except Exception as e:
                print(f"Error during search: {e}")
                
        self.is_searching = False
