from .. import db
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON

class User(db.Model):
    id: Mapped[str] = mapped_column(String(300), primary_key=True)
    user: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    password: Mapped[str] = mapped_column(String(300), nullable=True)
    cart = mapped_column(JSON)