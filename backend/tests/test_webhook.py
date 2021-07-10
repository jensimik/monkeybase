import json
import random
import string
import time
from unittest import mock

from loguru import logger

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from stripe.webhook import WebhookSignature

from backend.app import models
from backend.app.core.config import settings

PAYMENT_INTENT_CREATED = {
    "id": "evt_1J0A2uB3jLVglL0odkBjie9i",
    "object": "event",
    "api_version": "2020-08-27",
    "created": 1623178384,
    "data": {
        "object": {
            "id": "pi_1J0A2uB3jLVglL0orWoxZL4o",
            "object": "payment_intent",
            "amount": 2000,
            "amount_capturable": 0,
            "amount_received": 0,
            "application": None,
            "application_fee_amount": None,
            "canceled_at": None,
            "cancellation_reason": None,
            "capture_method": "automatic",
            "charges": {
                "object": "list",
                "data": [],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/charges?payment_intent=pi_1J0A2uB3jLVglL0orWoxZL4o",
            },
            "client_secret": "pi_1J0A2uB3jLVglL0orWoxZL4o_secret_9atN8YrFgJs9AATzlTu3Egzjy",
            "confirmation_method": "automatic",
            "created": 1623178384,
            "currency": "usd",
            "customer": None,
            "description": "(created by Stripe CLI)",
            "invoice": None,
            "last_payment_error": None,
            "livemode": False,
            "metadata": {},
            "next_action": None,
            "on_behalf_of": None,
            "payment_method": None,
            "payment_method_options": {
                "card": {
                    "installments": None,
                    "network": None,
                    "request_three_d_secure": "automatic",
                }
            },
            "payment_method_types": ["card"],
            "receipt_email": None,
            "review": None,
            "setup_future_usage": None,
            "shipping": None,
            "source": None,
            "statement_descriptor": None,
            "statement_descriptor_suffix": None,
            "status": "requires_payment_method",
            "transfer_data": None,
            "transfer_group": None,
        }
    },
    "livemode": False,
    "pending_webhooks": 1,
    "request": {"id": "req_07X5MudaGVx9sW", "idempotency_key": None},
    "type": "payment_intent.created",
}

PAYMENT_INTENT_FAILED = PAYMENT_INTENT_CREATED.copy()
PAYMENT_INTENT_FAILED["type"] = "payment_intent.fail"

PAYMENT_INTENT_SUCCEEDED = PAYMENT_INTENT_CREATED.copy()
PAYMENT_INTENT_SUCCEEDED["type"] = "payment_intent.succeeded"


def _webhook_post(client: TestClient, payload: dict, make_invalid=False):
    data = json.dumps(payload)
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{data}"
    signature = WebhookSignature._compute_signature(
        signed_payload, settings.STRIPE_WEBHOOK_SECRET
    )
    if make_invalid:
        list_signature = list(signature)
        for _ in range(random.randint(5, 10)):
            list_signature[random.randint(0, len(list_signature) - 1)] = random.choice(
                [string.ascii_lowercase]
            )
        signature = "".join(list_signature)
    headers = {"stripe-signature": f"t={timestamp},v1={signature}"}
    return client.post("/webhook/stripe", headers=headers, data=data)


@mock.patch("backend.app.core.utils._sendgrid_send")
def test_webhook_payment_intent_succeeded(
    mock_mail_send,
    client: TestClient,
    auth_client_basic: TestClient,
    slot_with_stripe_id: models.Slot,
):
    # this doesnt do anything currently but should return 200
    response = _webhook_post(client, PAYMENT_INTENT_CREATED)
    assert response.status_code == status.HTTP_200_OK

    # response = _webhook_post(client, PAYMENT_INTENT_FAILED)
    # assert response.status_code == status.HTTP_200_OK

    PAYMENT_INTENT_SUCCEEDED["data"]["object"]["id"] = slot_with_stripe_id.payment_id
    response = _webhook_post(client, PAYMENT_INTENT_SUCCEEDED)
    assert response.status_code == status.HTTP_200_OK
    assert mock_mail_send.called

    # check this user is now member of product 1
    response = auth_client_basic.get("/me")
    user = response.json()
    assert user["member"][0]["product"]["id"] == 1


def test_webhook_invalid(
    client: TestClient,
    auth_client_basic: TestClient,
    slot_with_stripe_id: models.Slot,
):
    PAYMENT_INTENT_SUCCEEDED["data"]["object"]["id"] = slot_with_stripe_id.payment_id
    response = _webhook_post(client, PAYMENT_INTENT_SUCCEEDED, make_invalid=True)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


NETS_EVENT_COMPLETED = {
    "id": "36ce3ff4a896450ea2b70f3263554772",
    "merchantId": 100017120,
    "timestamp": "2021-05-04T22:09:08.4342+02:00",
    "event": "payment.checkout.completed",
    "data": {
        "order": {
            "amount": {"amount": 5500, "currency": "SEK"},
            "reference": "Hosted Demo Order",
            "orderItems": [
                {
                    "reference": "Sneaky NE2816-82",
                    "name": "Sneaky",
                    "quantity": 2,
                    "unit": "pcs",
                    "unitPrice": 2500,
                    "taxRate": 1000,
                    "taxAmount": 500,
                    "netTotalAmount": 5000,
                    "grossTotalAmount": 5500,
                }
            ],
        },
        "consumer": {
            "firstName": "John",
            "lastName": "Doe",
            "billingAddress": {
                "addressLine1": "Solgatan 4",
                "addressLine2": "",
                "city": "STOCKHOLM",
                "country": "SWE",
                "postcode": "11522",
                "receiverLine": "John doe",
            },
            "country": "SWE",
            "email": "john.doe@example.com",
            "ip": "192.230.114.3",
            "phoneNumber": {"prefix": "+46", "number": "12345678"},
            "shippingAddress": {
                "addressLine1": "Solgatan 4",
                "addressLine2": "",
                "city": "STOCKHOLM",
                "country": "SWE",
                "postcode": "11522",
                "receiverLine": "John Doe",
            },
        },
        "paymentId": "02a900006091a9a96937598058c4e474",
    },
}


@mock.patch("backend.app.core.utils._sendgrid_send")
def test_nets_webhook_success(
    mock_mail_send,
    client: TestClient,
    slot_with_nets_id: models.Slot,
):
    NETS_EVENT_COMPLETED["data"]["paymentId"] = slot_with_nets_id.payment_id

    logger.info(NETS_EVENT_COMPLETED)

    headers = {"Authorization": f"Bearer {settings.NETS_EASY_WEBHOOK_SECRET}"}
    response = client.post(
        "/webhook/netseasy", headers=headers, json=NETS_EVENT_COMPLETED
    )

    assert response.status_code == status.HTTP_200_OK

    assert mock_mail_send.called
