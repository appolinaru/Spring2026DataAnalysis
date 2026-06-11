"""CRUD-функции для территорий и показателей."""

from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.territories.models import Territory, TerritoryMetric
from app.territories.schemas import (
    TerritoryCreate,
    TerritoryMetricCreate,
    TerritoryMetricUpdate,
    TerritoryUpdate,
)


def _territory_select():
    """Базовый запрос для выборки территорий с WKT-геометрией."""
    return select(
        Territory.id,
        Territory.name,
        Territory.territory_type,
        Territory.level,
        Territory.description,
        func.ST_AsText(Territory.geom).label("geom_wkt"),
        Territory.created_at,
    )


def get_territory(db: Session, territory_id: int):
    """Получить территорию по ID."""
    stmt = _territory_select().where(Territory.id == territory_id)
    return db.execute(stmt).mappings().first()


def list_territories(db: Session, limit: int = 100, offset: int = 0):
    """Получить список территорий."""
    stmt = _territory_select().order_by(Territory.id).limit(limit).offset(offset)
    return db.execute(stmt).mappings().all()


def create_territory(db: Session, data: TerritoryCreate):
    """Создать территорию."""
    geom = WKTElement(data.geom_wkt, srid=4326)
    territory = Territory(
        name=data.name,
        territory_type=data.territory_type,
        level=data.level,
        description=data.description,
        geom=geom,
    )
    db.add(territory)
    db.commit()
    db.refresh(territory)
    return get_territory(db, territory.id)


def update_territory(db: Session, territory_id: int, data: TerritoryUpdate):
    """Обновить территорию."""
    territory = db.get(Territory, territory_id)
    if territory is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "geom_wkt" in update_data:
        territory.geom = WKTElement(update_data.pop("geom_wkt"), srid=4326)

    for field, value in update_data.items():
        setattr(territory, field, value)

    db.commit()
    db.refresh(territory)
    return get_territory(db, territory.id)


def delete_territory(db: Session, territory_id: int):
    """Удалить территорию."""
    territory = db.get(Territory, territory_id)
    if territory is None:
        return False
    db.delete(territory)
    db.commit()
    return True


def list_intersecting_territories(
    db: Session, wkt: str, limit: int = 100, offset: int = 0
):
    """Найти территории, пересекающиеся с заданной геометрией."""
    search_geom = WKTElement(wkt, srid=4326)
    stmt = (
        _territory_select()
        .where(func.ST_Intersects(Territory.geom, search_geom))
        .order_by(Territory.id)
        .limit(limit)
        .offset(offset)
    )
    return db.execute(stmt).mappings().all()


# CRUD для показателей


def create_metric(db: Session, territory_id: int, data: TerritoryMetricCreate):
    """Создать показатель территории."""
    metric = TerritoryMetric(
        territory_id=territory_id,
        year=data.year,
        population=data.population,
        area_km2=data.area_km2,
        source=data.source,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def list_metrics_by_territory(db: Session, territory_id: int):
    """Получить показатели территории."""
    stmt = (
        select(TerritoryMetric)
        .where(TerritoryMetric.territory_id == territory_id)
        .order_by(TerritoryMetric.year)
    )
    return db.execute(stmt).scalars().all()


def update_metric(db: Session, metric_id: int, data: TerritoryMetricUpdate):
    """Обновить показатель."""
    metric = db.get(TerritoryMetric, metric_id)
    if metric is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(metric, field, value)

    db.commit()
    db.refresh(metric)
    return metric


def delete_metric(db: Session, metric_id: int):
    """Удалить показатель."""
    metric = db.get(TerritoryMetric, metric_id)
    if metric is None:
        return False
    db.delete(metric)
    db.commit()
    return True