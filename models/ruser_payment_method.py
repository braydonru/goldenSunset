from sqlmodel import SQLModel, Field
from typing import Optional

class User_payment_method(SQLModel, table=True):
    id:Optional[int] = Field(default=None,primary_key=True)
    user_id:int = Field(default=None)
    payment_method_id:int = Field(default=None)