"""业务模型：shipments / charge_info / 六张选项表。

分类字段全部为 VARCHAR 内容列，不设指向选项表的外键（design D6/D26）。
六张选项表结构完全相同，用 OptionMixin 共享列定义，显式声明六个类。
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import AuditMixin, User  # noqa: F401


class Shipment(Base, AuditMixin):
    """shipments 表：只有 shipment_num 一个业务字段 + lifecycle 业务状态。"""

    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_num: Mapped[str] = mapped_column(String(64), unique=True)
    lifecycle: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )


class ChargeInfo(Base, AuditMixin):
    """charge_info 表：一条记录同时承载应付侧与应收侧。

    字段口径来自上游费用信息表单（design D30）：
    通用列 job_num / charge_code / description；
    应付列 department / branch / cost_currency / os_cost_amt / creditor；
    应收列 sell_currency / os_sell_amt / debtor；
    折算后金额列 estimated_cost / local_cost_amt / estimated_revenue /
    local_sell_amt——本位币（CNY）才等于原币金额，否则为 0.00。
    """

    __tablename__ = "charge_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"))
    job_num: Mapped[str] = mapped_column(String(64))
    charge_code: Mapped[str] = mapped_column(String(64))
    # 描述：默认取费用代码表里该 code 的描述，页面可改
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    department: Mapped[str] = mapped_column(String(64))
    branch: Mapped[str] = mapped_column(String(64))
    # 以下六个侧字段对关联生成的记录允许为 NULL（未填写的一侧，spec：留空待补）
    cost_currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    os_cost_amt: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    creditor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sell_currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    os_sell_amt: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    debtor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    # 折算后的估算/本地金额：只有本位币才有值
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    local_cost_amt: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    estimated_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    local_sell_amt: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)


class OptionMixin(AuditMixin):
    """六张选项表的公共列。子类补 __tablename__ 与 code 唯一约束。

    「名称」列不在这里：费用代码表用的是 description，其余五类用 name。
    """

    code: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="1")


class NamedOptionMixin(OptionMixin):
    """带「名称」列的选项表（应付部门、分支机构、币种、应付对象、应收对象）。"""

    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class ChargeCode(OptionMixin, Base):
    """费用代码选项表：第二列是 description（描述），不是 name。"""

    __tablename__ = "charge_codes"
    __table_args__ = (UniqueConstraint("code", name="uk_charge_codes_code"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class Department(NamedOptionMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("code", name="uk_departments_code"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class BranchOption(NamedOptionMixin, Base):
    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("code", name="uk_branches_code"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class Currency(NamedOptionMixin, Base):
    __tablename__ = "currencies"
    __table_args__ = (UniqueConstraint("code", name="uk_currencies_code"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class Creditor(NamedOptionMixin, Base):
    __tablename__ = "creditors"
    __table_args__ = (UniqueConstraint("code", name="uk_creditors_code"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class Debtor(NamedOptionMixin, Base):
    __tablename__ = "debtors"
    __table_args__ = (UniqueConstraint("code", name="uk_debtors_code"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
