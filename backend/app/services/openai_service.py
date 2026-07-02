import json

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def chat_json(system_prompt: str, user_prompt: str) -> dict:
    """Call the chat model and parse a JSON object from its response."""
    response = get_client().chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return json.loads(response.choices[0].message.content)


def chat_text(system_prompt: str, messages: list[dict]) -> str:
    response = get_client().chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return response.choices[0].message.content
