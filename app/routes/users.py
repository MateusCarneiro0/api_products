from flask import Blueprint,request,jsonify

from ..db.models.User import User
from ..db import db

from ..auth.authentication import required_authentication

users_bp = Blueprint("users_bp",__name__,url_prefix="/users")

@users_bp.route("/me", methods=["GET"])
@required_authentication
def fetchUser(id):
    try:
        selectedUser = User.query.get_or_404(id)
        if selectedUser is None:
            return jsonify({"error": "Not user found"}), 404
        return jsonify(
            {
                "user": selectedUser.user,
                "cart": selectedUser.cart,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@users_bp.route("/cart", methods=["GET", "POST", "DELETE"])  # type: ignore
@required_authentication
def fetchCart(id):
    selectedUser = User.query.get_or_404(id)
    if request.method == "GET":
        try:
            cart = selectedUser.cart
            return jsonify({"cart": cart}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    elif request.method == "POST":
        try:
            product = request.get_json()["product"]
            if not product or "id" not in product:
                return jsonify({"error": "has not the parameter 'id'"})

            cart = list(selectedUser.cart) if selectedUser.cart is not None else []

            cart = [x for x in cart if x["id"] != product["id"]]

            cart.append(product)

            selectedUser.cart = cart

            db.session.commit()
            return jsonify({"cart": selectedUser.cart}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    elif request.method == "DELETE":
        try:
            product_id = request.get_json()["id"]
            cart = list(selectedUser.cart) if selectedUser.cart is not None else []
            cart = (
                list(filter(lambda product: product["id"] != product_id, cart))
                if selectedUser.cart is not None
                else []
            )
            selectedUser.cart = cart
            db.session.commit()
            return jsonify({"cart": selectedUser.cart})
        except Exception as e:
            return {"error": str(e)}, 500


@users_bp.route("/clearCart", methods=["DELETE"])
@required_authentication
def clearCart(id):
    try:
        selectedUser = User.query.get_or_404(id)
        selectedUser.cart = []
        db.session.commit()
        return jsonify({"cart": selectedUser.cart, "status": "clean"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500