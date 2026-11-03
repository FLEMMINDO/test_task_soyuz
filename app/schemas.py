from typing import Literal

from pydantic import BaseModel, Field, field_validator

NO_DATA = "данных нет"


class ProductInput(BaseModel):
    name: str | None = None
    manufacturer: str | None = None
    specs: dict[str, str] = Field(default_factory=dict)
    description: str | None = None
    url: str | None = None

    @field_validator("name", "manufacturer", "description", "url", mode="before")
    @classmethod
    def _clean_text(cls, v):
        if v is None:
            return None
        return str(v).strip() or None

    @field_validator("specs", mode="before")
    @classmethod
    def _clean_specs(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("specs должен быть объектом вида {название: значение}")
        cleaned = {}
        for key, value in v.items():
            key, value = str(key).strip(), "" if value is None else str(value).strip()
            if key and value:
                cleaned[key] = value
        return cleaned


class Spec(BaseModel):
    name: str
    value: str


class ProductCard(BaseModel):
    seo_title: str
    seo_description: str
    key_specs: list[Spec]
    search_queries: list[str]
    manager_block: str
    missing_info: list[str] = Field(default_factory=list)


class MissingField(BaseModel):
    key: str
    label: str


class GenerateRequest(BaseModel):
    raw: str
    extra: ProductInput | None = None
    force: bool = False


class GenerateResponse(BaseModel):
    status: Literal["ok", "needs_more_data"]
    product_class: str | None = None
    missing_fields: list[MissingField] = Field(default_factory=list)
    product: ProductInput | None = None
    card: ProductCard | None = None
    warnings: list[str] = Field(default_factory=list)
