from flask import Flask
from flask_cors import CORS
from .extensions import db, cache, jwt, mail
from .config import Config
from .models import Users
# from .routes import main as main_blueprint, auth as auth_blueprint
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    ## Initialize the extensions
    db.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)

    with app.app_context():
        db.create_all()
        create_admin_user()

    return app

def create_admin_user():
    with db.session.begin():
        admin = Users.query.filter_by(role='admin').first()
        if not admin:
            admin = Users(username='admin', email = 'admin@adveri.com', password='root', role='admin')
            db.session.add(admin)
            db.session.commit()