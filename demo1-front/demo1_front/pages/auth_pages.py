import reflex as rx
from demo1_front.state.auth import AuthState
from demo1_front.components.layout import layout
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_200, SAKURA_400, SAKURA_500, SAKURA_600,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
)


def login_page() -> rx.Component:
    return layout(
        rx.center(
            rx.card(
                rx.vstack(
                    rx.center(
                        rx.vstack(
                            rx.text("🌸", font_size="2.5rem", text_align="center"),
                            rx.heading("Welcome back", size="6", weight="bold", color=SAKURA_DARK),
                            rx.text("Sign in to continue learning", size="2", color=SAKURA_MUTED),
                            align_items="center",
                            spacing="2",
                        ),
                        width="100%",
                        margin_bottom="1.5rem",
                    ),
                    rx.cond(
                        AuthState.show_login_error,
                        rx.callout(
                            AuthState.login_error,
                            size="1",
                            color_scheme="red",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.text("Username", size="2", weight="medium", color=SAKURA_DARK),
                    rx.input(
                        placeholder="Enter username…",
                        on_change=AuthState.set_login_username,
                        value=AuthState.login_username,
                        width="100%", size="3",
                        background=SAKURA_50,
                        color=SAKURA_DARK,
                        _placeholder={"color": "#5c3d4a"},
                        border_color=SAKURA_200,
                        _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
                    ),
                    rx.text("Password", size="2", weight="medium", color=SAKURA_DARK),
                    rx.input(
                        placeholder="Enter password…",
                        type="password",
                        on_change=AuthState.set_login_password,
                        value=AuthState.login_password,
                        width="100%", size="3",
                        background=SAKURA_50,
                        color=SAKURA_DARK,
                        _placeholder={"color": "#5c3d4a"},
                        border_color=SAKURA_200,
                        _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
                    ),
                    rx.button(
                        "Log In", size="3", width="100%",
                        on_click=AuthState.login, margin_top="0.5rem",
                        background=SAKURA_500, color="white",
                        _hover={"background": SAKURA_600},
                        cursor="pointer",
                    ),
                    rx.flex(
                        rx.text("Don't have an account?", size="2", color=SAKURA_MUTED),
                        rx.button(
                            "Sign Up", variant="ghost", size="2",
                            on_click=rx.redirect("/signup"),
                            color=SAKURA_400,
                            _hover={"color": SAKURA_500},
                        ),
                        justify="between", width="100%", margin_top="0.5rem", align="center",
                    ),
                    spacing="3",
                    width="100%",
                ),
                max_width="400px",
                width="100%",
                padding="2rem",
                background=SAKURA_CARD,
                border=f"1px solid {SAKURA_100}",
                box_shadow=f"0 8px 40px {SAKURA_100}",
            ),
            width="100%",
            height="80vh",
        ),
        hide_header=True,
    )


def signup_page() -> rx.Component:
    return layout(
        rx.center(
            rx.card(
                rx.vstack(
                    rx.center(
                        rx.vstack(
                            rx.text("🌸", font_size="2.5rem", text_align="center"),
                            rx.heading("Create account", size="6", weight="bold", color=SAKURA_DARK),
                            rx.text("Start your learning journey", size="2", color=SAKURA_MUTED),
                            align_items="center",
                            spacing="2",
                        ),
                        width="100%",
                        margin_bottom="1.5rem",
                    ),
                    rx.cond(
                        AuthState.show_signup_error,
                        rx.callout(
                            AuthState.signup_error,
                            size="1",
                            color_scheme="red",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        AuthState.show_signup_success,
                        rx.callout(
                            AuthState.signup_success,
                            size="1",
                            color_scheme="green",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.text("Username", size="2", weight="medium", color=SAKURA_DARK),
                    rx.input(
                        placeholder="Choose username…",
                        on_change=AuthState.set_signup_username,
                        value=AuthState.signup_username,
                        width="100%", size="3",
                        background=SAKURA_50,
                        color=SAKURA_DARK,
                        _placeholder={"color": "#5c3d4a"},
                        border_color=SAKURA_200,
                        _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
                    ),
                    rx.text("Password", size="2", weight="medium", color=SAKURA_DARK),
                    rx.input(
                        placeholder="Choose password…",
                        type="password",
                        on_change=AuthState.set_signup_password,
                        value=AuthState.signup_password,
                        width="100%", size="3",
                        background=SAKURA_50,
                        color=SAKURA_DARK,
                        _placeholder={"color": "#5c3d4a"},
                        border_color=SAKURA_200,
                        _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
                    ),
                    rx.button(
                        "Sign Up", size="3", width="100%",
                        on_click=AuthState.signup, margin_top="0.5rem",
                        background=SAKURA_500, color="white",
                        _hover={"background": SAKURA_600},
                        cursor="pointer",
                    ),
                    rx.flex(
                        rx.text("Already have an account?", size="2", color=SAKURA_MUTED),
                        rx.button(
                            "Log In", variant="ghost", size="2",
                            on_click=rx.redirect("/login"),
                            color=SAKURA_400,
                            _hover={"color": SAKURA_500},
                        ),
                        justify="between", width="100%", margin_top="0.5rem", align="center",
                    ),
                    spacing="3",
                    width="100%",
                ),
                max_width="400px",
                width="100%",
                padding="2rem",
                background=SAKURA_CARD,
                border=f"1px solid {SAKURA_100}",
                box_shadow=f"0 8px 40px {SAKURA_100}",
            ),
            width="100%",
            height="80vh",
        ),
        hide_header=True,
    )
