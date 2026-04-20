import reflex as rx
from demo1_front.components.header import header
from demo1_front.components.skeleton import SAKURA_BG


def layout(*children, hide_header: bool = False, **props) -> rx.Component:
    """The main app layout with sakura theme."""

    return rx.box(
        rx.cond(
            hide_header,
            rx.fragment(),
            header()
        ),

        rx.box(
            *children,
            padding="2rem",
            max_width="1200px",
            margin="0 auto",
        ),

        width="100%",
        min_height="100vh",
        background=f"linear-gradient(180deg, {SAKURA_BG} 0%, #FFF5F7 100%)",
        **props,
    )
