import re
from dataclasses import dataclass

from app.schemas import ProductInput


@dataclass(frozen=True)
class RequiredField:
    key: str    # "name" | "manufacturer" | "description" | "url" | "specs" | "specs.<название>"
    label: str  # как показываем пользователю


@dataclass(frozen=True)
class ProductClass:
    key: str
    name_ru: str
    keywords: tuple[str, ...]  # по каким словам в названии или типе узнаём класс
    required: tuple[RequiredField, ...]


def _specs(*names: str) -> tuple[RequiredField, ...]:
    return tuple(RequiredField(f"specs.{name}", name) for name in names)


BASE = (
    RequiredField("name", "Название товара"),
    RequiredField("manufacturer", "Производитель"),
    RequiredField("description", "Описание или фрагмент технического паспорта"),
    RequiredField("url", "Ссылка на товар"),
)

DISCRETE_MODULE = ProductClass(
    key="discrete_module",
    name_ru="модуль ввода/вывода дискретных сигналов",
    keywords=("модуль ввода", "модуль вывода", "мк110"),
    required=BASE
    + _specs(
        "Напряжение питания:; МК110-220.8Д(ДН).4Р; МК110-224.8Д(ДН).4Р",
        "Потребляемая мощность, ВА, не более",
        "Количество дискретных выходных элементов",
        "Параметры дискретных выходов (электромагнитных реле)",
        "Количество дискретных входов",
        "Интерфейс связи с компьютером",
        "Максимальная скорость обмена по интерфейсу RS-485, бит/сек",
        "Протокол связи, используемый для передачи информации",
        "Степень защиты корпуса",
        "Габаритные размеры прибора, мм",
        "Масса прибора, кг, не более",
        "Средний срок службы, лет",
        "Гальваническая развязка дискретных входов",
        "Электрическая прочность изоляции дискретных входов, В",
        "Максимальная частота сигнала, подаваемого на дискретный вход, кГц",
        "Минимальная длительность импульса, воспринимаемого дискретным входом, мс",
        "Напряжение питания дискретных входов, В",
        "Максимальный входной ток дискретного входа, мА, не более",
        "Ток «логической единицы», мА, не менее",
        "Ток «логического нуля», мА, не более",
        "Сопротивление контакта (ключа) и соединительных проводов, подключаемых к дискретному входу, Ом, не более",
        "Тип датчика дискретного входа",
    ),
)

CURRENT_CLAMPS = ProductClass(
    key="current_clamps",
    name_ru="токовые клещи",
    keywords=("клещи", "датчик тока"),
    required=BASE + _specs("Напряжение, В", "Сила тока"),
)

# запасной класс, если тип товара не определился
GENERIC = ProductClass(
    key="generic",
    name_ru="не определён",
    keywords=(),
    required=BASE + (RequiredField("specs", "Технические характеристики"),),
)

CLASSES = (DISCRETE_MODULE, CURRENT_CLAMPS)


def normalize(text: str) -> str:
    text = re.sub(r"[^a-zа-я0-9 ]+", " ", text.lower().replace("ё", "е"))
    return " ".join(text.split())


def detect_class(product: ProductInput) -> ProductClass:
    haystack = normalize(f"{product.name or ''} {product.specs.get('Тип', '')}")
    for cls in CLASSES:
        if any(keyword in haystack for keyword in cls.keywords):
            return cls
    return GENERIC