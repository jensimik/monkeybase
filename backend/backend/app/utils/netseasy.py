import requests
from nameparser import HumanName

from ..core.config import settings

headers = {
    "Authorization": settings.NETS_EASY_SECRET_KEY,
    "CommercePlatformTag": "monkeybase",
    "Accept": "application/json",
}


async def create_payment_id(order_id, product, user):
    human_name = HumanName(user.name)
    post_data = {
        "checkout": {
            "integrationType": "EmbeddedCheckout",
            "url": "https://monkey.gnerd.dk/checkout.html",
            "termsUrl": "https://monkey.gnerd.dk/terms.html",
            "consumer": {
                "email": user.email,
                "phoneNumber": {
                    "prefix": "+45",
                    "number": user.mobile.replace("+45", ""),
                },
                "privatePerson": {
                    "firstName": human_name.first,
                    "lastName": human_name.last,
                },
            },
            "merchantHandlesConsumerData": True,
        },
        "notifications": {
            "webHooks": [
                {
                    "eventName": "payment.checkout.completed",
                    "url": "https://monkey.gnerd.dk/webhook-nets-easy",
                    "authorization": settings.NETS_EASY_WEBHOOK_SECRET,
                },
                {
                    "eventName": "payment.charge.failed",
                    "url": "https://monkey.gnerd.dk/webhook-nets-easy",
                    "authorization": settings.NETS_EASY_WEBHOOK_SECRET,
                },
            ]
        },
        "order": {
            "items": [
                {
                    "reference": f"product_id_{product.id}",
                    "name": product.name,
                    "quantity": 1,
                    "unit": "pcs",
                    "unitPrice": product.price,
                    "grossTotalAmount": product.price,
                    "netTotalAmount": product.price,
                }
            ],
            "amount": product.price,
            "currency": "DKK",
            "reference": str(order_id),
        },
    }
    req = requests.post(
        f"{settings.NETS_EASY_BASE_URL}/v1/payments",
        headers=headers,
        json=post_data,
        timeout=(5, 10),
    )
    if req.status_code == 201:
        data = req.json()
        return data["paymentId"]

    raise Exception(
        f"could not create payment_id server status code: {req.status_code} {req.text}"
    )
