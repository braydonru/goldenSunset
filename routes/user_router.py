from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from config.security import hash_password
from routes.deps.db_session import SessionDep
from models.user import User,UserCreateIn, UserCreateOut

user_router = APIRouter(prefix='/Login', tags=['Login'])

@user_router.post('/register')
def register(db:SessionDep,
             name: str = Form(...),
             username: str = Form(...),
             email: str = Form(...),
             password: str = Form(...)):
    hashed_password = hash_password(password)

    user_db=User(name=name
                 ,username=username
                 ,email=email
                 ,password=hashed_password)
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return "user registered successfully"
