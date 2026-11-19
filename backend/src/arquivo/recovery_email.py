"""Entrega de ligações de recuperação. Os tokens e destinatários nunca vão para logs."""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from arquivo.config import get_settings

logger = logging.getLogger(__name__)


def send_recovery_email(email: str, token: str) -> None:
    settings = get_settings()
    if settings.resend_api_key is None or settings.public_url is None:
        logger.error("Serviço de recuperação de acesso indisponível")
        return
    link = f"{settings.public_url}/#recuperar={token}"
    payload = {
        "from": settings.recovery_email_from,
        "to": [email],
        "subject": "Recuperar acesso ao Arquivo do Universo",
        "text": (
            "Recebemos um pedido para alterar a tua palavra-passe.\n\n"
            f"Escolhe uma nova palavra-passe nesta ligação, válida por 30 minutos:\n{link}\n\n"
            "Se não pediste esta alteração, podes ignorar este email."
        ),
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {settings.resend_api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "User-Agent": "ArquivoDoUniverso/0.1",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            response.read()
    except HTTPError as error:
        logger.error("Falha na entrega da recuperação de acesso (HTTP %s)", error.code)
    except (URLError, TimeoutError, OSError):
        logger.error("Falha na ligação ao serviço de recuperação de acesso")
