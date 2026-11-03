from app.schemas import NO_DATA, MissingField, ProductCard, ProductInput, Spec
from app.services.product_classes import ProductClass, normalize


def _is_filled(product: ProductInput, key: str) -> bool:
    if key.startswith("specs."):
        wanted = normalize(key.removeprefix("specs."))
        return any(normalize(name) == wanted for name in product.specs)
    if key == "specs":
        return bool(product.specs)
    return bool(getattr(product, key))


def find_missing(product: ProductInput, cls: ProductClass) -> list[MissingField]:
    return [
        MissingField(key=field.key, label=field.label)
        for field in cls.required
        if not _is_filled(product, field.key)
    ]


def apply_missing(card: ProductCard, missing: list[MissingField]) -> ProductCard:
    """Список недостающего формирует код по классу товара, а не модель."""
    card.key_specs = [s for s in card.key_specs if s.value.strip().lower() != NO_DATA]
    card.key_specs += [Spec(name=f.label, value=NO_DATA) for f in missing if f.key.startswith("specs")]
    card.missing_info = [f.label for f in missing]
    return card


def merge(base: ProductInput, extra: ProductInput) -> ProductInput:
    """Данные пользователя дополняют исходные; уже заполненное поле не затирается."""
    return ProductInput(
        name=base.name or extra.name,
        manufacturer=base.manufacturer or extra.manufacturer,
        specs={**extra.specs, **base.specs},
        description=base.description or extra.description,
        url=base.url or extra.url,
    )