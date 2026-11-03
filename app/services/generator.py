import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import ProductCard, ProductInput
from app.services.validator import validate_card

SYSTEM_PROMPT = (
    Path(__file__).resolve().parent.parent / "prompts" / "card_system.md"
).read_text(encoding="utf-8")

SCHEMA_HINT = (
    "Ответ должен быть JSON-объектом с полями seo_title, seo_description, "
    "key_specs (список объектов name/value), search_queries, manager_block, missing_info."
)


class LLMError(Exception):
    pass


def _call_llm(messages: list[dict]) -> str:
    settings = get_settings()
    try:
        response = httpx.post(
            settings.mistral_url,
            headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
            json={
                "model": settings.mistral_model,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=settings.request_timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.TimeoutException as exc:
        raise LLMError("Mistral не ответил за отведённое время") from exc
    except httpx.HTTPStatusError as exc:
        raise LLMError(f"Mistral вернул ошибку {exc.response.status_code}") from exc
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise LLMError("Не удалось получить ответ от Mistral") from exc


def generate_card(product: ProductInput) -> tuple[ProductCard, list[str]]:
    """Возвращает карточку и предупреждения. Нарушения правил приводят к повторным запросам."""
    settings = get_settings()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                product.model_dump(exclude_none=True), ensure_ascii=False, indent=2
            ),
        },
    ]

    card, errors, warnings = None, [], []
    for _ in range(settings.max_retries + 1):
        raw = _call_llm(messages)
        try:
            parsed = ProductCard.model_validate_json(raw)
        except ValidationError:
            feedback = [SCHEMA_HINT]
        else:
            card = parsed
            errors, warnings = validate_card(parsed, product)
            if not errors:
                return card, warnings
            feedback = errors
        messages += [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": "Исправь ответ. Нарушения:\n- "
                + "\n- ".join(feedback)
                + "\nВерни полный JSON заново.",
            },
        ]

    if card is None:
        raise LLMError("Модель не вернула корректный JSON")
    return card, errors + warnings