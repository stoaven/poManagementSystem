"""导出：把费用信息写成 Excel。

表头用**上游英文字段名**——导出的文件大多是要拿去对账或二次加工的，
英文列名与上游表结构一一对应，粘回去不会有歧义。
"""
from io import BytesIO
from typing import Iterable, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

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

# 金额列（写数字而不是文本，才能在 Excel 里求和与筛选）
AMOUNT_COLUMNS = (6, 7, 8, 11, 12, 13)

# 列宽：按表头长度给个下限，长文本留宽一点
COLUMN_WIDTHS = [14, 28, 14, 12, 14, 16, 14, 15, 16, 14, 14, 17, 15, 18]


def _amount(value) -> Optional[float]:
    """金额写成数字；空值留空（不是 0，免得把「未填写」看成「零」）。"""
    return float(value) if value is not None else None


def build_charge_info_workbook(lines: Iterable[ChargeInfo]) -> bytes:
    """把一组费用信息写成 .xlsx 的字节内容。"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Charge Info"

    ws.append(EXPORT_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for line in lines:
        ws.append([
            line.charge_code,
            line.description,
            line.department,
            line.branch,
            line.cost_currency,
            _amount(line.estimated_cost),
            _amount(line.os_cost_amt),
            _amount(line.local_cost_amt),
            line.creditor,
            line.sell_currency,
            _amount(line.os_sell_amt),
            _amount(line.estimated_revenue),
            _amount(line.local_sell_amt),
            line.debtor,
        ])

    for idx, width in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    for idx in AMOUNT_COLUMNS:
        for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
            for cell in row:
                cell.number_format = "#,##0.00"
    # 首行冻结，滚动时表头始终可见
    ws.freeze_panes = "A2"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_filename(shipment_num: str) -> str:
    """文件名：取货运订单号，去掉文件系统不认的字符。"""
    safe = "".join(c for c in shipment_num if c.isalnum() or c in "-_.").strip()
    safe = safe or "shipment"
    return f"charge-info-{safe}.xlsx"
