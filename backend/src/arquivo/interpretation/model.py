from typing import Protocol

import anthropic


class InterpretationUnavailable(RuntimeError):
    pass


class TextModel(Protocol):
    name: str

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str: ...


class AnthropicModel:
    def __init__(self, api_key: str, model: str) -> None:
        self.name = model
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=60.0,
            max_retries=2,
        )

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        try:
            response = self._client.messages.create(
                model=self.name,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                extra_body={"temperature": 0.8},
            )
        except (anthropic.APIError, TimeoutError) as error:
            raise InterpretationUnavailable(
                "o serviço de interpretação está indisponível"
            ) from error
        return "".join(block.text for block in response.content if block.type == "text")
