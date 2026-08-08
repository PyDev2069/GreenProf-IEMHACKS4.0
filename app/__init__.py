from flask import Flask
from app.config import Config
from app.extensions import db, migrate, mail, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.models import user, product, stage
        from app.models import carbon_card  # noqa: F401 — registers model with SQLAlchemy

    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.products import bp as products_bp
    from app.routes.carbon_card import bp as carbon_card_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(carbon_card_bp)

    return app