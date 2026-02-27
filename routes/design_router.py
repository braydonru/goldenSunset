from http.client import HTTPException

from fastapi import APIRouter, Form, UploadFile, File
from models.designs import Design
from .deps.db_session import SessionDep
import os, shutil
from sqlmodel import select

design_router = APIRouter(prefix="/design", tags=["Design"])


@design_router.get("/get_all_designs")
def get_all_designs(db:SessionDep):
    response = select(Design)
    designs = db.exec(response).all()
    return designs

@design_router.get("/get_enable_design")
def get_enabled_designs(db:SessionDep):
    response = select(Design).filter(Design.enable == True)
    designs = db.exec(response).all()
    return designs

@design_router.post("/create_design")
def create_design(db:SessionDep,
                  name:str=Form(...),
                  category:str=Form(...),
                  img:UploadFile=File(...),
                  ):


    os.makedirs("static/designs", exist_ok=True)

    ruta_imagen = f"static/designs/{img.filename}"

    with open(ruta_imagen, "wb") as buffer:
        shutil.copyfileobj(img.file, buffer)

    design = Design(
        name=name,
        category=category,
        img=ruta_imagen
    )

    db.add(design)
    db.commit()
    db.refresh(design)
    return design


@design_router.put("/disable_design/{id}")
def disable_design(db:SessionDep,id):
    design = db.get(Design, id)
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")

    design.enable = False
    db.commit()
    db.refresh(design)
    return design


@design_router.put("/enable_design/{id}")
def enable_design(db: SessionDep, id):
    design = db.get(Design, id)
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")

    design.enable = True
    db.commit()
    db.refresh(design)
    return design