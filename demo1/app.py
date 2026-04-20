import sys
import os

if sys.platform == 'win32':
    # Workaround for VSCode debugger (debugpy) crashing with PyTorch on Windows
    _original_realpath = os.path.realpath
    def _safe_realpath(*args, **kwargs):
        if args and isinstance(args[0], str) and args[0].startswith('<'):
            return args[0]
        return _original_realpath(*args, **kwargs)
    os.path.realpath = _safe_realpath

from flask import Flask
from config import Config
from extensions import db, jwt
from controllers.auth import auth_bp
from controllers.admin import admin_bp
from controllers.collection import collection_bp
from controllers.flashcard import flashcard_bp
from controllers.recommendation import recommendation_bp
from controllers.search import search_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(collection_bp, url_prefix='/api/collections')
    app.register_blueprint(flashcard_bp, url_prefix='/api/flashcards')
    app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')
    app.register_blueprint(search_bp, url_prefix='/api/search')

    # Create tables
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)