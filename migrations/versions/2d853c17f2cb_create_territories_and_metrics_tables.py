"""create territories and metrics tables

Revision ID: 2d853c17f2cb
Revises:
Create Date: 2026-06-11 14:52:32.781176
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

revision: str = "2d853c17f2cb"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Включаем расширение PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Таблица территорий
    op.create_table(
        "territories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("territory_type", sa.String(length=100), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column(
            "geom",
            Geometry(
                geometry_type="MULTIPOLYGON",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("level >= 0", name="ck_territories_level_non_negative"),
    )

    # Пространственный индекс
    op.create_index(
        "idx_territories_geom",
        "territories",
        ["geom"],
        postgresql_using="gist",
    )

    # Таблица показателей
    op.create_table(
        "territory_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("territory_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("area_km2", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["territory_id"],
            ["territories.id"],
            name="fk_territory_metrics_territory_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "territory_id",
            "year",
            name="uq_territory_metrics_territory_year",
        ),
    )

    op.create_index(
        "idx_territory_metrics_territory_id",
        "territory_metrics",
        ["territory_id"],
    )

    # Реальные данные по районам Санкт-Петербурга (упрощённые геометрии)
    op.execute(
        """
        INSERT INTO territories (id, name, territory_type, level, geom)
        VALUES
        (
            1,
            'Адмиралтейский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.28 59.92, 30.32 59.92, 30.32 59.95, 30.28 59.95, 30.28 59.92)))',
                4326
            )
        ),
        (
            2,
            'Василеостровский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.20 59.93, 30.28 59.93, 30.28 59.96, 30.20 59.96, 30.20 59.93)))',
                4326
            )
        ),
        (
            3,
            'Выборгский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.32 59.96, 30.40 59.96, 30.40 60.00, 30.32 60.00, 30.32 59.96)))',
                4326
            )
        ),
        (
            4,
            'Калининский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.35 59.98, 30.42 59.98, 30.42 60.02, 30.35 60.02, 30.35 59.98)))',
                4326
            )
        ),
        (
            5,
            'Кировский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.20 59.88, 30.28 59.88, 30.28 59.92, 30.20 59.92, 30.20 59.88)))',
                4326
            )
        ),
        (
            6,
            'Красногвардейский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.40 59.93, 30.48 59.93, 30.48 59.97, 30.40 59.97, 30.40 59.93)))',
                4326
            )
        ),
        (
            7,
            'Московский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.28 59.88, 30.35 59.88, 30.35 59.92, 30.28 59.92, 30.28 59.88)))',
                4326
            )
        ),
        (
            8,
            'Невский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.42 59.88, 30.50 59.88, 30.50 59.93, 30.42 59.93, 30.42 59.88)))',
                4326
            )
        ),
        (
            9,
            'Петроградский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.25 59.95, 30.32 59.95, 30.32 59.98, 30.25 59.98, 30.25 59.95)))',
                4326
            )
        ),
        (
            10,
            'Приморский район',
            'district',
            1,
            ST_GeomFromText(
                'MULTIPOLYGON(((30.15 59.98, 30.25 59.98, 30.25 60.05, 30.15 60.05, 30.15 59.98)))',
                4326
            )
        );
        """
    )

    # Показатели населения по районам (приблизительные данные)
    op.execute(
        """
        INSERT INTO territory_metrics (territory_id, year, population, area_km2, source)
        VALUES
        (1, 2024, 157897, 13.82, 'Федеральная служба государственной статистики'),
        (2, 2024, 203949, 29.65, 'Федеральная служба государственной статистики'),
        (3, 2024, 507123, 115.40, 'Федеральная служба государственной статистики'),
        (4, 2024, 536934, 61.45, 'Федеральная служба государственной статистики'),
        (5, 2024, 334668, 48.50, 'Федеральная служба государственной статистики'),
        (6, 2024, 380632, 56.83, 'Федеральная служба государственной статистики'),
        (7, 2024, 288973, 71.07, 'Федеральная служба государственной статистики'),
        (8, 2024, 466013, 61.77, 'Федеральная служба государственной статистики'),
        (9, 2024, 124874, 24.00, 'Федеральная служба государственной статистики'),
        (10, 2024, 582034, 109.87, 'Федеральная служба государственной статистики');
        """
    )


def downgrade() -> None:
    op.drop_index("idx_territory_metrics_territory_id", table_name="territory_metrics")
    op.drop_table("territory_metrics")

    op.drop_index("idx_territories_geom", table_name="territories")
    op.drop_table("territories")
