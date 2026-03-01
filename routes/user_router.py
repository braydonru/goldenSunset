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


@user_router.get('/users')
def get_users(db:SessionDep):
    response = select(User)
    users = db.exec(response).all()
    return users

@user_router.get('/users/{username}')
def get_user(db:SessionDep,username: str):
    user = db.query(User).filter(User.username==username).first()
    if not user:
        raise HTTPException(status_code=404,detail='User not found',)
    return user

@user_router.put('/users/{id}')
def update_user(db:SessionDep,id:int):
    user = db.get(User,id)
    if not user:
        raise HTTPException(status_code=404,detail='User not found')
    user.is_superuser = True
    db.commit()
    db.refresh(user)
    return user