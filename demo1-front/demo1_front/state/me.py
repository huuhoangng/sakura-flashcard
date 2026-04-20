import reflex as rx
import httpx
from .base import BaseState

class MeState(BaseState):
    """The state for the Me page."""
    
    my_collections: list[dict] = []
    
    old_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    
    is_loading: bool = True
    
    show_password_dialog: bool = False
    
    async def load_profile(self):
        """Fetch user's collections."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/collections/",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    self.my_collections = response.json()
            except Exception as e:
                print(f"Error loading profile collections: {e}")
                
        self.is_loading = False
        
    def open_password_dialog(self):
        self.show_password_dialog = True
        
    def close_password_dialog(self):
        self.show_password_dialog = False
        self.old_password = ""
        self.new_password = ""
        self.confirm_password = ""
        
    async def change_password(self):
        """Handle password change."""
        if self.new_password != self.confirm_password:
            return rx.window_alert("New passwords do not match!")
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.flask_api_url}/auth/change-password",
                    json={"old_password": self.old_password, "new_password": self.new_password},
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    self.close_password_dialog()
                    return rx.window_alert("Password changed successfully!")
                else:
                    msg = response.json().get("msg", "Failed to change password")
                    return rx.window_alert(msg)
            except Exception as e:
                return rx.window_alert(str(e))
