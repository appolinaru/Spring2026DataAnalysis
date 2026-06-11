"""ORM-модели территорий и показателей."""

from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db import Base


class Territory(Base):
    """Территория."""

    __tablename__ = "territories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    territory_type: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    geom = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    metrics: Mapped[list["TerritoryMetric"]] = relationship(
        "TerritoryMetric",
        back_populates="territory",
        cascade="all, delete-orphan",
    )


class TerritoryMetric(Base):
    """Показатель территории."""

    __tablename__ = "territory_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    territory_id: Mapped[int] = mapped_column(
        ForeignKey("territories.id", ondelete="CASCADE"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_km2: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=True,
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    territory: Mapped["Territory"] = relationship("Territory", back_populates="metrics")