"""charge_info 新增描述与四个折算后金额列

- description：描述，默认取费用代码表里该 code 的描述
- estimated_cost / local_cost_amt：估算成本与本地成本
- estimated_revenue / local_sell_amt：估算收入与本地应收金额
折算规则（design D32）：只有本位币 CNY 才等于原币金额，否则为 0.00。

Revision ID: 3d8f1a6b42c7
Revises: 2f2ae1c94190
Create Date: 2026-11-26 16:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '3d8f1a6b42c7'
down_revision = '2f2ae1c94190'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('charge_info',
                  sa.Column('description', sa.String(length=200), nullable=True))
    op.add_column('charge_info',
                  sa.Column('estimated_cost', sa.Numeric(14, 2), nullable=True))
    op.add_column('charge_info',
                  sa.Column('local_cost_amt', sa.Numeric(14, 2), nullable=True))
    op.add_column('charge_info',
                  sa.Column('estimated_revenue', sa.Numeric(14, 2), nullable=True))
    op.add_column('charge_info',
                  sa.Column('local_sell_amt', sa.Numeric(14, 2), nullable=True))

    # 已有记录按同样的规则回填：本位币才等于原币金额
    op.execute("""
        UPDATE charge_info
        SET estimated_cost = CASE WHEN cost_currency = 'CNY' THEN os_cost_amt ELSE 0 END,
            local_cost_amt = CASE WHEN cost_currency = 'CNY' THEN os_cost_amt ELSE 0 END,
            estimated_revenue = CASE WHEN sell_currency = 'CNY' THEN os_sell_amt ELSE 0 END,
            local_sell_amt = CASE WHEN sell_currency = 'CNY' THEN os_sell_amt ELSE 0 END
    """)

    # 描述从费用代码表带出（表外代码留空）
    op.execute("""
        UPDATE charge_info ci
        JOIN charge_codes cc ON ci.charge_code = cc.code
        SET ci.description = cc.description
    """)


def downgrade() -> None:
    op.drop_column('charge_info', 'local_sell_amt')
    op.drop_column('charge_info', 'estimated_revenue')
    op.drop_column('charge_info', 'local_cost_amt')
    op.drop_column('charge_info', 'estimated_cost')
    op.drop_column('charge_info', 'description')
