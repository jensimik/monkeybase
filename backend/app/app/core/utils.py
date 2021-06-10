from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, From, Mail

from .. import models
from .config import settings


class MailTemplateEnum(Enum):

    PASSWORD_RESET = "d-d53c66a7bcb54b2ca17ccd7f6b1be47d"
    WELCOME = "d-d53c66a7bcb54b2ca17ccd7f6b1be47d"
    PAYMENT_FAILED = "pf1"
    PAYMENT_SUCCEEDED = "ps1"


def send_transactional_email(
    to_email: str,
    template_id: str,
    data: Dict[Any, Any],
    attachments: List[Attachment] = [],
):
    sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    message = Mail(
        from_email=From(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
        to_emails=to_email,
    )
    message.template_id = template_id
    message.dynamic_template_data = data

    for attachment in attachments:
        message.add_attachment(attachment)

    sg_client.send(message)
