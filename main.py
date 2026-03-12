from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel
from starlette.staticfiles import StaticFiles
import os

from routes.design_router import design_router
from routes.review_routes import reviews_router
from routes.product_variant_routes import product_variant_router
from routes.color_routes import color_router
from config.security import security
from routes.category_router import category_router
from config.db import engine
from models import *
from routes.product_router import product_router
from routes.user_router import user_router
from routes.order_routes import order_router
from routes.stripe_routes import stripe_router
from fastapi.middleware.cors import CORSMiddleware
from config.db import engine, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja eventos de inicio y cierre
    """
    # Startup: crear tablas
    print("🚀 Iniciando aplicación...")
    create_tables()
    print("✅ Base de datos lista!")

    yield

    # Shutdown
    print("👋 Cerrando aplicación...")

SQLModel.metadata.create_all(engine)

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.title='Golden Sunset'
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
                   "http://localhost:3000",
                   "https://https://golden-sunset-front-q5udvwbzl-braydonru1234-2254s-projects.vercel.app",
                  ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/", tags=['Home'])
def Home():
    return (f'Hola mundo')



app.include_router(product_router)
app.include_router(category_router)
app.include_router(user_router)
app.include_router(order_router)
app.include_router(security)
app.include_router(color_router)

app.include_router(product_variant_router)

app.include_router(reviews_router)

app.include_router(design_router)

app.include_router(stripe_router)
