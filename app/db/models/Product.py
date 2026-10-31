from .. import db
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import String,JSON,Float

class Product(db.Model):
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    descricao: Mapped[str] = mapped_column(String(250), nullable=False)
    imagem: Mapped[str] = mapped_column(String(900), nullable=True)
    categorias = mapped_column(JSON)
    link: Mapped[str] = mapped_column(String(150), nullable=True)
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