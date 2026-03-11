from fastapi import APIRouter, HTTPException, Form
from sqlmodel import select
from routes.deps.db_session import SessionDep
from models.order import Order
from models.user import User
from models.ruser_payment_method import User_payment_method
from services.stripe_service import create_payment, add_payment_method_to_user, create_user, create_payment_method
import traceback

stripe_router = APIRouter(prefix='/stripe', tags=['Stripe'])


@stripe_router.post("/payment")
def stripe_payment(
        db: SessionDep,
        client_id: int = Form(...),
        order_id: int = Form(...),
        token: str = Form(...),  # token de la tarjeta (tok_visa, etc.)
):
    try:
        # 1. Verificar orden
        order_db = db.get(Order, order_id)
        if not order_db:
            raise HTTPException(status_code=404, detail="Order not found")

        # 2. Verificar que la orden no esté ya pagada
        if order_db.state:
            raise HTTPException(status_code=400, detail="Order already paid")

        # 3. Verificar usuario
        user_db = db.get(User, client_id)
        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        # 4. Crear PaymentMethod con el token
        payment_method_id = create_payment_method(token)
        print(f"✅ PaymentMethod creado: {payment_method_id}")

        # 5. Crear o obtener cliente en Stripe
        stripe_customer_id = create_user(user_db.name, user_db.email)
        print(f"✅ Cliente Stripe: {stripe_customer_id}")

        # 6. Asociar método de pago al cliente
        add_payment_method_to_user(stripe_customer_id, payment_method_id)
        print(f"✅ Método asociado al cliente")

        # 7. Crear y confirmar el pago
        create_payment(payment_method_id, stripe_customer_id, order_db.price)
        print(f"✅ Pago realizado exitosamente")

        # 8. Actualizar orden
        order_db.state = True
        db.commit()

        return {
            "status": "success",
            "message": "Payment completed successfully",
            "order_id": order_db.id
        }

    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")