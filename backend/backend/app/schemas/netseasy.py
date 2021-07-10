from typing import Optional
from pydantic import BaseModel


class WebhookEvent(BaseModel):
    id: str
    merchantId: int
    timestamp: str
    event: str
    data: dict


# class Amount(BaseModel):
#     amount: int
#     currency: str


# class Order(BaseModel):
#     amount: Optional[Amount]


# class CheckoutCompletedData(BaseModel):
#     paymentId: str
#     order: Optional[Order]


# class CheckoutCompleted(WebhookEvent):
#     data: CheckoutCompletedData
