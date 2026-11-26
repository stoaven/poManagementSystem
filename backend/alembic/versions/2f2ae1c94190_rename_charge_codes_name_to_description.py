"""charge_codes 的 name 列改名为 description

用重命名而不是「加新列 + 删旧列」——后者会丢掉已有的描述内容。

Revision ID: 2f2ae1c94190
Revises: 26d6fd6760d1
Create Date: 2026-11-26 15:56:12.964481
"""
from alembic import op
import sqlalchemy as sa

revision = '2f2ae1c94190'
down_revision = '26d6fd6760d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 费用代码表的第二列叫「描述」，其余五类选项表仍叫「名称」
    op.alter_column(
        'charge_codes', 'name', new_column_name='description',
        existing_type=sa.String(length=200), existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'charge_codes', 'description', new_column_name='name',
        existing_type=sa.String(length=200), existing_nullable=True,
    )
