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
        raise HTTPException(status_code=402, detail=error_msg)  # Solo el mensaje amigable
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail='Payment error')

def add_payment_method_to_user(customer_id: str, payment_method_id: str):
    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )
    except stripe.error.StripeError as e:
        # Extraer el mensaje amigable del error
        if hasattr(e, 'error') and hasattr(e.error, 'message'):
            error_msg = e.error.message
            # Limpiar el mensaje si es necesario
            if 'expired' in error_msg.lower():
                raise HTTPException(status_code=402, detail='Your card has expired')
            elif 'declined' in error_msg.lower():
                raise HTTPException(status_code=402, detail='Your card was declined')
            else:
                raise HTTPException(status_code=402, detail='Card error')
        raise HTTPException(status_code=400, detail='Payment error')

def create_payment(payment_method_id: str, customer_id: str, amount: int):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency='usd',
            payment_method=payment_method_id,
            customer=customer_id,
            confirm=True,
        )
        return payment_intent
    except stripe.error.CardError as e:
        error_messages = {
            'card_declined': 'Your card was declined',
            'insufficient_funds': 'Insufficient funds',
            'expired_card': 'Your card has expired',
            'incorrect_cvc': 'Incorrect security code',
            'processing_error': 'Processing error',
        }
        error_code = e.error.code if hasattr(e, 'error') else 'card_declined'
        error_msg = error_messages.get(error_code, 'Your card was declined')
        raise HTTPException(status_code=402, detail=error_msg)
    except stripe.error.StripeError as e:
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