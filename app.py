from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from products import products

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Usuario(db.Model):
    id = db.Column(db.String(30), primary_key=True)
    user = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(500), nullable=True)
    cart = db.Column(db.JSON)


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/products/<string:id>")
def fetchProductsId(id):

    return jsonify(list(filter(lambda x: x["id"] == id, products)))


@app.route("/products")
def fetchProducts():
    return jsonify(products)


@app.route("/users/createnewuser", methods=["POST"])
def createNewUser():
    dados = request.get_json()
    if (
        not dados
        or "user" not in dados
        or "password" not in dados
        or "id" not in dados
    ):
        return jsonify({"error": "O valor não preenche todos os dados"})
    senha = generate_password_hash(dados["password"])
    new_user = Usuario(
        user=dados["user"],
        password=senha,
        id=dados["id"],
        cart=[],
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"user": dados["user"], "id": dados["id"]})
    except Exception as e:

        db.session.rollback()
        
        return jsonify({"error":str(e)})


@app.route("/users/cart/<string:id>")
def fetchUsers():

    return db.session.get()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
