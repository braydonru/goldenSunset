from sqlmodel import SQLModel, Field
from typing import Optional
from .product_variant import Product_Variant

class Color(SQLModel, table=True):
    __tablename__ = "color"
    id: Optional[int] = Field(default=None, primary_key=True)
    color_name: str  # Black, White, Red
    color_code: str
    enable: Optional[bool] = Field(default=True)
    variant: str
    front_image_path: Optional[str] = None
    back_image_path: Optional[str] = None
