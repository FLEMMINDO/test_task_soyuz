import json

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import (
    GenerateRequest,
    GenerateResponse,
    ProductInput,
)
from app.services.completeness import apply_missing, find_missing, merge
from app.services.generator import LLMError, generate_card
from app.services.product_classes import detect_class

router = APIRouter(prefix="/api")


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    if len(req.raw) > get_settings().max_input_chars:
        raise HTTPException(413, "Входной JSON слишком большой")

    try:
        data = json.loads(req.raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            400, f"Некорректный JSON: {exc.msg} (строка {exc.lineno}, символ {exc.colno})"
        )
    if not isinstance(data, dict):
        raise HTTPException(400, "Ожидался JSON-объект с данными одного товара")

    try:
        product = ProductInput.model_validate(data)
    except ValidationError as exc:
        details = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(422, f"Некорректные данные товара: {details}")

    if req.extra:
        product = merge(product, req.extra)

    cls = detect_class(product)
    missing = find_missing(product, cls)
    if missing and not req.force:
        return GenerateResponse(
            status="needs_more_data",
            product_class=cls.name_ru,
            missing_fields=missing,
            product=product,
        )
    if not product.name:
        raise HTTPException(422, "Без названия товара карточку сформировать нельзя")

    try:
        card, warnings = generate_card(product)
    except LLMError as exc:
        raise HTTPException(502, str(exc))

    card = apply_missing(card, missing)

    return GenerateResponse(
        status="ok",
        product_class=cls.name_ru,
        missing_fields=missing,
        product=product,
        card=card,
        warnings=warnings,
    )