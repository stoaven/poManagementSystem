"""删除 related_source_id 列（关联收费用功能已下线）

Revision ID: 26d6fd6760d1
Revises: 35c71130e91b
Create Date: 2026-11-21 21:07:01.309953
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '26d6fd6760d1'
down_revision = '35c71130e91b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 关联收费用功能已下线：这一列不再有人写入，先去外键再去列
    op.drop_constraint('charge_info_ibfk_2', 'charge_info', type_='foreignkey')
    op.drop_column('charge_info', 'related_source_id')


def downgrade() -> None:
    op.add_column('charge_info', sa.Column('related_source_id', mysql.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('charge_info_ibfk_2', 'charge_info', 'charge_info', ['related_source_id'], ['id'])
