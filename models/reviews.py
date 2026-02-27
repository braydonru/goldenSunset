from sqlmodel import SQLModel, Field
from typing import Optional

from starlette.datastructures import UploadFile


class Reviews(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    comment: str
    username:str
    product_img:Optional[str] = None
    calification:int