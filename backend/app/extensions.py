from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_mail import Mail
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
mail = Mail()
bcrypt = Bcrypt()