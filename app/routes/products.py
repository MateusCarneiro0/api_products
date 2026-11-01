from flask import Blueprint,jsonify
from sqlalchemy import select
from ..db.models.Product import Product
from ..db import db

products_bp = Blueprint("products_bp",__name__,url_prefix="/products")

@products_bp.route("/<string:id>")
def fetchProductsId(id):
    product = Product.query.get_or_404(id)
    if not product == None:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({"error": "product not found"}), 404


@products_bp.route("/")
def fetchProducts():
    selected_products = select(Product).limit(50)
    raw_products = db.session.scalars(selected_products).all()
    products = [product.to_dict() for product in raw_products]
    return jsonify(products)