from fastapi import APIRouter, HTTPException, Form, File,UploadFile, Depends
from models.producto import Product, ProductoCreateIn, ProductoCreateOut
from models.category import Category
from routes.deps.db_session import SessionDep
from typing import Annotated
from sqlmodel import select
import os, shutil
from config.security import require_role


product_router = APIRouter(prefix="/product", tags=["product"])


@product_router.get("/enable")
def get_product(db:SessionDep)->list[Product]:
    statement=select(Product).filter(Product.enable==True)
    products=db.exec(statement).all()
    return products

@product_router.get("/")
def get_product_all(db:SessionDep)->list[Product]:
    statement=select(Product)
    products=db.exec(statement).all()
    return products


@product_router.post("/create")
def create_product(db:SessionDep,
                   nombre: str = Form(...),
                   descripcion: str = Form(...),
                   price: float = Form(...),
                   img_url: UploadFile = File(...),
                   category:int = Form(...),


                   #user:Annotated[str,Depends(require_role('True'))]
                   ):
    # crear carpeta si no existe
    os.makedirs("static/", exist_ok=True)
    # ruta donde se guardará
    ruta_imagen = f"static/{img_url.filename}"
    # guardar archivo físico
    with open(ruta_imagen, "wb") as buffer:
        shutil.copyfileobj(img_url.file, buffer)

        categoria = db.get(Category,category)
        tipo=categoria.name
    # guardar SOLO el path relativo en la BD
    producto = Product(
        nombre=nombre,
        descripcion=descripcion,
        price=price,
        img_url=f"/static/{img_url.filename}",
        category_id=category,
        type=tipo
    )

    db.add(producto)
    db.commit()
    db.refresh(producto)

    return producto

@product_router.put("/update/{id}")
def update_product(db:SessionDep,id:int,product:ProductoCreateIn, user:Annotated[str,Depends(require_role('True'))])->Product:
    product_db=db.get(Product,id)
    if not product_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for key, value in product:
        setattr(product_db, key, value)
    db.commit()
    db.refresh(product_db)
    return product_db

@product_router.delete("/delete/{id}")
def delete_product(db:SessionDep,id:int, user:Annotated[str,Depends(require_role('True'))]):
    product_db=db.get(Product,id)
    if not product_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product_db.enable=False
    db.commit()
    return None

@product_router.put("/activate/{id}")
def activate_product(db:SessionDep,id:int,user:Annotated[str,Depends(require_role('True'))]):
    product_db=db.get(Product,id)
    if not product_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if product_db.enable:
        raise HTTPException(status_code=409, detail="Product already activated")
    product_db.enable=True
    db.commit()
    return None