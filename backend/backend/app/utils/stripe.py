import stripe

from ..core.config import settings

stripe.api_key = settings.STRIPE_API_KEY


def create_payment_intent(
    stripe_customer_id: str,
    amount: int,
    statement_descriptor_suffix: str,
    metadata: dict,
) -> dict:
    return stripe.PaymentIntent.create(
        customer=stripe_customer_id,
        statement_descriptor_suffix=statement_descriptor_suffix,
        amount=amount,
        currency="dkk",
        payment_method_types=["card"],
        metadata=metadata,
    )


def create_customer(email: str, name: str, metadata: dict) -> str:
    customer = stripe.Customer.create(email=email, name=name, metadata=metadata)
    return customer.id


def update_customer(stripe_customer_id: str, email: str, name: str) -> dict:
    return stripe.Customer.modify(stripe_customer_id, email=email, name=name)
