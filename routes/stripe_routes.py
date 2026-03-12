from fastapi import APIRouter, HTTPException, Form
from sqlmodel import select
from routes.deps.db_session import SessionDep
from models.order import Order
from models.user import User
from services.stripe_service import create_payment, add_payment_method_to_user, create_user, create_payment_method
import traceback
import time
import os
import stripe

STRIPE_SECRET_KEY = os.getenv("STRIPE_KEY")
stripe.api_key = STRIPE_SECRET_KEY
stripe_router = APIRouter(prefix='/stripe', tags=['Stripe'])


from fastapi import APIRouter, HTTPException, Form
from sqlmodel import select
from routes.deps.db_session import SessionDep
from models.order import Order
from models.user import User
from services.stripe_service import create_payment, add_payment_method_to_user, create_user, create_payment_method
import traceback
import time

stripe_router = APIRouter(prefix='/stripe', tags=['Stripe'])


@stripe_router.post("/payment")
def stripe_payment(
        db: SessionDep,
        client_id: int = Form(...),
        order_id: int = Form(...),
        token: str = Form(...),
):
    try:
        print(f"\n📦 === NUEVA PETICIÓN DE PAGO ===")
        print(f"   - client_id: {client_id}")
        print(f"   - order_id: {order_id}")

        # 1. Validar orden
        order_db = db.get(Order, order_id)
        if not order_db:
            raise HTTPException(status_code=404, detail="Order not found")

        if order_db.state:
            raise HTTPException(status_code=400, detail="Order already paid")

        # 2. Validar usuario
        user_db = db.get(User, client_id)
        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        # 3. Validar precio
        if not order_db.price or order_db.price <= 0:
            raise HTTPException(status_code=400, detail="Invalid order amount")

        # 4. Crear PaymentMethod
        try:
            payment_method_id = create_payment_method(token)
            print(f"✅ PaymentMethod: {payment_method_id}")
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid payment token")

        # 5. Crear cliente Stripe
        try:
            stripe_customer_id = create_user(user_db.name, user_db.email)
            print(f"✅ Cliente Stripe: {stripe_customer_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Could not create Stripe customer")

        # 6. Asociar método de pago
        try:
            add_payment_method_to_user(stripe_customer_id, payment_method_id)
            print(f"✅ Método asociado")
        except Exception as e:
            # Si ya está asociado, continuamos
            pass

        time.sleep(1)

        # 7. Crear pago SIN REDIRECCIONES
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(order_db.price * 100),
                currency='usd',
                payment_method=payment_method_id,
                customer=stripe_customer_id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # 👈 NO REDIRECCIONES
                }
            )

            if payment_intent.status == 'succeeded':
                order_db.state = True
                db.commit()
                return {
                    "status": "success",
                    "message": "Payment completed",
                    "order_id": order_db.id
                }
            else:
                return {
                    "status": payment_intent.status,
                    "message": f"Payment {payment_intent.status}"
                }

        except stripe.error.CardError as e:
            error_code = e.error.code if hasattr(e, 'error') else 'unknown'
            error_messages = {
                'card_declined': 'Your card was declined',
                'insufficient_funds': 'Insufficient funds',
                'expired_card': 'Your card has expired',
                'incorrect_cvc': 'Incorrect security code',
                'processing_error': 'Processing error',
            }
            error_msg = error_messages.get(error_code, 'Your card was declined')
            raise HTTPException(status_code=402, detail=error_msg)

        except stripe.error.StripeError as e:
            print(f"❌ StripeError: {str(e)}")
            raise HTTPException(status_code=400, detail='Payment error')

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@stripe_router.post("/confirm-payment")
def confirm_payment(
        db: SessionDep,
        order_id: int = Form(...),
        payment_intent_id: str = Form(...),
):
    """Endpoint para confirmar pagos después de 3D Secure"""
    try:
        print(f"🔄 Confirmando pago para orden {order_id}")

        # Verificar el estado del PaymentIntent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status == 'succeeded':
            order_db = db.get(Order, order_id)
            if order_db:
                order_db.state = True
                db.commit()
                print(f"✅ Orden {order_id} marcada como pagada después de 3D Secure")

            return {
                "status": "success",
                "message": "Payment confirmed successfully",
                "order_id": order_id
            }
        else:
            return {
                "status": payment_intent.status,
                "message": f"Payment is {payment_intent.status}",
                "order_id": order_id
            }

    except Exception as e:
        print(f"❌ Error confirmando pago: {str(e)}")
        raise HTTPException(status_code=400, detail="Payment confirmation failed")
