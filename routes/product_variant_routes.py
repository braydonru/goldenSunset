from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from models.product_variant import Product_Variant
from models.category import Category
from .deps.db_session import SessionDep
from sqlmodel import select
import os, shutil


product_variant_router = APIRouter(tags=["Product Variant"],prefix="/product_variant")


@product_variant_router.get('/')
def get_variants_all(db:SessionDep):
    response = select(Product_Variant)
    variants = db.exec(response).all()
    return variants

@product_variant_router.get('/enable')
def get_variants_enable(db:SessionDep):
    response = select(Product_Variant).filter(Product_Variant.enable == True)
    variants = db.exec(response).all()
    return variants

@product_variant_router.get('/by_category')
def get_variants_by_category(db:SessionDep,category:str):
    response = select(Product_Variant).filter(Product_Variant.category_name == category,Product_Variant.enable == True)
    variants = db.exec(response).all()
    return variants

@product_variant_router.post('/create')
def create_product_variant(db:SessionDep,
                           name:str=Form(...),
                           category_id: int =Form(...),
                           image_url: UploadFile=File(...)
                           ):

    os.makedirs("static/variants/", exist_ok=True)
    ruta_imagen = f"static/variants/{image_url.filename}"

    with open(ruta_imagen, "wb") as buffer:
        shutil.copyfileobj(image_url.file, buffer)

    response= select(Category).filter(Category.id == category_id)
    category_name = db.exec(response).one().name

    product_variant = Product_Variant(
        name=name,
        category_id=category_id,
        category_name=category_name,
        image_url=ruta_imagen
    )

    db.add(product_variant)
    db.commit()
    db.refresh(product_variant)
    return product_variant

@product_variant_router.put('/disable/{id}')
def disable_product_variant(db:SessionDep,id):
    variant = db.get(Product_Variant, id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    variant.enable = False
    db.commit()
    db.refresh(variant)
    return variant

@product_variant_router.put('/enable/{id}')
def disable_product_variant(db:SessionDep,id):
    variant = db.get(Product_Variant, id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    variant.enable = True
    db.commit()
    db.refresh(variant)
    return variant


