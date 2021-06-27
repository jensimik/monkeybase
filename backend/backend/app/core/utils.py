import datetime
from enum import Enum, unique
from typing import Any, Dict, List

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, From, Mail

from .config import settings


def tz_now():
    return datetime.datetime.now(settings.TZ)


def tz_today():
    return tz_now().date()


@unique
class MailTemplateEnum(str, Enum):

    PASSWORD_RESET: str = "d-d53c66a7bcb54b2ca17ccd7f6b1be47d"
    WELCOME: str = "a-d53c66a7bcb54b2ca17ccd7f6b1be47d"
    PAYMENT_FAILED: str = "pf1"
    PAYMENT_SUCCEEDED: str = "ps1"


sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)


def _sendgrid_send(message):
    sg_client.send(message)


def send_transactional_email(
    to_email: str,
    template_id: str,
    data: Dict[Any, Any],
    attachments: List[Attachment] = [],
):

    message = Mail(
        from_email=From(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = data

    for attachment in attachments:
        message.add_attachment(attachment)

    _sendgrid_send(message)
