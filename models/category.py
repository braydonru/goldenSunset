from sqlmodel import SQLModel, Field

class CategoryBase(SQLModel):
    name: str = Field()
    enable: bool = Field(default=True)

class CategoryCreateIn(CategoryBase):...

class CategoryCreateOut(SQLModel):
    id: int=Field()

class Category(CategoryBase, table=True):
    id: int = Field(primary_key=True)
