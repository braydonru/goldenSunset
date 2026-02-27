from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlmodel import Session, select
from models.color import Color
from routes.deps.db_session import SessionDep
from typing import List, Optional, Annotated
from config.security import require_role
import os, shutil
color_router = APIRouter(prefix="/colors", tags=["colors"])


@color_router.get("/")
def get_colors_all(db: SessionDep,):
    query = select(Color)
    colors = db.exec(query).all()
    return colors
@color_router.get("/enable")
def get_colors_enable(db: SessionDep,):
    query = select(Color).filter(Color.enable==True)
    colors = db.exec(query).all()
    return colors

@color_router.get("/{color_id}")
def get_color(color_id: int, db: SessionDep):
    color = db.get(Color, color_id)
    if not color:
        raise HTTPException(404, "Color not found")
    return color

@color_router.post("/")
def create_color(
    db: SessionDep,
    color_name: str = Form(...),
    color_code: str = Form(...),
    variant:str = Form(...),
    front_image: UploadFile = File(...),
    back_image: UploadFile = File(...),

):

    folder = "static/img/pullovers"
    os.makedirs(folder, exist_ok=True)

    normalized = color_name.lower().replace(" ", "_")

    front_filename = f"{normalized}_front.png"
    back_filename = f"{normalized}_back.png"

    front_path = f"/static/img/pullovers/{front_filename}"
    back_path = f"/static/img/pullovers/{back_filename}"

    with open(f"{folder}/{front_filename}", "wb") as buffer:
        shutil.copyfileobj(front_image.file, buffer)

    with open(f"{folder}/{back_filename}", "wb") as buffer:
        shutil.copyfileobj(back_image.file, buffer)

    new_color = Color(
        color_name=color_name,
        color_code=color_code,
        variant=variant,
        front_image_path=front_path,
        back_image_path=back_path
    )

    db.add(new_color)
    db.commit()
    db.refresh(new_color)

    return new_color
@color_router.put("/disable_color")
def disable_color(db: SessionDep,id):
    db_color = db.get(Color, id)
    if not db_color:
        raise HTTPException(404, "Color not found")
    db_color.enable = False
    db.commit()
    db.refresh(db_color)
    return "Color has been disabled"

@color_router.put("/enable_color")
def enable_color(db: SessionDep,id):
    db_color = db.get(Color, id)
    if not db_color:
        raise HTTPException(404, "Color not found")
    db_color.enable = True
    db.commit()
    db.refresh(db_color)
    return "Color has been enabled"


@color_router.get("/by_variant/{variant}")
def get_colors_by_variant(db: SessionDep, variant: str):
    response = select(Color).where(Color.variant == variant, Color.enable == True)
    colors = db.exec(response).all()
    return colors