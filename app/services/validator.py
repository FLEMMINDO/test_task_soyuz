import re

from app.schemas import ProductCard, ProductInput

TITLE_MAX = 70
DESC_MIN, DESC_MAX = 800, 1200
QUERIES_MIN, QUERIES_MAX = 3, 5
RICH_INPUT_SPECS = 3  # при меньшем числе характеристик нижняя граница длины не обязательна

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_THOUSANDS = re.compile(r"(?<=\d)[\s\u00a0](?=\d{3}(?!\d))")
_IGNORE = re.compile(r"B2B|B2C|24/7", re.IGNORECASE)


def _numbers(text: str) -> set[str]:
    text = _THOUSANDS.sub("", _IGNORE.sub(" ", text))
    return {n.replace(",", ".") for n in _NUMBER.findall(text)}


def _input_text(product: ProductInput) -> str:
    parts = [product.name, product.manufacturer, product.description, product.url]
    parts += [f"{k} {v}" for k, v in product.specs.items()]
    return " ".join(p for p in parts if p)


def _card_text(card: ProductCard) -> str:
    parts = [card.seo_title, card.seo_description, card.manager_block, *card.search_queries]
    parts += [f"{s.name} {s.value}" for s in card.key_specs]
    return " ".join(parts)


def validate_card(card: ProductCard, product: ProductInput) -> tuple[list[str], list[str]]:
    """Возвращает (ошибки, предупреждения). Ошибки запускают повторный запрос к модели."""
    errors, warnings = [], []

    if len(card.seo_title) > TITLE_MAX:
        errors.append(
            f"SEO-заголовок {len(card.seo_title)} символов, нужно не больше {TITLE_MAX}"
        )

    length = len(card.seo_description)
    if length > DESC_MAX:
        errors.append(f"SEO-описание {length} символов, нужно не больше {DESC_MAX}")
    elif length < DESC_MIN:
        message = f"SEO-описание {length} символов, нужно не меньше {DESC_MIN}"
        if len(product.specs) >= RICH_INPUT_SPECS:
            errors.append(message)
        else:
            warnings.append(message + " (во входных данных мало информации)")

    if not QUERIES_MIN <= len(card.search_queries) <= QUERIES_MAX:
        errors.append(
            f"Поисковых запросов {len(card.search_queries)}, нужно от {QUERIES_MIN} до {QUERIES_MAX}"
        )

    foreign = sorted(_numbers(_card_text(card)) - _numbers(_input_text(product)))
    if foreign:
        errors.append(
            "В тексте есть числа, которых нет во входных данных: "
            + ", ".join(foreign)
            + ". Удали их или замени на формулировки без чисел"
        )

    return errors, warnings