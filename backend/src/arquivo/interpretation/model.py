import logging
from typing import Protocol

import anthropic


class InterpretationUnavailable(RuntimeError):
    pass


class InterpretationMisconfigured(InterpretationUnavailable):
    pass


class TextModel(Protocol):
    name: str

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str: ...


class AnthropicModel:
    def __init__(self, api_key: str, model: str) -> None:
        self.name = model
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=240.0,
            max_retries=2,
        )

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        try:
            response = self._client.messages.create(
                model=self.name,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
        except (
            anthropic.BadRequestError,
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
            anthropic.NotFoundError,
        ) as error:
            logging.getLogger(__name__).error(
                "erro de configuração Anthropic (%s)", type(error).__name__
            )
            raise InterpretationMisconfigured(
                "a configuração do serviço de interpretação é inválida"
            ) from error
        except (anthropic.APIError, TimeoutError) as error:
            raise InterpretationUnavailable(
                "o serviço de interpretação está indisponível"
            ) from error
        return "".join(block.text for block in response.content if block.type == "text")
