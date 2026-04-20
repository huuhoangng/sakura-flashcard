import reflex as rx
import httpx
from .base import BaseState

class AdminState(BaseState):
    """The state for Admin tables."""
    
    users: list[dict] = []
    collections: list[dict] = []
    flashcards: list[dict] = []
    logs: list[dict] = []
    
    search_term: str = ""
    is_loading: bool = True
    
    # Pagination & Tab State
    current_tab: str = "users"
    page: int = 1
    total_pages: int = 1
    per_page: int = 20
    
    # Sorting state
    sort_column: str = ""
    sort_ascending: bool = True
    
    def check_admin_access(self):
        """Ensure only admins reach here."""
        if not self.is_authenticated or self.user_role != "admin":
            self.logout()
            return rx.redirect("/login")
    
    async def toggle_sort(self, column: str):
        """Toggle sort on a column. Click again to reverse direction."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        await self.load_data_for_current_tab()
            
    async def set_tab(self, tab_name: str):
        self.current_tab = tab_name
        self.page = 1
        self.search_term = ""
        self.sort_column = ""
        self.sort_ascending = True
        await self.load_data_for_current_tab()

    async def perform_search(self):
        self.page = 1
        await self.load_data_for_current_tab()

    async def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            await self.load_data_for_current_tab()

    async def prev_page(self):
        if self.page > 1:
            self.page -= 1
            await self.load_data_for_current_tab()

    async def load_data_for_current_tab(self):
        if self.current_tab == "users":
            await self.load_users()
        elif self.current_tab == "collections":
            await self.load_collections()
        elif self.current_tab == "flashcards":
            await self.load_flashcards()
        elif self.current_tab == "logs":
            await self.load_logs()
            
    async def initial_load(self):
        auth_check = self.check_admin_access()
        if auth_check is not None:
            return auth_check
        await self.load_data_for_current_tab()

    async def load_users(self):
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/admin/users/search",
                    headers=self.get_headers(),
                    params={
                        "q": self.search_term, 
                        "page": self.page, 
                        "per_page": self.per_page,
                        "sort_by": self.sort_column,
                        "order": "asc" if self.sort_ascending else "desc"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self.users = data.get("items", [])
                    self.total_pages = data.get("pages", 1)
            except Exception as e:
                print(f"Error loading users: {e}")
        self.is_loading = False
        
    async def delete_user(self, user_id: str):
        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.flask_api_url}/admin/user/{user_id}", headers=self.get_headers())
        await self.load_users()

    async def load_collections(self):
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/admin/collections",
                    headers=self.get_headers(),
                    params={
                        "q": self.search_term, 
                        "page": self.page, 
                        "per_page": self.per_page,
                        "sort_by": self.sort_column,
                        "order": "asc" if self.sort_ascending else "desc"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self.collections = data.get("items", [])
                    self.total_pages = data.get("pages", 1)
            except:
                pass
        self.is_loading = False

    async def delete_collection(self, collection_id: str):
        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.flask_api_url}/admin/collections/{collection_id}", headers=self.get_headers())
        await self.load_collections()

    async def load_flashcards(self):
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/admin/flashcards/search",
                    headers=self.get_headers(),
                    params={
                        "q": self.search_term, 
                        "page": self.page, 
                        "per_page": self.per_page,
                        "sort_by": self.sort_column,
                        "order": "asc" if self.sort_ascending else "desc"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self.flashcards = data.get("items", [])
                    self.total_pages = data.get("pages", 1)
            except:
                pass
        self.is_loading = False
        
    async def delete_flashcard(self, flashcard_id: str):
        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.flask_api_url}/admin/flashcards/{flashcard_id}", headers=self.get_headers())
        await self.load_flashcards()
        
    async def load_logs(self):
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/admin/logs",
                    headers=self.get_headers(),
                    params={
                        "q": self.search_term, 
                        "page": self.page, 
                        "per_page": self.per_page,
                        "sort_by": self.sort_column,
                        "order": "asc" if self.sort_ascending else "desc"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self.logs = data.get("items", [])
                    self.total_pages = data.get("pages", 1)
            except:
                pass
        self.is_loading = False
