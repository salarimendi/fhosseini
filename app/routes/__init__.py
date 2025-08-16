# routes/__init__.py
from flask import Blueprint

# Import all route blueprints
from .main import main_bp
from .auth import auth_bp
from .verses import verses_bp
from .comments import comments_bp
from .admin import admin_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(verses_bp, url_prefix='/verses')
    app.register_blueprint(comments_bp, url_prefix='/comments')
    app.register_blueprint(admin_bp, url_prefix='/admin')