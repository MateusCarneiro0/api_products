<<<<<<< HEAD
from app import app, db

with app.app_context():
    db.create_all()
print("Banco de dados criado")
=======
from app import app,db

with app.app_context():
    db.create_all()
>>>>>>> 1b7bf03 (Creating datetime_utils and creating refresh tokens)
