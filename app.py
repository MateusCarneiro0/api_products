from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, JSON, Float, select
from sqlalchemy.exc import IntegrityError, DataError
import uuid
import os
from flask_cors import CORS
from authentication import create_access_token, required_authentication, refresh_route

uri = os.getenv("DATABASE_URL", "sqlite:///users.db")

app = Flask(__name__)


CORS(app)

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


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
            "nome":self.nome,
            "id":self.id,
            "link":self.link,
            "imagem":self.imagem,
            "alias":self.alias,
            "categoria":self.categoria,
            "categorias":self.categorias,
            "descricao":self.descricao,
            "preco":self.preco
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
    acess_token,refresh_token = create_access_token(identify=userId)
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
        return jsonify(
            {
                "user": dados["user"],
                "cart": [],
                "acess_token": acess_token,
                "refresh_token": refresh_token,
            }
        )
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "many characters", "manyCharacters": True,"details":str(e)}), 200
    except DataError as e:
        db.session.rollback()
        return jsonify({"error": "many characters", "manyCharacters": True,"details":str(e)}), 200
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
        
        acess_token,refresh_token = create_access_token(selectedUser.id)
        return jsonify(
            {
                "auth": True,
                "acess_token": acess_token,
                "user": selectedUser.user,
                "cart": selectedUser.cart,
                "refresh_token":refresh_token
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
    return jsonify({"acess_token": acess_token, "refresh_token": refresh_token})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
