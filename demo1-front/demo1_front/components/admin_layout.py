import reflex as rx
from demo1_front.components.header import header
from demo1_front.state.admin import AdminState
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_400, SAKURA_500,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_BG,
)


def admin_sidebar() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("🌸", font_size="1.2rem"),
            rx.heading("Admin", size="5", weight="bold", color=SAKURA_DARK),
            spacing="2",
            align_items="center",
            margin_bottom="2rem",
        ),
        rx.button(
            rx.icon("users", size=16), "Users",
            variant="ghost", width="100%", justify="start",
            color=SAKURA_DARK,
            _hover={"background": SAKURA_100, "color": SAKURA_500},
            on_click=[AdminState.set_tab("users"), rx.redirect("/admin")],
        ),
        rx.button(
            rx.icon("library", size=16), "Collections",
            variant="ghost", width="100%", justify="start",
            color=SAKURA_DARK,
            _hover={"background": SAKURA_100, "color": SAKURA_500},
            on_click=[AdminState.set_tab("collections"), rx.redirect("/admin")],
        ),
        rx.button(
            rx.icon("layers", size=16), "Flashcards",
            variant="ghost", width="100%", justify="start",
            color=SAKURA_DARK,
            _hover={"background": SAKURA_100, "color": SAKURA_500},
            on_click=[AdminState.set_tab("flashcards"), rx.redirect("/admin")],
        ),
        rx.button(
            rx.icon("scroll-text", size=16), "Logs",
            variant="ghost", width="100%", justify="start",
            color=SAKURA_DARK,
            _hover={"background": SAKURA_100, "color": SAKURA_500},
            on_click=[AdminState.set_tab("logs"), rx.redirect("/admin")],
        ),
        width="240px",
        height="100vh",
        padding="1.5rem",
        background=SAKURA_50,
        border_right=f"1px solid {SAKURA_100}",
        position="sticky",
        top="0",
        spacing="1",
    )


def admin_layout(*children, **props) -> rx.Component:
    return rx.box(
        header(),
        rx.flex(
            rx.box(
                *children,
                padding="2rem",
                width="100%",
                max_width="1200px",
                margin="0 auto",
            ),
            width="100%",
            justify="center",
        ),
        width="100%",
        min_height="100vh",
        background=SAKURA_BG,
    )
