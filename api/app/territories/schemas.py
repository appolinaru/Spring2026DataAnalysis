"""Pydantic-схемы для территорий и показателей."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TerritoryBase(BaseModel):
    """Базовая схема территории."""

    name: str = Field(..., min_length=1, max_length=255)
    territory_type: str = Field(..., min_length=1, max_length=100)
    level: int = Field(..., ge=0)
    description: str | None = None
    geom_wkt: str = Field(..., description="WKT-строка геометрии MULTIPOLYGON")


class TerritoryCreate(TerritoryBase):
    """Схема создания территории."""


class TerritoryUpdate(BaseModel):
    """Схема обновления территории."""

    name: str | None = Field(None, min_length=1, max_length=255)
    territory_type: str | None = Field(None, min_length=1, max_length=100)
    level: int | None = Field(None, ge=0)
    description: str | None = None
    geom_wkt: str | None = Field(None, description="WKT-строка геометрии")


class TerritoryRead(BaseModel):
    """Схема чтения территории."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    territory_type: str
    level: int
    description: str | None
    geom_wkt: str
    created_at: datetime


class TerritoryMetricCreate(BaseModel):
    """Схема создания показателя."""

    year: int
    population: int | None = None
    area_km2: Decimal | None = None
    source: str | None = None


class TerritoryMetricUpdate(BaseModel):
    """Схема обновления показателя."""

    year: int | None = None
    population: int | None = None
    area_km2: Decimal | None = None
    source: str | None = None


class TerritoryMetricRead(BaseModel):
    """Схема чтения показателя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    territory_id: int
    year: int
    population: int | None
    area_km2: Decimal | None
    source: str | None
    created_at: datetime