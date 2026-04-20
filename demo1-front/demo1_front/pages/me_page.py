import reflex as rx
from demo1_front.components.layout import layout
from demo1_front.state.me import MeState
from demo1_front.components.skeleton import (
    SAKURA_50, SAKURA_100, SAKURA_200, SAKURA_400, SAKURA_500, SAKURA_600,
    SAKURA_DARK, SAKURA_MUTED, SAKURA_CARD,
    skeleton_list_items,
)


def collection_list_item(collection: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.button(
                    "Study",
                    size="2",
                    width="100%",
                    on_click=rx.redirect(f"/study/{collection['id']}"),
                    disabled=collection["flashcard_count"].to(int) < 4,
                    background=SAKURA_400,
                    color="white",
                    _hover={"background": SAKURA_500},
                    cursor="pointer",
                ),
                rx.button(
                    "Edit", variant="outline", size="2",
                    width="100%",
                    on_click=rx.redirect(f"/collection/edit/{collection['id']}"),
                    border_color=SAKURA_200,
                    color=SAKURA_DARK,
                    _hover={"background": SAKURA_100, "border_color": SAKURA_400},
                ),
                width="90px",
                align_items="center",
                spacing="2",
            ),
            rx.vstack(
                rx.heading(
                    collection["name"],
                    size="4",
                    cursor="pointer",
                    on_click=rx.redirect(f"/collection/{collection['id']}"),
                    color=SAKURA_DARK,
                    _hover={"color": SAKURA_500},
                    transition="color 0.15s",
                ),
                rx.text(
                    collection["status"],
                    size="2",
                    font_style="italic",
                    color=SAKURA_MUTED,
                ),
                spacing="1",
                align_items="start",
            ),
            spacing="5",
            align_items="center",
        ),
        width="100%",
        padding="1rem",
        border_radius="12px",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
        _hover={"border_color": SAKURA_200, "box_shadow": f"0 2px 12px {SAKURA_100}"},
        transition="all 0.2s ease",
    )


def change_password_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Change Password", color=SAKURA_DARK),
            rx.dialog.description("Enter your old and new password.", color=SAKURA_MUTED),
            rx.flex(
                rx.text("Old Password", size="2", weight="bold", color=SAKURA_DARK),
                rx.input(placeholder="Old Password", type="password", on_change=MeState.set_old_password, value=MeState.old_password, background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"}, border_color=SAKURA_200, _focus={"border_color": SAKURA_400}),
                rx.text("New Password", size="2", weight="bold", color=SAKURA_DARK),
                rx.input(placeholder="New Password", type="password", on_change=MeState.set_new_password, value=MeState.new_password, background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"}, border_color=SAKURA_200, _focus={"border_color": SAKURA_400}),
                rx.text("Retype New Password", size="2", weight="bold", color=SAKURA_DARK),
                rx.input(placeholder="Confirm Password", type="password", on_change=MeState.set_confirm_password, value=MeState.confirm_password, background=SAKURA_50, color=SAKURA_DARK, _placeholder={"color": "#5c3d4a"}, border_color=SAKURA_200, _focus={"border_color": SAKURA_400}),
                direction="column",
                spacing="3",
                padding_y="3",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray", on_click=MeState.close_password_dialog)
                ),
                rx.button("Save", on_click=MeState.change_password, background=SAKURA_500, color="white", _hover={"background": SAKURA_600}),
                spacing="3",
                justify="end",
            ),
        ),
        open=MeState.show_password_dialog,
    )


def me_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading(MeState.username, size="7", color=SAKURA_DARK),
                    rx.button(
                        "Create Collection",
                        on_click=rx.redirect("/collection/create"),
                        margin_top="1rem",
                        width="100%",
                        background=SAKURA_500,
                        color="white",
                        _hover={"background": SAKURA_600},
                        cursor="pointer",
                    ),
                    rx.button(
                        "Change Password",
                        on_click=MeState.open_password_dialog,
                        variant="outline",
                        margin_top="0.5rem",
                        width="100%",
                        border_color=SAKURA_200,
                        color=SAKURA_DARK,
                        _hover={"background": SAKURA_100, "border_color": SAKURA_400},
                    ),
                    align_items="start",
                    width="250px",
                ),
                rx.box(width="1px", background=SAKURA_100),
                rx.vstack(
                    rx.heading("My Collections", size="6", margin_bottom="1rem", color=SAKURA_DARK),
                    rx.cond(
                        MeState.is_loading,
                        skeleton_list_items(4),
                        rx.scroll_area(
                            rx.vstack(
                                rx.foreach(
                                    MeState.my_collections,
                                    collection_list_item,
                                ),
                                spacing="3",
                                padding="0.5rem",
                            ),
                            type="always",
                            scrollbars="vertical",
                            width="100%",
                            flex="1",
                        ),
                    ),
                    width="100%",
                    align_items="start",
                    flex="1",
                ),
                spacing="8",
                width="100%",
                align_items="start",
                height="100%",
            ),
            change_password_dialog(),
            width="100%",
            height="100%",
            spacing="0",
        ),
    )
