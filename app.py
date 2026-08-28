from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, JSON, Float, select
import uuid
import os
from flask_cors import CORS
from authentication import create_access_token, required_authentication, refresh_route
from dotenv import load_dotenv
from redis_manager import put_in_redis
from utils.jwt_utils import decode_jwt
from utils.datetime_utils import calculate_seconds_of_now_future_date

load_dotenv()

uri = os.getenv("DATABASE_URL", "sqlite:///users.db")
client_site = os.getenv("CLIENT_SITE", "localhost:3000")
app = Flask(__name__)


CORS(app, origins=["http://localhost:5173", client_site], supports_credentials=True)

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

is_dev = os.getenv("DEV", "true") == "true"


class User(db.Model):
    id: Mapped[str] = mapped_column(String(300), primary_key=True)
    user: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    password: Mapped[str] = mapped_column(String(300), nullable=True)
    cart = mapped_column(JSON)


class Product(db.Model):
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    descricao: Mapped[str] = mapped_column(String(250), nullable=False)
    imagem: Mapped[str] = mapped_column(String(900), nullable=True)
    categorias = mapped_column(JSON)
    link: Mapped[str] = mapped_column(String(80), nullable=True)
    preco: Mapped[float] = mapped_column(Float, nullable=False)
    categoria: Mapped[str] = mapped_column(String(2), nullable=False)
    alias: Mapped[str] = mapped_column(String(50), nullable=True)

    def to_dict(self):
        product = {
            "nome": self.nome,
            "id": self.id,
            "link": self.link,
            "imagem": self.imagem,
            "alias": self.alias,
            "categoria": self.categoria,
            "categorias": self.categorias,
            "descricao": self.descricao,
            "preco": self.preco,
        }
        return product


with app.app_context():
    db.create_all()


@app.route("/products/<string:id>")
def fetchProductsId(id):
    product = Product.query.get_or_404(id)
    if not product == None:
        return jsonify(product.to_dict()), 200
    else:
        return jsonify({"error": "product not found"}), 404


@app.route("/")
@app.route("/products")
def fetchProducts():
    selected_products = select(Product).limit(50)
    raw_products = db.session.scalars(selected_products).all()
    products = [product.to_dict() for product in raw_products]
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
    acess_token, refresh_token = create_access_token(identify=userId)
    new_user = User(
        user=dados["user"],  # type:ignore
        password=new_password,  # type:ignore
        id=userId,  # type:ignore
        cart=[],  # type:ignore
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        response = make_response(
            jsonify(
                {
                    "user": dados["user"],
                    "cart": [],
                }
            ),
            201,
        )
        response.set_cookie(
            key="acess_token",
            value=acess_token,
            max_age=3600,
            secure=not is_dev,
            httponly=True,
            samesite="None",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=3600 * 24 * 7,
            secure=not is_dev,
            httponly=True,
            samesite="None",
        )

        response.set_cookie(
            key="is_logged",
            value="true",
            max_age=3600 * 24 * 7,
            secure=not is_dev,
            httponly=False,
            samesite="None",
        )

        return response

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

        acess_token, refresh_token = create_access_token(selectedUser.id)
        response = make_response(
            jsonify(
                {
                    "auth": True,
                    "user": selectedUser.user,
                    "cart": selectedUser.cart,
                }
            ),
            201,
        )
        response.set_cookie(
            key="acess_token",
            value=acess_token,
            max_age=3600,
            secure=not is_dev,
            httponly=True,
            samesite="None",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=3600 * 24 * 7,
            secure=not is_dev,
            httponly=True,
            samesite="None",
        )
        response.set_cookie(
            key="is_logged",
            value="true",
            max_age=3600 * 24 * 7,
            secure=not is_dev,
            httponly=False,
            samesite="None",
        )
        return response
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
        selectedUser = User.query.get_or_404(id)
        selectedUser.cart = []
        db.session.commit()
        return jsonify({"cart": selectedUser.cart, "status": "clean"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/refresh", methods=["POST"])
@refresh_route
def refresh(identify):
    acess_token, refresh_token = create_access_token(identify=identify)
    response = make_response(jsonify({"status": "refreshed"}))

    response.set_cookie(
        key="acess_token",
        value=acess_token,
        max_age=3600,
        httponly=True,
        samesite="None",
        secure=not is_dev,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=3600 * 24 * 7,
        httponly=True,
        samesite="None",
        secure=not is_dev,
    )
    response.set_cookie(
        key="is_logged",
        value="true",
        max_age=3600 * 24 * 7,
        secure=not is_dev,
        httponly=False,
        samesite="None",
    )
    return response


@app.route("/users/logout", methods=["DELETE"])
@required_authentication
def logout():
    tokens = request.get_json()
    if not tokens or not "acess_token" in tokens or not "refresh_token" in tokens:
        return jsonify(
            {
                "error": "É preciso de acess_token e refresh token",
                "type_error": "Insuficient",
            }
        )
    try:
        acess_token_payload = decode_jwt(tokens["acess_token"])
        expire_time_acess_token = calculate_seconds_of_now_future_date(
            acess_token_payload["exp"]
        )
        expire_time_refresh_token = calculate_seconds_of_now_future_date(
            decode_jwt(tokens["refresh_token"], "exp")  # type:ignore
        )

        put_in_redis(
            tokens["acess_token"],
            time=expire_time_acess_token,
            id=acess_token_payload["identify"],
        )
        put_in_redis(
            tokens["refresh_token"],
            time=expire_time_refresh_token,
            id=acess_token_payload["identify"],
        )
        return jsonify({"status": "correct"}), 200
    except Exception as err:
        return jsonify({"status": "error", "details": str(err)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
