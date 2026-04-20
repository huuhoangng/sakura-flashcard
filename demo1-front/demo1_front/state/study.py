import reflex as rx
import httpx
import time
import random
from .base import BaseState
from typing import List, Dict

class StudyState(BaseState):
    """The state for Study pages (Tinder and Kahoot UI)."""
    
    @rx.var
    def collection_id(self) -> str:
        return self.router.page.params.get("col_id", "")
    
    # Common
    is_loading: bool = True
    is_completed: bool = False
    mode: str = "Card learning" # or "Quiz"
    
    # Tinder specific
    current_card: dict = {}
    is_flipped: bool = False
    start_time: float = 0.0
    
    # Kahoot specific
    kahoot_query: str = ""
    kahoot_choices: list[str] = []
    kahoot_answer_index: int = -1
    
    async def load_study_session(self):
        """Init the study session for a collection."""
        if not self.is_authenticated:
            return rx.redirect("/login")
            
        self.is_loading = True
        self.is_completed = False
        self.is_flipped = False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/flashcards/collection/{self.collection_id}/study",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    data = response.json()
                    cards = data.get("cards", [])
                    if not cards:
                        self.is_completed = True
                    else:
                        self.current_card = cards[0]
                        self.start_time = time.time()
                        
                        if self.mode == "Quiz":
                            error_event = await self.load_question()
                            if error_event:
                                self.is_loading = False
                                return error_event
            except Exception as e:
                print(f"Error starting study session: {e}")
                
        self.is_loading = False

    def flip_card(self):
        """Tinder mode: flip front to back."""
        self.is_flipped = not self.is_flipped

    async def submit_review(self, quality: int):
        """Submit review for the current card and load the next."""
        self.is_loading = True
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.flask_api_url}/flashcards/collection/{self.collection_id}/review",
                    json={"reviews": [{"card_id": self.current_card.get("id"), "quality": quality}]},
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("is_complete"):
                        self.is_completed = True
                    else:
                        self.current_card = data.get("next_card", {})
                        self.is_flipped = False
                        self.start_time = time.time()
                        
                        if self.mode == "Quiz":
                            error_event = await self.load_question()
                            if error_event:
                                self.is_loading = False
                                return error_event
            except Exception as e:
                pass
                
        self.is_loading = False
        
    async def tinder_swipe_left(self):
        """Not remembered -> Quality 0"""
        await self.submit_review(0)
        
    async def tinder_swipe_right(self):
        """Remembered -> Quality based on time."""
        interval = time.time() - self.start_time
        if interval < 5:
            quality = 4
        elif interval < 8:
            quality = 3
        else:
            quality = 2
        await self.submit_review(quality)
        
    async def load_question(self):
        """Kahoot mode: load multiple choice question for current card."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.flask_api_url}/flashcards/collection/{self.collection_id}/question",
                    params={"next_card_id": self.current_card.get('id')},
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    data = response.json()
                    
                    ans_card = data.get("answer", {})
                    distractors = data.get("choices", [])
                    
                    self.kahoot_query = ans_card.get("front", "")
                    
                    # Merge answer and distractors
                    all_choices = [c.get("back", "") for c in distractors]
                    all_choices.append(ans_card.get("back", ""))
                    
                    # Shuffle to randomize answer position
                    random.shuffle(all_choices)
                    
                    self.kahoot_choices = all_choices
                    self.kahoot_answer_index = all_choices.index(ans_card.get("back", ""))
                else:
                    error_msg = response.json().get("msg", "Error loading Kahoot question")
                    print(f"Kahoot API Error {response.status_code}: {error_msg}")
                    return rx.window_alert(error_msg)
            except Exception as e:
                print(f"Kahoot Exception: {e}")
                return rx.window_alert(str(e))
                
    async def submit_kahoot_answer(self, choice_index: int):
        """Checks Kahoot answer and submits review."""
        if choice_index == self.kahoot_answer_index:
            # Right answer
            interval = time.time() - self.start_time
            if interval < 5:
                quality = 5
            else:
                quality = 4
            await self.submit_review(quality)
        else:
            # Wrong answer
            await self.submit_review(0)
            
    async def set_mode(self, mode: str):
        self.mode = mode
        # Trigger reload to ensure consistent state
        error_event = await self.load_study_session()
        if error_event:
            return error_event
