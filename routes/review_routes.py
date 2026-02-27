from fastapi import APIRouter, Form, File, UploadFile
from models.reviews import Reviews
from .deps.db_session import SessionDep
from sqlmodel import select
import os, shutil
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])

@reviews_router.get('/get_all')
def get_reviews(db:SessionDep):
    query = select(Reviews)
    reviews = db.exec(query).all()
    return reviews


import os
import shutil
from fastapi import UploadFile


@reviews_router.post("/create_review")
def create_review(db: SessionDep,
                  comment: str = Form(...),
                  username: str = Form(...),
                  product_img: UploadFile = File(...),
                  calification: int = Form(...)
                  ):
    # ✅ CORRECCIÓN: Usar ruta relativa (sin el slash inicial)
    upload_dir = "static/reviews/"

    # Crear carpeta si no existe (en la raíz del proyecto)
    os.makedirs(upload_dir, exist_ok=True)

    # Generar nombre único para evitar conflictos
    import uuid
    file_extension = os.path.splitext(product_img.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"

    # Ruta completa del archivo
    file_path = os.path.join(upload_dir, unique_filename)

    # Guardar archivo físico
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(product_img.file, buffer)

    # Ruta para guardar en BD (con / al inicio para la URL)
    db_image_path = f"/static/reviews/{unique_filename}"

    review = Reviews(
        comment=comment,
        username=username,
        product_img=db_image_path,  # Guardamos la ruta con /static/
        calification=calification
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    return review