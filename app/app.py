from flask import Flask, jsonify
from flask_cors import CORS

from sqlalchemy import select

from .db import db
from .db.models.Product import Product

from .env_variables import url, client_site, host, port, is_dev

from .routes.users import users_bp
from .routes.auth import auth_bp
from .routes.products import products_bp 

def create_app():
    app = Flask(__name__)

    CORS(
        app,
        origins=["http://localhost:5173", client_site, "http://localhost:4173"],
        supports_credentials=True,
    )
    treated_uri = ""

    if url.startswith("postgres://"):
        treated_uri = url.replace("postgres://", "postgresql://", 1)
    else:
        treated_uri = url

    app.config["SQLALCHEMY_DATABASE_URI"] = treated_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    db.init_app(app=app)

    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    @app.route("/")
    def fetchProducts():
        selected_products = select(Product).limit(50)
        raw_products = db.session.scalars(selected_products).all()
        products = [product.to_dict() for product in raw_products]
        return jsonify(products)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=host, port=port, debug=is_dev)
