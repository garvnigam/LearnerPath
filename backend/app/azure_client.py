from openai import OpenAI
from .config import settings
import json


def get_client() -> OpenAI:
    # Azure AI Foundry resources expose an OpenAI-compatible endpoint at
    # <resource-root>/openai/v1 — normalize whatever root URL is configured
    # so this works whether or not the portal-copied value already has the suffix.
    base_url = settings.azure_openai_endpoint.rstrip("/")
    if not base_url.endswith("/openai/v1"):
        base_url += "/openai/v1"
    return OpenAI(
        api_key=settings.azure_openai_key,
        base_url=base_url,
    )


def chat_json(system: str, messages: list[dict], temperature: float = 0.4) -> dict:
    client = get_client()
    resp = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "system", "content": system}] + messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content or "{}")


def chat_text(system: str, messages: list[dict], temperature: float = 0.7) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "system", "content": system}] + messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""
