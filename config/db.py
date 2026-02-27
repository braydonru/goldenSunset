# config/db.py
from sqlmodel import create_engine
from pathlib import Path

# Crear directorio database si no existe
Path("database").mkdir(exist_ok=True)

# SQLite creará el archivo automáticamente
engine = create_engine(
    "sqlite:///database/app.db",
    connect_args={"check_same_thread": False},
    echo=True  # Muestra las consultas SQL en consola
)

def create_tables():
    """Crea todas las tablas definidas en los modelos"""
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    print("✅ Tablas creadas/verificadas en database/app.db")