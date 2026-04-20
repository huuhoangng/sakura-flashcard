import reflex as rx
import httpx
from .base import BaseState

class HomeState(BaseState):
    """The state for the Home page."""
    
    similar_collections: list[dict] = []
    similar_flashcards: list[dict] = []
    discover_collections: list[dict] = []
    discover_flashcards: list[dict] = []
    
    is_loading: bool = True
    insufficient_data: bool = False
    
    async def load_recommendations(self):
        """Load recommendations on page load."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        self.insufficient_data = False
        
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            try:
                # Semantic Flashcards
                r1 = await client.post(f"{self.flask_api_url}/recommendations/flashcards", headers=headers, json={"top_n": 5})
                if r1.status_code == 200:
                    data1 = r1.json()
                    self.similar_flashcards = data1.get("recommendations", [])
                    if data1.get("insufficient_data", False):
                        self.insufficient_data = True
                
                # Semantic Collections
                r2 = await client.post(f"{self.flask_api_url}/recommendations/collections", headers=headers, json={"top_n": 5})
                if r2.status_code == 200:
                    data2 = r2.json()
                    self.similar_collections = data2.get("recommendations", [])
                    if data2.get("insufficient_data", False):
                        self.insufficient_data = True
                    
                # Discovery Flashcards
                r3 = await client.post(f"{self.flask_api_url}/recommendations/discovery/flashcards", headers=headers, json={"top_n": 5})
                if r3.status_code == 200:
                    self.discover_flashcards = r3.json().get("discovery_recommendations", [])
                    
                # Discovery Collections
                r4 = await client.post(f"{self.flask_api_url}/recommendations/discovery/collections", headers=headers, json={"top_n": 5})
                if r4.status_code == 200:
                    self.discover_collections = r4.json().get("discovery_recommendations", [])
                    
            except Exception as e:
                print(f"Error loading recommendations: {e}")
        
        self.is_loading = False
