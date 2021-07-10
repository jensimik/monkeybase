from pydantic import BaseModel


class WebhookEvent(BaseModel):
    id: str
    merchantId: int
    timestamp: str
    event: str
    data: dict
