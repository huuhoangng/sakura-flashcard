import reflex as rx
import httpx
from .base import BaseState

class AuthState(BaseState):
    """The authentication state for login and signup."""
    
    # Login form
    login_username: str = ""
    login_password: str = ""
    login_error: str = ""
    
    # Signup form
    signup_username: str = ""
    signup_password: str = ""
    signup_error: str = ""
    signup_success: str = ""
    
    # Dialogs state
    show_login_error: bool = False
    show_signup_error: bool = False
    show_signup_success: bool = False
    
    async def login(self):
        """Handle login."""
        self.login_error = ""
        self.show_login_error = False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.flask_api_url}/auth/login",
                    json={"username": self.login_username, "password": self.login_password}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token", "")
                    self.user_role = data.get("role", "user")
                    self.username = self.login_username
                    
                    self.login_username = ""
                    self.login_password = ""
                    
                    if self.user_role == "admin":
                        return rx.redirect("/admin")
                    else:
                        return rx.redirect("/")
                else:
                    self.login_error = response.json().get("msg", "Login failed")
                    self.show_login_error = True
            except Exception as e:
                self.login_error = str(e)
                self.show_login_error = True

    async def signup(self):
        """Handle signup."""
        self.signup_error = ""
        self.signup_success = ""
        self.show_signup_error = False
        self.show_signup_success = False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.flask_api_url}/auth/signup",
                    json={"username": self.signup_username, "password": self.signup_password}
                )
                if response.status_code in (200, 201):
                    self.signup_success = "Signup successful! You can now log in."
                    self.show_signup_success = True
                    self.signup_username = ""
                    self.signup_password = ""
                else:
                    self.signup_error = response.json().get("msg", "Signup failed")
                    self.show_signup_error = True
            except Exception as e:
                self.signup_error = str(e)
                self.show_signup_error = True
                
    def logout(self):
        """Log out the user."""
        self.auth_token = ""
        self.user_role = ""
        self.username = ""
        return rx.redirect("/login")
        
    def check_auth(self):
        """Redirect if not authenticated or invalid."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
    def check_admin(self):
        """Redirect if not admin."""
        if not self.is_authenticated:
            return rx.redirect("/login")
        if not self.is_admin:
            self.logout()
            return rx.redirect("/")
            
    def redirect_if_auth(self):
        """Redirect away from login/signup if already auth."""
        if self.is_authenticated:
            return rx.redirect("/")

    async def check_auth_validity(self):
        """Check if the internal token is actually valid on the backend."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/auth/check", 
                    headers=self.get_headers()
                )
                if response.status_code in (401, 403, 422):
                    self.auth_token = ""
                    self.user_role = ""
                    self.username = ""
                    return rx.redirect("/login")
            except Exception:
                pass
