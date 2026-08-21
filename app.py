from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from products import products
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, JSON
from sqlalchemy.exc import IntegrityError, DataError
import uuid
import os
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    get_jwt_identity,
    create_access_token,
)
import datetime
import jwt
import functools

uri = os.getenv("DATABASE_URL", "sqlite:///users.db")
secret_key_jwt = os.getenv("JWT_SECRET_KEY_APP", "COLOQUE UMA CHAVE IMEDIATAMENTE")

app = Flask(__name__)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=14)
app.config["JWT_SECRET_KEY"] = secret_key_jwt

CORS(app)

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

algorithm = os.getenv("ALGORITHM","HS256")


def create_token():
    token = request.headers.get("Authentication")
    if token is None:
        return jsonify(
            {
                "error": "No JWT Token",
            }
        ), 401
    return token


def create_acess_token(data):
    payload = {
        "id": data,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=7),
    }
    token = jwt.encode(key=secret_key_jwt, payload=payload)
    return token


def required_authentication(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        try:
            token = create_token()

            data_decoded = jwt.decode(
                jwt=token,# type:ignore
                key=secret_key_jwt,
                algorithms=[algorithm],  
            )
            return func(*args, **kwargs, id=data_decoded)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Expired token", "type_error": "invalid"}), 422

        except jwt.DecodeError:
            return jsonify({"error": "Invalid Token", "type_error": "expired"}), 422

    return wrapper


class User(db.Model):
    id: Mapped[str] = mapped_column(String(300), primary_key=True)
    user: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=True)
    cart = mapped_column(JSON)


with app.app_context():
    db.create_all()


@app.route("/products/<string:id>")
def fetchProductsId(id):
    selected_product = list(filter(lambda x: x["id"] == id, products))
    if selected_product:
        return jsonify(selected_product), 200
    else:
        return jsonify({"error": "product not found"}), 404


@app.route("/")
@app.route("/products")
def fetchProducts():
    return jsonify(products)


@app.route("/users/createnewuser", methods=["POST"])
def createNewUser():
    dados = request.get_json()
    if not dados or "user" not in dados or "password" not in dados:
        return jsonify({"error": "O valor não preenche todos os dados"}), 401
    if len(dados["user"]) > 100 or len(dados["password"]) > 100:
        return jsonify({"error": "many characters", "manyCharacters": True}), 200

    hasRepeated = User.query.filter(User.user == dados["user"]).first()
    if not hasRepeated is None:
        return jsonify({"error": "repeat usernames", "hasRepeated": True}), 200
    userId = uuid.uuid4().hex
    new_password = generate_password_hash(dados["password"])
    acess_token = create_access_token(identity=userId)
    new_user = User(
        user=dados["user"],  # type:ignore
        password=new_password,  # type:ignore
        id=userId,  # type:ignore
        cart=[],  # type:ignore
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"user": dados["user"], "cart": [], "acess_token": acess_token})
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "many characters", "manyCharacters": True}), 200
    except DataError as e:
        db.session.rollback()
        return jsonify({"error": "many characters", "manyCharacters": True}), 200
    except Exception as e:
        db.session.rollback()

        return jsonify({"error": str(e)}), 400


@app.route("/users/me", methods=["GET"])
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


@app.route("/users/login", methods=["POST"])
def loginUser():
    try:
        username = request.get_json()["username"]
        password = request.get_json()["password"]
        selectedUser = User.query.filter(username == User.user).first()
        if selectedUser is None or not check_password_hash(
            selectedUser.password, password
        ):
            return jsonify({"auth": False, "message": "Usuário não encontrado"}), 200
        acess_token = create_access_token(selectedUser.id)
        return jsonify(
            {
                "auth": True,
                "acess_token": acess_token,
                "user": selectedUser.user,
                "cart": selectedUser.cart,
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/users/cart", methods=["GET", "POST", "DELETE"])  # type: ignore
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


@app.route("/users/clearCart", methods=["DELETE"])
@required_authentication
def clearCart(id):
    try:
        id = get_jwt_identity()
        selectedUser = User.query.get_or_404(id)
        selectedUser.cart = []
        db.session.commit()
        return jsonify({"cart": selectedUser.cart, "status": "clean"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
