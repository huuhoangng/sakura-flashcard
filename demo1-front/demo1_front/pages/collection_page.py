import reflex as rx
from demo1_front.components.layout import layout
from demo1_front.state.collection import CollectionState
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_200, SAKURA_400, SAKURA_500, SAKURA_600,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
    skeleton_detail_page,
)


def edit_flashcard_row(flashcard: dict, index: int) -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("trash"), color_scheme="red", variant="soft",
            on_click=lambda: CollectionState.remove_flashcard_row(index),
        ),
        rx.text_area(
            value=flashcard["front"], placeholder="Front text", width="45%",
            on_change=lambda val: CollectionState.update_flashcard_front(val, index),
            background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"},
            border_color=SAKURA_200,
            _focus={"border_color": SAKURA_400},
        ),
        rx.text_area(
            value=flashcard["back"], placeholder="Back text", width="45%",
            on_change=lambda val: CollectionState.update_flashcard_back(val, index),
            background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"},
            border_color=SAKURA_200,
            _focus={"border_color": SAKURA_400},
        ),
        width="100%", align="center", spacing="4",
    )


def skeleton_edit_page() -> rx.Component:
    """Skeleton for the create/edit form."""
    return rx.vstack(
        rx.hstack(
            rx.skeleton(rx.box(height="40px", width="400px"), loading=True),
            rx.spacer(),
            rx.skeleton(rx.box(height="40px", width="80px"), loading=True),
            width="100%", align="center",
        ),
        rx.box(height="1px", width="100%", background=SAKURA_100, margin_y="2rem"),
        *[
            rx.hstack(
                rx.skeleton(rx.box(height="36px", width="36px"), loading=True),
                rx.skeleton(rx.box(height="60px", width="45%"), loading=True),
                rx.skeleton(rx.box(height="60px", width="45%"), loading=True),
                width="100%", spacing="4",
            )
            for _ in range(3)
        ],
        width="100%",
        spacing="4",
    )


def _edit_page(is_create: bool) -> rx.Component:
    return layout(
        rx.vstack(
            rx.cond(
                CollectionState.is_loading,
                skeleton_edit_page(),
                rx.vstack(
                    rx.hstack(
                        rx.input(
                            value=CollectionState.edit_name,
                            on_change=CollectionState.set_edit_name,
                            placeholder="Collection Name…",
                            size="3", width="400px", font_size="1.5rem",
                            background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"},
                            border_color=SAKURA_200,
                            _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.cond(CollectionState.edit_status == "public", "Public", "Private"),
                            size="3",
                            on_click=CollectionState.toggle_status,
                            variant="outline",
                            border_color=SAKURA_200,
                            color=SAKURA_DARK,
                            _hover={"background": SAKURA_100, "border_color": SAKURA_400},
                            cursor="pointer",
                            margin_right="0.5rem",
                        ),
                        rx.button(
                            "Save", size="3",
                            on_click=lambda: CollectionState.save_collection(not is_create),
                            background=SAKURA_500, color="white",
                            _hover={"background": SAKURA_600},
                            cursor="pointer",
                        ),
                        width="100%", align="center",
                    ),
                    rx.box(height="1px", width="100%", background=SAKURA_100, margin_y="2rem"),
                    rx.vstack(
                        rx.foreach(CollectionState.edit_flashcards, lambda fc, idx: edit_flashcard_row(fc, idx)),
                        width="100%", spacing="4",
                    ),
                    rx.button(
                        "Add Card", variant="outline", margin_top="1.5rem", width="100%",
                        on_click=CollectionState.add_flashcard_row,
                        border_color=SAKURA_200,
                        color=SAKURA_DARK,
                        _hover={"background": SAKURA_100, "border_color": SAKURA_400},
                    ),
                    width="100%",
                ),
            ),
            width="100%", max_width="800px", margin="0 auto",
        ),
    )


def create_collection_page() -> rx.Component:
    return _edit_page(is_create=True)


def edit_collection_page() -> rx.Component:
    return _edit_page(is_create=False)


def collection_details_page() -> rx.Component:
    return layout(
        rx.cond(
            CollectionState.is_loading,
            skeleton_detail_page(),
            rx.vstack(
                rx.hstack(
                    rx.heading(CollectionState.collection_info.get("name", "Unknown"), size="8", color=SAKURA_DARK),
                    rx.spacer(),
                    rx.button(
                        rx.icon("copy"), "Duplicate",
                        size="3",
                        on_click=CollectionState.duplicate,
                        variant="outline",
                        border_color=SAKURA_200,
                        color=SAKURA_DARK,
                        _hover={"background": SAKURA_100, "border_color": SAKURA_400},
                    ),
                    width="100%", align="center",
                ),
                rx.text(f"Owner: @{CollectionState.collection_info.get('owner_username', 'Unknown')}", color=SAKURA_MUTED, size="3"),
                rx.box(height="1px", width="100%", background=SAKURA_100, margin_y="2rem"),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Front", color=SAKURA_DARK),
                                rx.table.column_header_cell("Back", color=SAKURA_DARK),
                                background=SAKURA_50,
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                CollectionState.flashcards,
                                lambda fc: rx.table.row(
                                    rx.table.cell(fc["front"], color=SAKURA_DARK),
                                    rx.table.cell(fc["back"], color=SAKURA_MUTED),
                                ),
                            ),
                        ),
                        width="100%",
                    ),
                    border=f"1px solid {SAKURA_100}",
                    border_radius="12px",
                    overflow="hidden",
                    width="100%",
                ),
                width="100%", max_width="800px", margin="0 auto",
            ),
        ),
    )
