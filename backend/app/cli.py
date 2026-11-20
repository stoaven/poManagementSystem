"""命令行入口：create-admin / seed-options。

- create-admin --phone <手机号> --username <名称>：创建首个管理员（无密码，D17）
- seed-options：预置费用代码/应付部门/应付分支机构/币种四类初始选项
"""
import argparse

from app.core.security import is_valid_phone
from app.db.session import SessionLocal
from app.models import (
    BranchOption,
    ChargeCode,
    Creditor,
    Currency,
    Debtor,
    Department,
    User,
)

# 关联收费用的生成规则会写入 SHO / CNSHL / CNSHO 这三个取值，
# 它们必须同时存在于选项表里，否则生成的记录再编辑保存时会被取值校验拒绝。
SEED = {
    "charge_codes": ["DHLF", "OCUC", "OINSUR"],
    "departments": ["FIS", "FES", "FIA", "FEA"],
    "branches": ["SHL", "SHO"],
    "currencies": ["USD", "CNY", "EUR", "HKD"],
    "creditors": ["CNSHL", "MAERSK", "中远海运物流"],
    "debtors": ["CNSHO", "中远海运集运", "其它客户"],
}
SEED_MODELS = {
    "charge_codes": ChargeCode,
    "departments": Department,
    "branches": BranchOption,
    "currencies": Currency,
    "creditors": Creditor,
    "debtors": Debtor,
}


def create_admin(phone: str, username: str) -> None:
    if not is_valid_phone(phone):
        raise SystemExit("手机号格式非法（11 位数字）")
    db = SessionLocal()
    try:
        if db.query(User).filter(User.phone == phone).first():
            raise SystemExit("该手机号已被使用")
        u = User(phone=phone, username=username, authority="admin",
                 is_active=True, status=0, operator=None)
        db.add(u)
        db.commit()
        print(f"管理员已创建：{phone} / {username}")
    finally:
        db.close()


def seed_options() -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.authority == "admin", User.status == 0).first()
        if not admin:
            raise SystemExit("请先执行 create-admin 创建管理员（operator 外键需要真实用户）")
        for kind, codes in SEED.items():
            m = SEED_MODELS[kind]
            for code in codes:
                if db.query(m).filter(m.code == code).first():
                    continue
                db.add(m(code=code, name=None, is_active=True, status=0,
                         operator=admin.phone))
            print(f"{kind}: 预置 {len(codes)} 项")
        db.commit()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_admin = sub.add_parser("create-admin", help="创建首个管理员账号")
    p_admin.add_argument("--phone", required=True)
    p_admin.add_argument("--username", required=True)

    sub.add_parser("seed-options", help="预置初始选项数据")

    args = parser.parse_args()
    if args.cmd == "create-admin":
        create_admin(args.phone, args.username)
    elif args.cmd == "seed-options":
        seed_options()


if __name__ == "__main__":
    main()
