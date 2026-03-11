from fastapi import HTTPException, APIRouter, UploadFile, Form, File, Depends
from models.order import Order, OrderCreateIn
from models.user import User
from routes.deps.db_session import SessionDep
from sqlmodel import select
from config.order_utils import date_formater,query_email
from typing import Optional, Annotated
import os, shutil

from config.security import require_role

order_router = APIRouter(prefix="/order", tags=["order"])

#para obtener las ordenes q ya se pagaron
@order_router.get("/order")
def get_orders(db: SessionDep):
    # Hacer join con la tabla User
    statement = (
        select(
            Order.id,
            Order.size,
            Order.color,
            Order.type,
            Order.client_img,
            Order.preview_img,
            Order.specification,
            Order.date,
            User.email.label("user_email")  # Obtener el email del usuario
        ).filter(Order.state == True)
        .join(User, Order.user == User.id)  # Hacer join con la tabla User
        .order_by(Order.date.asc())
    )

    orderst = db.exec(statement).all()

    # Convertir a lista de diccionarios
    orders = []
    for order in orderst:
        order_dict = {
            "id": order.id,
            "size": order.size,
            "color": order.color,
            "type": order.type,
            "client_img": order.client_img,
            "preview_img": order.preview_img,
            "date": order.date,
            "owner": order.user_email
        }
        orders.append(order_dict)

    return orders

#para obtener las ordenes que estan por pagar por usuario
@order_router.get("/order_by_user/{id}")
def get_order_by_user(db: SessionDep, id:int):
    response = select(Order).filter(Order.user == id, Order.state == False)
    orders = db.exec(response).all()
    return orders

@order_router.post("/create")
def create_order(
        db: SessionDep,
        user: int = Form(...),
        size: Optional[str] = Form(None),
        color: Optional[str] = Form(None),
        type: Optional[str] = Form(None),
        specification: Optional[str] = Form(None),
        font: Optional[str] = Form(None),
        client_img: Optional[UploadFile] = File(None),
        preview_img: Optional[UploadFile] = File(None),
        client_img_back: Optional[UploadFile] = File(None),
        preview_img_back: Optional[UploadFile] = File(None),
        variation: Optional[str] = Form(None),
        qantity: Optional[int] = Form(None),
        price: Optional[float] = Form(None),
):
    import os
    import shutil
    import uuid
    from fastapi import HTTPException


    user_exists = db.query(User).filter(User.id == user).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Crear directorio
    os.makedirs("static/orders", exist_ok=True)

    # Inicializar datos de la orden
    order_data = {
        "user": user,
        "size": size,
        "color": color,
        "type": type or "Pullover",
        "specification": specification,
        "font": font,
        "variation":variation,
        "qantity": qantity,
        "price": price
    }

    saved_files = []  # Para tracking y rollback en caso de error

    # Función mejorada para guardar archivos
    def save_file_with_rollback(upload_file: UploadFile, prefix: str, side: str):
        if not upload_file:
            return None

        if not upload_file.filename or upload_file.filename == "":
            return None

        try:
            # Validar tipo de archivo
            if not upload_file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"{prefix} must be an image file"
                )

            # Generar nombre único con prefijo que identifique el lado
            original_filename = upload_file.filename
            file_ext = os.path.splitext(original_filename)[1]
            if not file_ext:
                file_ext = ".png"

            # Usar prefijo más descriptivo
            unique_filename = f"{side}_{prefix}_{uuid.uuid4().hex}{file_ext}"
            file_path = f"static/orders/{unique_filename}"

            print(f"💾 {side} - {prefix}: Guardando como {unique_filename}")

            # Guardar archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            # Agregar a la lista para posible rollback
            saved_files.append(file_path)

            return f"/static/orders/{unique_filename}"

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error guardando {side} - {prefix}: {e}")
            return None

    # PROCESAR DISEÑO FRONTAL
    front_has_design = False
    front_files_saved = []

    if client_img and client_img.filename:
        print("🔄 Procesando client_img (front)...")
        client_img_path = save_file_with_rollback(client_img, "client", "front")
        if client_img_path:
            order_data["client_img"] = client_img_path
            front_has_design = True
            front_files_saved.append("client_img")
            print(f"✅ client_img guardado: {client_img_path}")

    if preview_img and preview_img.filename:
        print("🔄 Procesando preview_img (front)...")
        preview_img_path = save_file_with_rollback(preview_img, "preview", "front")
        if preview_img_path:
            order_data["preview_img"] = preview_img_path
            front_has_design = True
            front_files_saved.append("preview_img")
            print(f"✅ preview_img guardado: {preview_img_path}")

    # PROCESAR DISEÑO TRASERO
    back_has_design = False
    back_files_saved = []

    if client_img_back and client_img_back.filename:
        print("🔄 Procesando client_img_back (back)...")
        client_img_back_path = save_file_with_rollback(client_img_back, "client", "back")
        if client_img_back_path:
            order_data["client_img_back"] = client_img_back_path
            back_has_design = True
            back_files_saved.append("client_img_back")
            print(f"✅ client_img_back guardado: {client_img_back_path}")

    if preview_img_back and preview_img_back.filename:
        print("🔄 Procesando preview_img_back (back)...")
        preview_img_back_path = save_file_with_rollback(preview_img_back, "preview", "back")
        if preview_img_back_path:
            order_data["preview_img_back"] = preview_img_back_path
            back_has_design = True
            back_files_saved.append("preview_img_back")
            print(f"✅ preview_img_back guardado: {preview_img_back_path}")


    for key, value in order_data.items():
        if key in ['client_img', 'preview_img', 'client_img_back', 'preview_img_back']:
            print(f"  {key}: {value}")

    # Validar que haya al menos un diseño
    if not front_has_design and not back_has_design:
        print("❌ No hay diseños, limpiando archivos guardados...")
        # Limpiar archivos guardados si no hay diseño
        for file_path in saved_files:
            try:
                os.remove(file_path)
                print(f"  Eliminado: {file_path}")
            except Exception as e:
                print(f"  Error eliminando {file_path}: {e}")

        raise HTTPException(
            status_code=400,
            detail="No design provided. Please add at least one design (front or back)."
        )

    # Crear la orden en la base de datos
    try:
        print(f"\n🗄️ Creando orden en la base de datos...")
        order_db = Order(**order_data)
        db.add(order_db)
        db.commit()
        db.refresh(order_db)

        print(f"✅ Orden creada exitosamente - ID: {order_db.id}")

        response_data = {
            "success": True,
            "order_id": order_db.id,
            "message": "Order created successfully",
            "designs": {
                "front": {
                    "has_design": front_has_design,
                    "client_img": order_data.get("client_img"),
                    "preview_img": order_data.get("preview_img")
                },
                "back": {
                    "has_design": back_has_design,
                    "client_img_back": order_data.get("client_img_back"),
                    "preview_img_back": order_data.get("preview_img_back")
                }
            },
            "details": {
                "size": size,
                "color": color,
                "font": font
            }
        }
        return response_data

    except Exception as e:

        # Rollback: eliminar archivos guardados si hay error en la BD
        db.rollback()

        for file_path in saved_files:
            try:
                os.remove(file_path)
                print(f"  Eliminado: {file_path}")
            except Exception as delete_error:
                print(f"  Error eliminando {file_path}: {delete_error}")

        print(f"Error creating order in database: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while creating order. Please try again."
        )

@order_router.delete("/delete/{id}")
def delete_order(db:SessionDep, id:int):
    order_db = db.get(Order,id)
    if not order_db:
        raise HTTPException(status_code=404, detail="Order not found")



    order_db.delete_images(static_dir="static")

    db.delete(order_db)
    db.commit()
    return "Order deleted successfully"

@order_router.get("/order/{id}")
def get_order_by_id(db: SessionDep, id: int):
    # Buscar la orden
    order_db = db.get(Order, id)

    if not order_db:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verificar si la orden tiene un usuario asociado
    if order_db.user is None:
        raise HTTPException(status_code=404, detail="Order owner not found")

    # Buscar el usuario propietario
    owner = db.get(User, order_db.user)

    if not owner:
        raise HTTPException(status_code=404, detail="Order owner not found")

    # Retornar la respuesta estructurada
    return {
        "id": order_db.id,
        "owner": owner.email,
        "type": order_db.type,
        "size": order_db.size,
        "color": order_db.color,
        "date": order_db.date,
        "client_img": order_db.client_img,
        "specification":order_db.specification,
        "font":order_db.font,
        "preview_img": order_db.preview_img,
        "client_img_back": order_db.client_img_back,
        "preview_img_back": order_db.preview_img_back,
        "variation":order_db.variation,
        "qantity":order_db.qantity,
        "price":order_db.price,
    }
