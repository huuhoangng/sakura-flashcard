import reflex as rx

class BaseState(rx.State):
    """The base state for the app."""
    flask_api_url: str = "http://localhost:5000/api"
    
    auth_token: str = rx.LocalStorage("", name="auth_token")
    user_role: str = rx.LocalStorage("", name="user_role")
    username: str = rx.LocalStorage("", name="username")
    
    @rx.var
    def is_authenticated(self) -> bool:
        return self.auth_token != ""
        
    @rx.var
    def is_admin(self) -> bool:
        return self.user_role == "admin"
        
    def get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
