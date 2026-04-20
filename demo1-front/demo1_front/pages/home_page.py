import reflex as rx
from demo1_front.components.layout import layout
from demo1_front.state.home import HomeState
from demo1_front.components.skeleton import (
    SAKURA_100, SAKURA_400, SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
    skeleton_card_row,
)


def collection_card(collection: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.center(
                rx.heading(collection.get("name", "Unknown"), size="4", color=SAKURA_DARK, text_align="center"),
                width="100%",
                height="80px",
                padding="0.5rem",
            ),
            rx.box(height="1px", width="100%", background=SAKURA_100),
            rx.flex(
                rx.text(f"@{collection.get('owner_username', 'unknown')}", size="1", color=SAKURA_MUTED),
                justify="end",
                width="100%",
                padding_x="0.5rem",
            ),
            spacing="2",
        ),
        width="200px",
        height="150px",
        cursor="pointer",
        on_click=rx.redirect(f"/collection/{collection.get('id')}"),
        background=SAKURA_CARD,
        border=f"1px solid {SAKURA_100}",
        _hover={"box_shadow": f"0 6px 24px {SAKURA_100}", "transform": "translateY(-3px)", "border_color": SAKURA_400},
        transition="all 0.2s ease",
    )


def flashcard_card(flashcard: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.center(
                rx.text(flashcard.get("front", ""), size="3", weight="medium", text_align="center", color=SAKURA_DARK),
                width="100%",
                height="80px",
                padding="0.5rem",
            ),
            rx.box(height="1px", width="100%", background=SAKURA_100),
            rx.flex(
                rx.text(f"@{flashcard.get('owner_username', 'unknown')}", size="1", color=SAKURA_MUTED),
                justify="end",
                width="100%",
                padding_x="0.5rem",
            ),
            spacing="2",
        ),
        width="200px",
        height="150px",
        cursor="pointer",
        on_click=rx.redirect(f"/collection/{flashcard.get('collection_id')}"),
        background=SAKURA_CARD,
        border=f"1px solid {SAKURA_100}",
        _hover={"box_shadow": f"0 6px 24px {SAKURA_100}", "transform": "translateY(-3px)", "border_color": SAKURA_400},
        transition="all 0.2s ease",
    )


def carousel_section(title: str, items: list, is_flashcard: bool = False) -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="5", color=SAKURA_DARK, margin_bottom="1.5rem"),
        rx.scroll_area(
            rx.hstack(
                rx.foreach(
                    items,
                    lambda item: flashcard_card(item) if is_flashcard else collection_card(item),
                ),
                spacing="4",
                padding="1.5rem",
            ),
            type="always",
            scrollbars="horizontal",
            width="100%",
        ),
        spacing="4",
        width="100%",
        margin_bottom="2rem",
    )


def skeleton_carousel_section(title: str) -> rx.Component:
    """Loading placeholder for a carousel section."""
    return rx.vstack(
        rx.skeleton(rx.box(height="24px", width="280px"), loading=True),
        skeleton_card_row(5),
        width="100%",
        margin_bottom="2rem",
        spacing="3",
    )


def index() -> rx.Component:
    return layout(
        rx.vstack(
            rx.cond(
                HomeState.is_loading,
                rx.vstack(
                    skeleton_carousel_section("Similar Recommended Collections"),
                    skeleton_carousel_section("Similar Recommended Flashcards"),
                    skeleton_carousel_section("Discover Collections"),
                    skeleton_carousel_section("Discover Flashcards"),
                    width="100%",
                ),
                rx.vstack(
                    # Semantic carousels: only show when user has sufficient data
                    rx.cond(
                        ~HomeState.insufficient_data,
                        rx.fragment(
                            carousel_section("Similar Recommended Collections", HomeState.similar_collections, False),
                            carousel_section("Similar Recommended Flashcards", HomeState.similar_flashcards, True),
                        ),
                    ),
                    # Discover carousels: always shown
                    carousel_section("Discover Collections", HomeState.discover_collections, False),
                    carousel_section("Discover Flashcards", HomeState.discover_flashcards, True),
                    width="100%",
                ),
            ),
        ),
    )
