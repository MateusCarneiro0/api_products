from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
from products import products
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
class Usuarios(db.Model):
    id = db.Column(db.Integer,primary_key =  True)
    user = db.Column(db.Integer,nullable = True)
@app.route("/")
def index():
    return "Hello, World!"

@app.route("/products/<string:id>")
def fetchProductsId(id):
    if id:
        return jsonify(list(filter(lambda x: x["id"] == id, products)))
    else:
        return jsonify(products)
@app.route("/products")
def fetchProducts():
    return jsonify(products)
    
if (__name__ == "__main__"):
    app.run(debug=True)