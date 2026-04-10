"""delete cities

Revision ID: aa5fcad56877
Revises: 31949fe07aa3
Create Date: 2026-04-10 21:47:39.229009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa5fcad56877'
down_revision: Union[str, Sequence[str], None] = '31949fe07aa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Сначала удаляем внешний ключ (Constraint)
    # Имя 'forms_city_fkey' взято из вашей ошибки
    op.drop_constraint('forms_city_fkey', 'forms', type_='foreignkey')

    # 2. Изменяем тип колонки city с Integer на String.
    # Добавляем postgresql_using, чтобы база знала, как превратить числа в текст
    op.alter_column('forms', 'city',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=100),
               nullable=True,
               postgresql_using="city::text") # Важно для PostgreSQL

    # 3. Теперь, когда ссылок больше нет, удаляем таблицу
    op.drop_table('cities')


def downgrade() -> None:
    """Откат миграции (на случай ошибки)"""
    # 1. Заново создаем таблицу cities
    op.create_table('cities',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id', name='cities_pkey')
    )
    
    # 2. Возвращаем колонку city к типу INTEGER
    # Внимание: если там записаны названия городов текстом, этот шаг может упасть
    op.alter_column('forms', 'city',
               existing_type=sa.String(length=100),
               type_=sa.INTEGER(),
               postgresql_using="city::integer")

    # 3. Возвращаем Foreign Key
    op.create_foreign_key('forms_city_fkey', 'forms', 'cities', ['city'], ['id'])
