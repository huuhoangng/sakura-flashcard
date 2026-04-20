import reflex as rx
import httpx
from .base import BaseState

class UserState(BaseState):
    """The state for a specific User's public page."""
    
    public_collections: list[dict] = []
    is_loading: bool = True
    
    @rx.var
    def viewed_username(self) -> str:
        return self.router.page.params.get("username_param", "")
    
    async def load_user_profile(self):
        """Load a specific user's public collections."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        # In Reflex, path variables are set automatically when defined as state vars and matching the route param.
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/collections/user/{self.viewed_username}",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    self.public_collections = response.json()
            except Exception as e:
                print(f"Error loading user profile: {e}")
                
        self.is_loading = False
