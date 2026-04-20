import reflex as rx
from demo1_front.components.layout import layout
from demo1_front.state.user import UserState
from demo1_front.components.skeleton import (
    SAKURA_100, SAKURA_200, SAKURA_400, SAKURA_500,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
    skeleton_list_items,
)


def public_collection_list_item(collection: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading(
                collection.get("name", "Unnamed Collection"),
                size="4",
                cursor="pointer",
                on_click=rx.redirect(f"/collection/{collection.get('id')}"),
                color=SAKURA_DARK,
                _hover={"color": SAKURA_500},
                transition="color 0.15s",
            ),
            rx.spacer(),
            rx.text(f"Cards: {collection.get('flashcard_count', 'N/A')}", size="2", color=SAKURA_MUTED),
            spacing="5",
            align_items="center",
            width="100%",
        ),
        width="100%",
        padding="1rem",
        border_radius="12px",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
        _hover={"border_color": SAKURA_200, "box_shadow": f"0 2px 12px {SAKURA_100}"},
        transition="all 0.2s ease",
    )


def user_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading(UserState.viewed_username, size="7", color=SAKURA_DARK),
                    rx.text("Public Profile", color=SAKURA_MUTED, size="2"),
                    align_items="start",
                    width="250px",
                ),
                rx.box(width="1px", height="500px", background=SAKURA_100),
                rx.vstack(
                    rx.heading("Public Collections", size="6", margin_bottom="1rem", color=SAKURA_DARK),
                    rx.cond(
                        UserState.is_loading,
                        skeleton_list_items(4),
                        rx.scroll_area(
                            rx.vstack(
                                rx.foreach(
                                    UserState.public_collections,
                                    public_collection_list_item,
                                ),
                                spacing="3",
                                padding="0.5rem",
                            ),
                            type="always",
                            scrollbars="vertical",
                            height="500px",
                            width="100%",
                        ),
                    ),
                    width="100%",
                    align_items="start",
                ),
                spacing="8",
                width="100%",
                align_items="start",
            ),
        ),
    )
