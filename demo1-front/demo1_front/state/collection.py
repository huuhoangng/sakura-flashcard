import reflex as rx
import httpx
from .base import BaseState
from typing import List, Dict, Any

class CollectionState(BaseState):
    """The state for collection view, create, edit."""
    
    @rx.var
    def collection_id(self) -> str:
        return self.router.page.params.get("col_id", "")
    
    # Detail fields
    collection_info: dict = {}
    flashcards: List[dict] = []
    is_loading: bool = True
    
    # Create/Edit fields
    edit_name: str = ""
    edit_status: str = "private"
    # Store rows explicitly so index mutations are easier
    edit_flashcards: List[dict] = []
    deleted_flashcard_ids: List[int] = []
    form_error: str = ""
    
    def toggle_status(self):
        self.edit_status = "public" if self.edit_status == "private" else "private"
        
    async def load_collection(self):
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/collections/{self.collection_id}",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    data = response.json()
                    self.collection_info = data
                    
                fc_resp = await client.get(
                    f"{self.flask_api_url}/flashcards/collection/{self.collection_id}",
                    headers=self.get_headers()
                )
                if fc_resp.status_code == 200:
                    self.flashcards = fc_resp.json()
            except Exception as e:
                print(f"Error loading collection: {e}")
                
        self.is_loading = False
        
    async def duplicate(self):
        """Duplicate redirects to create with ID parameter."""
        return rx.redirect(f"/collection/create?duplicate={self.collection_id}")
        
    async def handle_create_load(self):
        """Prepare create form, maybe loading duplicate data."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        self.edit_name = ""
        self.edit_status = "private"
        self.edit_flashcards = [{"id": -1, "front": "", "back": ""}]
        self.deleted_flashcard_ids = []
        self.form_error = ""
        
        # safely read query parameter
        try:
            duplicate_param = self.router.page.params.get("duplicate")
            if duplicate_param:
                if isinstance(duplicate_param, list):
                    duplicate_param = duplicate_param[0]
                    
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.flask_api_url}/collections/{duplicate_param}",
                        headers=self.get_headers()
                    )
                    if response.status_code == 200:
                        data = response.json()
                        self.edit_name = data.get("name", "Copy of collection") + " (Copy)"
                        self.edit_status = data.get("status", "private")
                        
                        fc_resp = await client.get(
                            f"{self.flask_api_url}/flashcards/collection/{duplicate_param}",
                            headers=self.get_headers()
                        )
                        if fc_resp.status_code == 200:
                            self.edit_flashcards = [
                                {"id": -1, "front": f.get("front", ""), "back": f.get("back", "")}
                                for f in fc_resp.json()
                            ]
                        else:
                            self.edit_flashcards = []
                        
                        if not self.edit_flashcards:
                            self.edit_flashcards = [{"id": -1, "front": "", "back": ""}]
        except Exception as e:
            print(f"Error duplicate: {e}")
            pass
        self.is_loading = False
        
    async def handle_edit_load(self):
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        self.deleted_flashcard_ids = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/collections/{self.collection_id}",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    data = response.json()
                    self.edit_name = data.get("name", "")
                    self.edit_status = data.get("status", "private")
                    
                fc_resp = await client.get(
                    f"{self.flask_api_url}/flashcards/collection/{self.collection_id}",
                    headers=self.get_headers()
                )
                if fc_resp.status_code == 200:
                    self.edit_flashcards = [
                        {"id": f.get("id"), "front": f.get("front", ""), "back": f.get("back", "")}
                        for f in fc_resp.json()
                    ]
            except Exception as e:
                pass
        self.is_loading = False

    def add_flashcard_row(self):
        self.edit_flashcards.append({"id": -1, "front": "", "back": ""})
        
    def remove_flashcard_row(self, index: int):
        if len(self.edit_flashcards) > 1:
            removed = self.edit_flashcards.pop(index)
            if removed.get("id", -1) != -1:
                self.deleted_flashcard_ids.append(removed["id"])
            
    def update_flashcard_front(self, front: str, index: int):
        self.edit_flashcards[index]["front"] = front
        
    def update_flashcard_back(self, back: str, index: int):
        self.edit_flashcards[index]["back"] = back

    async def save_collection(self, is_edit: bool = False):
        if not self.edit_name.strip():
            self.form_error = "Collection name is required."
            return rx.window_alert(self.form_error)
            
        for fc in self.edit_flashcards:
            if not fc["front"].strip() or not fc["back"].strip():
                self.form_error = "All flashcard inputs must be filled."
                return rx.window_alert(self.form_error)
                
        self.form_error = ""
        col_payload = {"name": self.edit_name, "status": self.edit_status}
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. Save Collection Base
                if is_edit:
                    response = await client.put(
                        f"{self.flask_api_url}/collections/{self.collection_id}",
                        json=col_payload, headers=self.get_headers()
                    )
                    col_id = int(self.collection_id)
                else:
                    response = await client.post(
                        f"{self.flask_api_url}/collections",
                        json=col_payload, headers=self.get_headers()
                    )
                    if response.status_code in (200, 201):
                        col_id = response.json().get("id")
                    else:
                        return rx.window_alert("Failed to create collection.")
                        
                if response.status_code in (200, 201):
                    # 2. Process Flashcard Additions and Updates
                    for fc in self.edit_flashcards:
                        if fc.get("id", -1) != -1:
                            # Update existing card
                            await client.put(
                                f"{self.flask_api_url}/flashcards/{fc['id']}",
                                json={"front": fc["front"], "back": fc["back"]},
                                headers=self.get_headers()
                            )
                        else:
                            # Create new card
                            await client.post(
                                f"{self.flask_api_url}/flashcards",
                                json={"collection_id": col_id, "front": fc["front"], "back": fc["back"]},
                                headers=self.get_headers()
                            )
                            
                    # 3. Process Flashcard Deletions
                    if is_edit:
                        for del_id in self.deleted_flashcard_ids:
                            await client.delete(
                                f"{self.flask_api_url}/flashcards/{del_id}",
                                headers=self.get_headers()
                            )
                    
                    rx.window_alert("Saved successfully!")
                    return rx.redirect(f"/collection/{col_id}")
                else:
                    return rx.window_alert("Failed to save collection core. " + str(response.status_code))
            except Exception as e:
                return rx.window_alert(f"Error: {str(e)}")
