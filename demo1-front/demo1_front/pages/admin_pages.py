import reflex as rx
from demo1_front.components.admin_layout import admin_layout
from demo1_front.state.admin import AdminState
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_200, SAKURA_400, SAKURA_500,
    SAKURA_DARK, SAKURA_MUTED,
    skeleton_table_rows,
)


def search_bar() -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="Search current tab…",
            on_change=AdminState.set_search_term,
            value=AdminState.search_term,
            background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"},
            border_color=SAKURA_200,
            _focus={"border_color": SAKURA_400, "box_shadow": f"0 0 0 2px {SAKURA_200}"},
            radius="full",
            size="2",
            width="250px",
        ),
        rx.icon_button(
            rx.icon("search"), on_click=AdminState.perform_search,
            variant="soft", color_scheme="pink", radius="full", size="2",
        ),
        align_items="center",
    )

def pagination_controls() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left"), "Previous",
            on_click=AdminState.prev_page,
            disabled=AdminState.page <= 1,
            variant="soft", color_scheme="pink", size="2",
        ),
        rx.text(f"Page {AdminState.page} of {AdminState.total_pages}", size="2", color=SAKURA_MUTED),
        rx.button(
            "Next", rx.icon("chevron-right"),
            on_click=AdminState.next_page,
            disabled=AdminState.page >= AdminState.total_pages,
            variant="soft", color_scheme="pink", size="2",
        ),
        align="center", spacing="4", margin_top="1rem", justify="center", width="100%"
    )


def sortable_header(label: str, column_key: str) -> rx.Component:
    """A clickable column header that triggers sorting and shows direction arrows."""
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, color=SAKURA_DARK, weight="medium"),
            rx.cond(
                AdminState.sort_column == column_key,
                rx.cond(
                    AdminState.sort_ascending,
                    rx.icon("arrow-up", size=14, color=SAKURA_400),
                    rx.icon("arrow-down", size=14, color=SAKURA_400),
                ),
                rx.icon("arrow-up-down", size=14, color=SAKURA_MUTED, opacity="0.4"),
            ),
            spacing="1",
            align="center",
        ),
        cursor="pointer",
        on_click=lambda: AdminState.toggle_sort(column_key),
        _hover={"background": SAKURA_100},
        transition="background 0.15s ease",
    )


def users_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    sortable_header("ID", "id"),
                    sortable_header("Username", "username"),
                    sortable_header("Role", "role"),
                    rx.table.column_header_cell("Action", color=SAKURA_DARK),
                    background=SAKURA_50,
                ),
            ),
            rx.table.body(
                rx.foreach(
                    AdminState.users,
                    lambda u: rx.table.row(
                        rx.table.cell(rx.link(u.get("id", ""), href=f"/user/{u.get('username', '')}", color=SAKURA_400, _hover={"color": SAKURA_500})),
                        rx.table.cell(u.get("username", ""), color=SAKURA_DARK),
                        rx.table.cell(u.get("role", ""), color=SAKURA_MUTED),
                        rx.table.cell(
                            rx.button(rx.icon("trash"), color_scheme="red", variant="soft",
                                     on_click=lambda: AdminState.delete_user(u.get("id", "")))
                        ),
                    ),
                ),
            ),
            width="100%",
        ),
        border=f"1px solid {SAKURA_100}",
        border_radius="12px",
        overflow="hidden",
        width="100%",
    )


def collections_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    sortable_header("ID", "id"),
                    sortable_header("Name", "name"),
                    sortable_header("Owner ID", "user_id"),
                    rx.table.column_header_cell("Action", color=SAKURA_DARK),
                    background=SAKURA_50,
                ),
            ),
            rx.table.body(
                rx.foreach(
                    AdminState.collections,
                    lambda c: rx.table.row(
                        rx.table.cell(c.get("id", ""), color=SAKURA_MUTED),
                        rx.table.cell(rx.link(c.get("name", ""), href=f"/collection/{c.get('id', '')}", color=SAKURA_400, _hover={"color": SAKURA_500})),
                        rx.table.cell(c.get("user_id", ""), color=SAKURA_MUTED),
                        rx.table.cell(
                            rx.hstack(
                                rx.button(rx.icon("pencil"), variant="soft", color_scheme="pink",
                                         on_click=rx.redirect(f"/collection/edit/{c.get('id', '')}")),
                                rx.button(rx.icon("trash"), color_scheme="red", variant="soft",
                                         on_click=lambda: AdminState.delete_collection(c.get("id", ""))),
                            ),
                        ),
                    ),
                ),
            ),
            width="100%",
        ),
        border=f"1px solid {SAKURA_100}",
        border_radius="12px",
        overflow="hidden",
        width="100%",
    )


def flashcards_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    sortable_header("ID", "id"),
                    sortable_header("Front", "front"),
                    sortable_header("Collection", "collection_id"),
                    rx.table.column_header_cell("Action", color=SAKURA_DARK),
                    background=SAKURA_50,
                ),
            ),
            rx.table.body(
                rx.foreach(
                    AdminState.flashcards,
                    lambda f: rx.table.row(
                        rx.table.cell(f.get("id", ""), color=SAKURA_MUTED),
                        rx.table.cell(f.get("front", ""), color=SAKURA_DARK),
                        rx.table.cell(rx.link(f.get("collection_id", ""), href=f"/collection/{f.get('collection_id', '')}", color=SAKURA_400, _hover={"color": SAKURA_500})),
                        rx.table.cell(
                            rx.button(rx.icon("trash"), color_scheme="red", variant="soft",
                                     on_click=lambda: AdminState.delete_flashcard(f.get("id", "")))
                        ),
                    ),
                ),
            ),
            width="100%",
        ),
        border=f"1px solid {SAKURA_100}",
        border_radius="12px",
        overflow="hidden",
        width="100%",
    )


def logs_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    sortable_header("ID", "id"),
                    sortable_header("User ID", "user_id"),
                    sortable_header("Action", "action"),
                    sortable_header("Time", "time"),
                    background=SAKURA_50,
                ),
            ),
            rx.table.body(
                rx.foreach(
                    AdminState.logs,
                    lambda l: rx.table.row(
                        rx.table.cell(l.get("id", ""), color=SAKURA_MUTED),
                        rx.table.cell(l.get("user_id", ""), color=SAKURA_MUTED),
                        rx.table.cell(l.get("action", ""), color=SAKURA_DARK),
                        rx.table.cell(l.get("time", ""), color=SAKURA_MUTED),
                    ),
                ),
            ),
            width="100%",
        ),
        border=f"1px solid {SAKURA_100}",
        border_radius="12px",
        overflow="hidden",
        width="100%",
    )


def admin_dashboard() -> rx.Component:
    return admin_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Admin Dashboard", size="8", color=SAKURA_DARK),
                rx.spacer(),
                search_bar(),
                width="100%", align="center", margin_bottom="1rem",
            ),
            
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger(rx.hstack(rx.icon("users"), rx.text("Users"), color=SAKURA_DARK), value="users"),
                    rx.tabs.trigger(rx.hstack(rx.icon("library"), rx.text("Collections"), color=SAKURA_DARK), value="collections"),
                    rx.tabs.trigger(rx.hstack(rx.icon("layers"), rx.text("Flashcards"), color=SAKURA_DARK), value="flashcards"),
                    rx.tabs.trigger(rx.hstack(rx.icon("scroll-text"), rx.text("Logs"), color=SAKURA_DARK), value="logs"),
                    width="100%",
                    margin_bottom="1rem",
                ),
                rx.cond(
                    AdminState.is_loading,
                    skeleton_table_rows(cols=4, rows=6),
                    rx.fragment(
                        rx.tabs.content(users_table(), value="users"),
                        rx.tabs.content(collections_table(), value="collections"),
                        rx.tabs.content(flashcards_table(), value="flashcards"),
                        rx.tabs.content(logs_table(), value="logs"),
                        pagination_controls(),
                    )
                ),
                value=AdminState.current_tab,
                on_change=AdminState.set_tab,
                width="100%",
            ),
            width="100%",
            spacing="4",
        )
    )
