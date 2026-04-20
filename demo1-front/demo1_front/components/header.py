import reflex as rx
from demo1_front.state.auth import AuthState
from demo1_front.state.search import SearchState
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_200, SAKURA_400, SAKURA_500,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
)


def search_result_item(item: dict) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.vstack(
                rx.text(item.get("title", ""), weight="bold", size="3", color=SAKURA_DARK),
                rx.text(item.get("subtitle", ""), size="1", color=SAKURA_MUTED),
                align_items="start",
            ),
            rx.spacer(),
            rx.badge(item.get("type", ""), color_scheme="pink", radius="full"),
            width="100%",
            padding="10px 12px",
            _hover={"background": SAKURA_50},
            border_radius="8px",
            transition="background 0.15s",
        ),
        href=item.get("url", "#"),
        width="100%",
        text_decoration="none",
        color="inherit",
    )


def header() -> rx.Component:
    return rx.hstack(
        # ── Logo ──
        rx.link(
            rx.hstack(
                rx.text("🌸", font_size="1.4rem"),
                rx.heading("Sakura Flashcard", size="5", weight="bold", color=SAKURA_500),
                spacing="2",
                align_items="center",
            ),
            href="/",
            _hover={"text_decoration": "none", "opacity": "0.85"},
            transition="opacity 0.15s",
        ),

        rx.spacer(),

        # ── Search Bar ──
        rx.vstack(
            rx.hstack(
                rx.input(
                    placeholder="Search collections, cards, users…",
                    width="380px",
                    radius="full",
                    size="3",
                    value=SearchState.query,
                    on_change=SearchState.handle_input,
                    background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"},
                    border_color=SAKURA_200,
                    _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
                ),
                rx.icon_button(
                    rx.icon("search"),
                    size="3",
                    radius="full",
                    variant="soft",
                    color_scheme="pink",
                    on_click=SearchState.perform_search,
                ),
                align_items="center",
            ),
            # ── Results Dropdown ──
            rx.cond(
                SearchState.show_results & (SearchState.query != ""),
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.button("Collection", variant=rx.cond(SearchState.show_collection, "solid", "outline"), size="1", radius="full", color_scheme="pink", on_click=lambda: SearchState.toggle_filter("collection")),
                            rx.button("Flashcard", variant=rx.cond(SearchState.show_flashcard, "solid", "outline"), size="1", radius="full", color_scheme="pink", on_click=lambda: SearchState.toggle_filter("flashcard")),
                            rx.button("User", variant=rx.cond(SearchState.show_user, "solid", "outline"), size="1", radius="full", color_scheme="pink", on_click=lambda: SearchState.toggle_filter("user")),
                            margin_bottom="2",
                            width="100%",
                            padding_x="12px",
                            padding_y="8px",
                        ),
                        rx.box(height="1px", width="100%", background=SAKURA_100),
                        rx.cond(
                            SearchState.is_searching,
                            rx.center(rx.spinner(size="2", color=SAKURA_400), padding="4", width="100%"),
                            rx.scroll_area(
                                rx.vstack(
                                    rx.foreach(SearchState.results, search_result_item),
                                    spacing="1",
                                    width="100%",
                                ),
                                type="always",
                                scrollbars="vertical",
                                max_height="300px",
                                width="100%",
                            ),
                        ),
                        rx.button(
                            "Close", variant="ghost", width="100%", size="1",
                            color=SAKURA_MUTED,
                            on_click=SearchState.set_show_results(False),
                        ),
                    ),
                    position="absolute",
                    top="100%",
                    left="0",
                    width="100%",
                    margin_top="4px",
                    background=SAKURA_CARD,
                    border=f"1px solid {SAKURA_100}",
                    box_shadow=f"0 8px 32px {SAKURA_100}",
                    border_radius="12px",
                    z_index="100",
                    padding_y="8px",
                ),
                rx.fragment(),
            ),
            position="relative",
        ),

        rx.spacer(),

        # ── Navigation ──
        rx.hstack(
            rx.button(
                rx.icon("user"), "Me",
                on_click=rx.redirect("/me"),
                variant="ghost", size="3",
                color=SAKURA_DARK,
                _hover={"background": SAKURA_50, "color": SAKURA_500},
            ),
            rx.cond(
                AuthState.is_admin,
                rx.button(
                    rx.icon("shield"), "Admin",
                    on_click=rx.redirect("/admin"),
                    variant="ghost", size="3",
                    color=SAKURA_MUTED,
                    _hover={"background": SAKURA_50, "color": SAKURA_500},
                ),
                rx.fragment(),
            ),
            rx.button(
                rx.icon("log-out"), "Logout",
                on_click=AuthState.logout,
                variant="ghost", size="3",
                color=SAKURA_MUTED,
                _hover={"background": "#FFF0F0", "color": "#C4364F"},
            ),
            spacing="4",
        ),

        # ── Header Container Style ──
        width="100%",
        padding_x="2rem",
        padding_y="0.75rem",
        align_items="center",
        justify="between",
        background=f"rgba(255,255,255,0.85)",
        backdrop_filter="blur(12px)",
        border_bottom=f"1px solid {SAKURA_100}",
        position="sticky",
        top="0",
        z_index="999",
    )
