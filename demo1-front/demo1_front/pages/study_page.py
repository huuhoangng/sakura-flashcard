import reflex as rx
from demo1_front.components.layout import layout
from demo1_front.state.study import StudyState
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_200, SAKURA_300, SAKURA_400, SAKURA_500,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
    skeleton_study_card,
)


def tinder_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.center(
                rx.text(
                    rx.cond(
                        StudyState.is_flipped,
                        StudyState.current_card.get("back", ""),
                        StudyState.current_card.get("front", ""),
                    ),
                    size="6", weight="bold", color=SAKURA_DARK, text_align="center",
                ),
                height="300px", width="100%",
                padding="2rem",
            ),
            rx.box(height="1px", width="100%", background=SAKURA_100),
            rx.hstack(
                rx.button(
                    rx.icon("x"), size="4", variant="soft",
                    color_scheme="red",
                    on_click=StudyState.tinder_swipe_left,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("flip-vertical"), variant="outline",
                    on_click=StudyState.flip_card,
                    border_color=SAKURA_200, color=SAKURA_DARK,
                    _hover={"background": SAKURA_100, "border_color": SAKURA_400},
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("check"), size="4", variant="soft",
                    background=SAKURA_400, color="white",
                    _hover={"background": SAKURA_500},
                    on_click=StudyState.tinder_swipe_right,
                ),
                width="100%", padding="1rem",
            ),
            width="100%",
        ),
        width="100%", max_width="400px", margin="0 auto",
        border_radius="1rem",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
        box_shadow=f"0 8px 32px {SAKURA_100}",
    )


def kahoot_view() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.center(
                rx.text(StudyState.kahoot_query, size="6", weight="bold", color=SAKURA_DARK, text_align="center"),
                height="180px", width="100%", padding="2rem",
            ),
            width="100%", max_width="600px",
            border_radius="1rem",
            border=f"1px solid {SAKURA_100}",
            background=SAKURA_CARD,
            box_shadow=f"0 4px 20px {SAKURA_100}",
            margin_bottom="1.5rem",
        ),
        rx.grid(
            rx.foreach(
                StudyState.kahoot_choices,
                lambda choice, idx: rx.button(
                    choice,
                    size="4", min_height="90px", height="auto", width="100%",
                    white_space="normal",
                    on_click=lambda: StudyState.submit_kahoot_answer(idx),
                    variant="outline",
                    border_color=SAKURA_200,
                    color=SAKURA_DARK,
                    _hover={"background": SAKURA_100, "border_color": SAKURA_400, "color": SAKURA_500},
                    transition="all 0.15s",
                    cursor="pointer",
                ),
            ),
            columns="2", spacing="4", width="100%", max_width="600px",
        ),
        align_items="center",
        width="100%",
    )


def study_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Study Session", size="7", color=SAKURA_DARK),
                rx.spacer(),
                rx.select(
                    ["Card learning", "Quiz"],
                    value=StudyState.mode,
                    on_change=StudyState.set_mode,
                    color=SAKURA_DARK,
                ),
                width="100%", align="center", max_width="800px", margin="0 auto",
            ),
            rx.box(height="1px", width="100%", background=SAKURA_100, margin_y="1.5rem"),
            rx.cond(
                StudyState.is_loading,
                skeleton_study_card(),
                rx.cond(
                    StudyState.is_completed,
                    rx.box(
                        rx.vstack(
                            rx.text("🌸", font_size="3rem"),
                            rx.heading("Well done!", size="8", color=SAKURA_500),
                            rx.text("You've completed all due cards for today.", color=SAKURA_MUTED, size="3"),
                            rx.button(
                                "Back to Collection",
                                on_click=rx.redirect(f"/collection/{StudyState.collection_id}"),
                                margin_top="1.5rem",
                                background=SAKURA_500, color="white",
                                _hover={"background": SAKURA_400},
                                cursor="pointer",
                            ),
                            align_items="center",
                            padding="3rem",
                            spacing="3",
                        ),
                        width="100%", max_width="500px", margin="0 auto",
                        border_radius="1rem",
                        border=f"1px solid {SAKURA_100}",
                        background=SAKURA_CARD,
                        box_shadow=f"0 8px 32px {SAKURA_100}",
                    ),
                    rx.cond(
                        StudyState.mode == "Card learning",
                        tinder_card(),
                        kahoot_view(),
                    ),
                ),
            ),
            width="100%",
        ),
    )
