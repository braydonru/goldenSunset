from fastapi import APIRouter, HTTPException, Depends, Form
from sqlmodel import select
from models.category import Category,CategoryCreateIn
from routes.deps.db_session import SessionDep
from typing import Annotated
from config.security import require_role

from models.producto import Product

category_router = APIRouter(prefix="/category",tags=["category"])

@category_router.get("/")
def get_categories_all(db:SessionDep):
    statement = select(Category)
    categories = db.exec(statement).all()
    return categories
@category_router.get("/enable")
def get_categories_enable(db:SessionDep):
    statement = select(Category).filter(Category.enable == True)
    categories = db.exec(statement).all()
    return categories

@category_router.post("/create")
def create_category(db:SessionDep,
                    user:Annotated[str,Depends(require_role('True'))],
                    name:str = Form(...),

                    ):
    category_db = Category(name=name)
    db.add(category_db)
    db.commit()
    db.add(category_db)
    db.commit()
    db.refresh(category_db)
    return category_db

@category_router.put("/update/{id}", )
def update_category(db:SessionDep,id:int,category:CategoryCreateIn, user:Annotated[str,Depends(require_role('True'))]):
    category_db = db.get(Category,id)
    if not category_db:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category:
        setattr(category_db, key, value)
    db.commit()
    db.refresh(category_db)
    return category_db

@category_router.put("/disable/{id}")
def disable_category(db:SessionDep,id:int, user:Annotated[str,Depends(require_role('True'))]):
    category_db = db.get(Category,id)
    if not category_db:
        raise HTTPException(status_code=404, detail="Category not found")
    if not category_db.enable:
        raise HTTPException(status_code=404, detail="Category already disabled")
    category_db.enable = False
    products_by_category=db.query(Product).filter(Product.category_id == id)
    for product in products_by_category:
        product.enable = False
    db.commit()
    return {"message":"Category disabled"}

@category_router.put("/enable/{id}")
def enable_category(db:SessionDep,id:int, user:Annotated[str,Depends(require_role('True'))]):
    category_db = db.get(Category,id)
    if not category_db:
        raise HTTPException(status_code=404, detail="Category not found")
    if category_db.enable:
        raise HTTPException(status_code=404, detail="Category already enable")
    category_db.enable = True
    products_by_category=db.query(Product).filter(Product.category_id == id)
    for product in products_by_category:
        product.enable = True
    db.commit()
    return {"message":"Category enabled successfully"}