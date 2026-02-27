from sqlmodel import SQLModel, Field
from typing import Optional
from .category import Category

class Product_Variant(SQLModel, table=True):
    id:Optional[int] = Field(primary_key=True)
    name:str = Field()
    category_id:int = Field(foreign_key='category.id')
    category_name:Optional[str] = Field(default='')
    image_url:Optional[str] = None
    enable:bool = Field(default=True)