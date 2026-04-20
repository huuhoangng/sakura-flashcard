import reflex as rx

# ── Sakura Color Tokens ──
SAKURA_50 = "#FFF5F7"
SAKURA_100 = "#FFE4EC"
SAKURA_200 = "#FFBDD2"
SAKURA_300 = "#FF8FAB"
SAKURA_400 = "#FF6B8A"
SAKURA_500 = "#E8456B"
SAKURA_600 = "#C4364F"
SAKURA_DARK = "#2D1B25"
SAKURA_MUTED = "#7A5A68"
SAKURA_BG = "#FFFBFC"
SAKURA_CARD = "#FFFFFF"


def skeleton_text(width: str = "100%", height: str = "14px") -> rx.Component:
    """A single shimmering text line."""
    return rx.skeleton(
        rx.box(height=height, width=width),
        loading=True,
    )


def skeleton_card() -> rx.Component:
    """Placeholder matching a 200×150 collection/flashcard card."""
    return rx.box(
        rx.vstack(
            rx.skeleton(rx.box(height="70px", width="100%"), loading=True),
            rx.skeleton(rx.box(height="10px", width="60%"), loading=True),
            rx.skeleton(rx.box(height="10px", width="40%"), loading=True),
            spacing="3",
            width="100%",
            padding="1rem",
        ),
        width="200px",
        height="150px",
        border_radius="var(--radius-3)",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
        overflow="hidden",
    )


def skeleton_card_row(count: int = 5) -> rx.Component:
    """A horizontal row of skeleton cards for carousel sections."""
    return rx.hstack(
        *[skeleton_card() for _ in range(count)],
        spacing="4",
        padding="1.5rem",
    )


def skeleton_list_item() -> rx.Component:
    """Placeholder matching a collection list item on the Me page."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.skeleton(rx.box(height="32px", width="70px"), loading=True),
                rx.skeleton(rx.box(height="32px", width="70px"), loading=True),
                spacing="2",
            ),
            rx.skeleton(rx.box(height="24px", width="250px"), loading=True),
            spacing="5",
            align_items="center",
            width="100%",
        ),
        width="100%",
        padding="1rem",
        border_radius="var(--radius-3)",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
    )


def skeleton_list_items(count: int = 3) -> rx.Component:
    """Multiple skeleton list items stacked."""
    return rx.vstack(
        *[skeleton_list_item() for _ in range(count)],
        spacing="4",
        width="100%",
        padding="1rem",
    )


def skeleton_table_rows(cols: int = 4, rows: int = 5) -> rx.Component:
    """Skeleton placeholder for an admin data table."""
    return rx.vstack(
        *[
            rx.hstack(
                *[
                    rx.skeleton(
                        rx.box(height="16px", width=f"{random_width}%"),
                        loading=True,
                    )
                    for random_width in ([20, 35, 25, 20][:cols])
                ],
                spacing="4",
                width="100%",
                padding_y="12px",
                padding_x="1rem",
                border_bottom=f"1px solid {SAKURA_100}",
            )
            for _ in range(rows)
        ],
        spacing="0",
        width="100%",
        border_radius="var(--radius-3)",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
        overflow="hidden",
    )


def skeleton_study_card() -> rx.Component:
    """Placeholder matching the tinder study card."""
    return rx.box(
        rx.vstack(
            rx.center(
                rx.skeleton(rx.box(height="40px", width="200px"), loading=True),
                height="300px",
                width="100%",
            ),
            rx.box(height="1px", width="100%", background=SAKURA_100),
            rx.hstack(
                rx.skeleton(rx.box(height="44px", width="44px"), loading=True),
                rx.spacer(),
                rx.skeleton(rx.box(height="36px", width="36px"), loading=True),
                rx.spacer(),
                rx.skeleton(rx.box(height="44px", width="44px"), loading=True),
                width="100%",
                padding="1rem",
            ),
            width="100%",
            padding="1rem",
        ),
        width="100%",
        max_width="400px",
        margin="0 auto",
        border_radius="1rem",
        border=f"1px solid {SAKURA_100}",
        background=SAKURA_CARD,
        box_shadow=f"0 4px 24px {SAKURA_100}",
    )


def skeleton_detail_page() -> rx.Component:
    """Placeholder for a collection detail page."""
    return rx.vstack(
        rx.hstack(
            rx.skeleton(rx.box(height="36px", width="300px"), loading=True),
            rx.spacer(),
            rx.skeleton(rx.box(height="36px", width="160px"), loading=True),
            width="100%",
            align="center",
        ),
        rx.skeleton(rx.box(height="16px", width="180px"), loading=True),
        rx.box(height="1px", width="100%", background=SAKURA_100, margin_y="2rem"),
        skeleton_table_rows(cols=2, rows=4),
        width="100%",
        max_width="800px",
        margin="0 auto",
    )
