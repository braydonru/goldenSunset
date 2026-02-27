from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    name: str = Field()
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    password: str = Field()


class UserCreateIn(UserBase):...

class UserCreateOut(SQLModel):
    name: str = Field()
    username: str = Field()
    email: str = Field()
    password: str = Field()

class User(UserBase, table=True):
    id: int = Field(primary_key=True)
    is_superuser: bool = Field(default=False)