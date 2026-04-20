import reflex as rx
from demo1_front.state.auth import AuthState
from demo1_front.state.home import HomeState
from demo1_front.pages.auth_pages import login_page, signup_page
from demo1_front.pages.home_page import index
from demo1_front.pages.me_page import me_page
from demo1_front.state.me import MeState
from demo1_front.pages.user_page import user_page
from demo1_front.state.user import UserState

app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="pink",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
    style={
        "font_family": "'Inter', sans-serif",
        "::selection": {
            "background": "#FFE4EC",
            "color": "#2D1B25",
        },
        "input": {
            "color": "black",
        },
        "textarea": {
            "color": "black",
        },
        "::placeholder": {
            "color": "#2D1B25",
            "opacity": "1",
        },
    },
)

app.add_page(
    index,
    route="/",
    on_load=[AuthState.check_auth_validity, HomeState.load_recommendations]
)
app.add_page(
    login_page,
    route="/login",
    on_load=AuthState.redirect_if_auth
)
app.add_page(
    signup_page,
    route="/signup",
    on_load=AuthState.redirect_if_auth
)
app.add_page(
    me_page,
    route="/me",
    on_load=[AuthState.check_auth_validity, MeState.load_profile]
)
app.add_page(
    user_page,
    route="/user/[username_param]",
    on_load=[AuthState.check_auth_validity, UserState.load_user_profile]
)

from demo1_front.pages.collection_page import create_collection_page, edit_collection_page, collection_details_page
from demo1_front.state.collection import CollectionState

app.add_page(
    create_collection_page,
    route="/collection/create",
    on_load=[AuthState.check_auth_validity, CollectionState.handle_create_load]
)
app.add_page(
    edit_collection_page,
    route="/collection/edit/[col_id]",
    on_load=[AuthState.check_auth_validity, CollectionState.handle_edit_load]
)
app.add_page(
    collection_details_page,
    route="/collection/[col_id]",
    on_load=[AuthState.check_auth_validity, CollectionState.load_collection]
)

from demo1_front.pages.study_page import study_page
from demo1_front.state.study import StudyState

app.add_page(
    study_page,
    route="/study/[col_id]",
    on_load=[AuthState.check_auth_validity, StudyState.load_study_session]
)

from demo1_front.pages.admin_pages import admin_dashboard
from demo1_front.state.admin import AdminState

app.add_page(admin_dashboard, route="/admin", on_load=[AuthState.check_auth_validity, AdminState.initial_load])
