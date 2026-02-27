from fastapi import APIRouter,Depends, HTTPException
from passlib.context import CryptContext
from sqlmodel import select, Session
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import jwt
from routes.deps.db_session import SessionDep, get_db
from passlib.context import CryptContext
from typing import Annotated
from dotenv import load_dotenv
from models.user import User
import os
load_dotenv()

security = APIRouter()
oauth2 = OAuth2PasswordBearer(tokenUrl='token')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def encode_token(payload: dict) -> str:
    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
    return token


def decode_token(token: Annotated[str, Depends(oauth2)], session: Annotated[Session, Depends(get_db)]) -> dict:
    data = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
    user_db = select(User).where(User.username == data['username'])
    result = session.exec(user_db).first()
    return {'username': result.username, 'is_superuser': result.is_superuser, 'id': result.id}


@security.post('/token')
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Session = Depends(get_db)):
    user_db = select(User).where(User.username == form_data.username)
    result = session.exec(user_db).first()

    if not result:
        raise HTTPException(status_code=404, detail="user doesn't exist")

    if not verify_password(form_data.password, result.password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    token = encode_token({'username': result.username, 'superuser': result.is_superuser, 'id': result.id})

    return {'access_token': token,'username':result.username,'superuser':result.is_superuser,'id':result.id}


@security.get('/login/profile')
def profile(my_user: Annotated[dict, Depends(decode_token)]):
    return my_user


def require_role(required_role: str):
    def role_checker(user: Annotated[dict, Depends(decode_token)]):
        if user['is_superuser'] is not True:
            raise HTTPException(status_code=403, detail=f'This operation require a superuser')
        return user
    return role_checker