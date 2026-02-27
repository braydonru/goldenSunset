from sqlmodel import SQLModel, Field
from typing import Optional

class Design(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    img:Optional[str]=None
    enable: Optional[bool]= Field(default=True)
