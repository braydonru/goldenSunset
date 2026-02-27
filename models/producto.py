from sqlmodel import SQLModel, Field
from .category import Category
from typing import Optional

class ProductBase(SQLModel):
    nombre: str = Field()
    descripcion: str = Field()
    price: float = Field()
    img_url: Optional[str] = None
    category_id: int = Field(foreign_key='category.id')
    type:str = Field()
    enable:bool = Field(default=True)


class ProductoCreateIn(ProductBase):...

class ProductoCreateOut(SQLModel):
    id:int = Field()

class Product(ProductBase, table=True):
    id: int = Field(primary_key=True)
