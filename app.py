from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from products import products
import uuid
import os

app = Flask(__name__)
uri = os.getenv("DATABASE_URL","sqlite:///users.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.String(30), primary_key=True)
    user = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(500), nullable=True)
    cart = db.Column(db.JSON)
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
    hasRepeated = User.query.filter(User.user == dados["user"]).first()
    if not hasRepeated is None:
        return jsonify({"error": "repeat usernames"}), 200
    userId = uuid.uuid4().hex
    new_password = generate_password_hash(dados["password"])
    new_user = User(
        user=dados["user"],
        password=new_password,
        id=userId,
        cart=[],
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"user": dados["user"], "id": userId})
    except Exception as e:
        db.session.rollback()

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
        return jsonify({"auth": True, "id": selectedUser.id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/users/<string:id>/cart", methods=["GET"])
def fetchCart(id):
    selectedUser = User.query.get_or_404(id)
    if selectedUser is None:
        return jsonify({"error": "Not found id"}), 404
    try:
        cart = selectedUser.cart
        return jsonify(cart), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/users/<string:id>/addproductcart", methods=["POST"])
def addInCart(id):
    try:
        product = request.get_json()

        # 1. Certifique-se de usar o nome correto da classe (Usuario) e passe o id direto
        selectedUser = User.query.get_or_404(id)

        # 2. Pega o carrinho atual ou cria uma lista vazia novinha
        cart = list(selectedUser.cart) if selectedUser.cart is not None else []

        # 3. CORREÇÃO: Apenas faça o append. Não jogue o resultado em outra variável!
        cart.append(product)

        # 4. Devolve a lista 'cart' modificada para o atributo do usuário
        selectedUser.cart = cart

        db.session.commit()
        return jsonify({"cart":selectedUser.cart}), 200
    except Exception as e:
        db.session.rollback()  # Boa prática: desfaz a tentativa se der erro
        return jsonify({"error": str(e)}), 500


@app.route("/users/<string:id>/removeProductCart/<string:product_id>", methods=["POST"])
def removeInCart(id,product_id):
    try:
        selectedUser = User.query.get_or_404(ident=id)
        cart = list(selectedUser.cart) if selectedUser.cart is not None else []
        cart = (
            list(filter(lambda product: product["id"] != product_id, cart))
            if selectedUser.cart is not None
            else [])
        selectedUser.cart = cart
        db.session.commit()
        return jsonify({"cart":selectedUser.cart})
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/users/<string:id>/clearCart", methods=["POST"])
def clearCart(id):
    try:
        selectedUser = User.query.get_or_404(id)
        selectedUser.cart = []
        db.session.commit()
        return jsonify({"cart": selectedUser.cart}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
