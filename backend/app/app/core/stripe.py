import stripe
from .config import settings

stripe.api_key = settings.STRIPE_API_KEY


def create_payment_intent(amount: int) -> dict:
    return stripe.PaymentIntent.create(amount=amount, currency="dkk")


def create_customer(email: str, name: str) -> str:
    customer = stripe.Customer.create(email=email, name=name)
    return customer["id"]


def update_customer(customer_id: str, email: str, name: str) -> dict:
    return stripe.Customer.modify(customer_id, email=email, name=name)
