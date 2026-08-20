from openai import AzureOpenAI
from .config import settings
import json


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=settings.azure_openai_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
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
