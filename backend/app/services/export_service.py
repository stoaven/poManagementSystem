"""导出：把费用信息写成 CSV。

表头用**上游英文字段名**——导出的文件大多是要拿去对账或二次加工的，
英文列名与上游表结构一一对应，粘回去不会有歧义。

CSV 带 UTF-8 BOM：Excel 双击打开时中文不乱码（没有 BOM 的话 Excel 会按
本地编码猜，中文常常变乱码）。行尾用 CRLF——RFC 4180 的规定，Excel 也认。
"""
import csv
import io
from decimal import Decimal
from typing import Iterable, List

from app.models import ChargeInfo

# 上游字段名，顺序即列顺序（与详情页表格一致）
EXPORT_HEADERS: List[str] = [
    "Charge Code",
    "Description",
    "Department",
    "Branch",
    "Cost Currency",
    "Estimated Cost",
    "OS Cost Amt",
    "Local Cost Amt",
    "Creditor",
    "Sell Currency",
    "OS Sell Amt",
    "Estimated Revenue",
    "Local Sell Amt",
    "Debtor",
]


def _amount(value) -> str:
    """金额写成不带千分位的数字文本。

    CSV 里没有「数字」这种类型，只有文本——所以不能带千分位逗号，
    否则表格软件会把它当字符串，列就没法求和了。空值留空（不是 0，
    免得把「未填写」看成「零」）。
    """
    if value is None:
        return ""
    return f"{Decimal(value):.2f}"


def build_charge_info_csv(lines: Iterable[ChargeInfo]) -> bytes:
    """把一组费用信息写成 .csv 的字节内容。"""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(EXPORT_HEADERS)
    for line in lines:
        writer.writerow([
            line.charge_code,
            line.description or "",
            line.department,
            line.branch,
            line.cost_currency or "",
            _amount(line.estimated_cost),
            _amount(line.os_cost_amt),
            _amount(line.local_cost_amt),
            line.creditor or "",
            line.sell_currency or "",
            _amount(line.os_sell_amt),
            _amount(line.estimated_revenue),
            _amount(line.local_sell_amt),
            line.debtor or "",
        ])
    # utf-8-sig：带 BOM，Excel 打开中文不乱码
    return buf.getvalue().encode("utf-8-sig")


def export_filename(shipment_num: str) -> str:
    """文件名：取货运订单号，去掉文件系统不认的字符。"""
    safe = "".join(
        c for c in shipment_num if c.isalnum() or c in "-_."
    ).strip()
    safe = safe or "shipment"
    return f"charge-info-{safe}.csv"
