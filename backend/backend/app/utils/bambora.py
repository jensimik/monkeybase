import aiohttp

from ..core.config import settings

CHECKOUT_SESSION_URL = "https://api.v1.checkout.bambora.com/sessions"
HEADERS = {"Authorization": f"Basic {settings.BAMBORA_API_KEY}"}


async def create_checkout_session(slot_id, amount, email, language):
    post_data = {
        "order": {"id": slot_id, "amount": amount, "currency": "DKK"},
        "customer": {"email": email},
        "instantcaptureamount": amount,
        "url": {
            "accept": settings.BAMBORA_ACCEPT_URL,
            "cancel": settings.BAMBORA_CANCEL_URL,
            "callbacks": [settings.BAMBORA_CALLBACK_URL.format(slot_id=slot_id)],
        },
        "paymentwindow": {
            "id": 1,
            "language": language,
            "paymentmethods": [
                {"id": "paymentcard", "action": "include"},
                {"id": "mobilepay", "action": "include"},
                {"id": "vipps", "action": "include"},
                {"id": "swish", "action": "include"},
            ],
        },
    }
    # if less than 200 DKK then try to avoid SCA
    # might be usefull for day-card-tickets?
    if amount < 20000:
        post_data["securitylevel"] = "none"
        post_data["securityexemption"] = "lowvaluepayment"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(
            CHECKOUT_SESSION_URL,
            json=post_data,
        ) as response:
            data = await response.json()
            meta = data["meta"]
            if meta["result"]:
                return data["token"], data["url"]
            # else raise exception with error
            raise Exception(meta["message"]["enduser"])
