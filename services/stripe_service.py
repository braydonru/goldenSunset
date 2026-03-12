import os
from dotenv import load_dotenv
import stripe
from fastapi import HTTPException

load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# En tu stripe_service.py, modifica las excepciones:

def create_payment_method(token: str) -> str:
    try:
        # Validar que el token no esté vacío
        if not token or not token.startswith('tok_'):
            raise HTTPException(status_code=400, detail="Invalid payment token")

        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={"token": token},
        )
        return payment_method.id
    except stripe.error.CardError as e:
        error_messages = {
            'card_declined': 'Your card was declined',
            'insufficient_funds': 'Insufficient funds',
            'expired_card': 'Your card has expired',
            'incorrect_cvc': 'Incorrect security code',
            'processing_error': 'Processing error',
            'lost_card': 'Card reported as lost',
            'stolen_card': 'Card reported as stolen',
            'pickup_card': 'Bank requests to pick up card',
        }
        error_code = e.error.code if hasattr(e, 'error') else 'card_declined'
        error_msg = error_messages.get(error_code, 'Your card was declined')
        raise HTTPException(status_code=402, detail=error_msg)
    except stripe.error.InvalidRequestError as e:
        # Token inválido o ya usado
        if 'token' in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid or expired payment token")
        raise HTTPException(status_code=400, detail="Invalid payment request")
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail='Payment error')


def add_payment_method_to_user(customer_id: str, payment_method_id: str):
    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )
    except stripe.error.StripeError as e:
        # Si el método ya está asociado, no es un error grave
        if hasattr(e, 'error') and hasattr(e.error, 'message'):
            error_msg = e.error.message
            if 'already' in error_msg.lower() and 'customer' in error_msg.lower():
                # El método ya está asociado, podemos continuar
                print(f"⚠️ Payment method already attached to customer")
                return

        # Si hay un error de tarjeta específico
        if hasattr(e, 'error') and hasattr(e.error, 'code'):
            error_code = e.error.code
            if error_code == 'expired_card':
                raise HTTPException(status_code=402, detail='Your card has expired')
            elif error_code == 'card_declined':
                raise HTTPException(status_code=402, detail='Your card was declined')
            elif error_code == 'incorrect_cvc':
                raise HTTPException(status_code=402, detail='Incorrect security code')

        # Si es otro error, propagar con mensaje amigable
        raise HTTPException(status_code=400, detail='Payment error')


def create_payment(payment_method_id: str, customer_id: str, amount: int):
    try:
        print(f"💳 Intentando crear pago:")
        print(f"   - payment_method_id: {payment_method_id}")
        print(f"   - customer_id: {customer_id}")
        print(f"   - amount: ${amount}")

        # URL de retorno (configurable por entorno)
        return_url = os.getenv("STRIPE_RETURN_URL", "http://localhost:3000/orders")

        # Intentar primero sin redirecciones
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='usd',
                payment_method=payment_method_id,
                customer=customer_id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # 👈 ESTO ES LA CLAVE
                }
            )
            return payment_intent

        except stripe.error.StripeError as e:
            # Si el error es porque requiere redirección, intentar con return_url
            if 'return_url' in str(e).lower() or 'redirect' in str(e).lower():
                print(f"⚠️ Tarjeta requiere autenticación 3D Secure")

                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),
                    currency='usd',
                    payment_method=payment_method_id,
                    customer=customer_id,
                    confirm=True,
                    return_url=return_url,
                )

                if payment_intent.status == 'requires_action':
                    # Devolver información para que el frontend maneje 3D Secure
                    return {
                        "requires_action": True,
                        "payment_intent_client_secret": payment_intent.client_secret,
                        "status": "requires_action"
                    }
                return payment_intent
            else:
                # Si es otro error, propagarlo
                raise e

    except stripe.error.CardError as e:
        error_code = e.error.code if hasattr(e, 'error') else 'unknown'
        error_msg = e.error.message if hasattr(e, 'error') else str(e)
        print(f"❌ CardError: {error_code} - {error_msg}")

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


def create_user(name: str, email: str) -> str:
    """Crea un cliente en Stripe y devuelve su ID"""
    try:
        # Buscar si el cliente ya existe por email
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            return customers.data[0].id

        # Crear nuevo cliente
        customer = stripe.Customer.create(
            name=name,
            email=email,
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")
