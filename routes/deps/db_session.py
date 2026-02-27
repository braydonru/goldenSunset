# routes/deps/db_session.py
from typing import Annotated, Generator
from fastapi import Depends
from sqlmodel import Session
from config.db import engine

def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesiones de base de datos
    Se asegura de cerrar la sesión después de cada request
    """
    with Session(engine) as session:
        yield session

# SessionDep es un tipo que puedes usar en tus endpoints
SessionDep = Annotated[Session, Depends(get_db)]