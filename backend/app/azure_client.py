from openai import OpenAI
from .config import settings
import json
import httpx


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


def _embeddings_base_url() -> str:
    """Azure resource root for embedding calls (NOT the /openai/v1 shape).

    Prefer the explicit embeddings_model_endpoint if set; otherwise derive from
    the chat endpoint by stripping any /openai/v1 or Foundry-project suffix.
    """
    ep = settings.embeddings_model_endpoint or settings.azure_openai_endpoint
    ep = ep.rstrip("/")
    for suffix in ("/openai/v1", "/openai"):
        if ep.endswith(suffix):
            ep = ep[: -len(suffix)]
    # If someone configured a Foundry project URL, coerce to the resource root.
    if "services.ai.azure.com" in ep and "/api/projects/" in ep:
        ep = ep.split("/api/projects/")[0].replace(
            "services.ai.azure.com", "openai.azure.com"
        )
    return ep


async def embed_text(text: str, timeout: float = 20.0) -> list[float]:
    """Return a 1536-dim embedding vector via Azure text-embedding-3-small.

    Uses direct HTTPS instead of the openai client because the embeddings
    deployment lives at the resource root (no /openai/v1 in the URL).
    """
    if not text or not text.strip():
        return []
    base = _embeddings_base_url()
    deployment = settings.embeddings_model_deployment or "text-embedding-3-small"
    key = settings.embeddings_model_key or settings.azure_openai_key
    api_version = settings.azure_openai_api_version or "2024-08-01-preview"
    url = f"{base}/openai/deployments/{deployment}/embeddings?api-version={api_version}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            url,
            headers={"api-key": key, "Content-Type": "application/json"},
            json={"input": text[:4000]},  # trim to keep latency stable
        )
        r.raise_for_status()
        data = r.json()["data"]
        return data[0]["embedding"]
