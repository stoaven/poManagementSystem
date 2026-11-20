/**
 * 字段名映射表：中文标签 -> 上游英文字段名。
 *
 * 英文取上游表结构的原名（Shipment No. / Charge Code / OS Cost Amt …），
 * 这样界面上看到的英文就是上游表里的列名，与上游核对时不必来回翻译。
 * 上游没有对应字段的（状态、操作人等）用自然英文名。
 *
 * 两张表：
 * - FIELD_NAMES：驼峰字段名 -> 英文名，给按接口字段取值的地方用
 * - LABEL_EN：中文标签 -> 英文名，给 BilingualLabel 的默认回退用
 * 同一个英文名可能对应多个中文标签（如「部门」与「应付部门」都是 Department），
 * 所以只有 FIELD_NAMES 要求取值互不重复。
 */
export const FIELD_NAMES: Record<string, string> = {
  // 货运订单
  shipmentNum: "Shipment No.",
  lifecycle: "Status",
  // 费用信息 · 通用
  chargeCode: "Charge Code",
  jobNum: "Job No.",
  // 费用信息 · 应付侧
  department: "Department",
  branch: "Branch",
  costCurrency: "Cost Currency",
  osCostAmt: "OS Cost Amt",
  creditor: "Creditor",
  // 费用信息 · 应收侧
  sellCurrency: "Sell Currency",
  osSellAmt: "OS Sell Amt",
  debtor: "Debtor",
  // 列表通用
  operator: "Operator",
  createdAt: "Created At",
  updatedAt: "Updated At",
  actions: "Actions",
  // 用户
  phone: "Phone",
  username: "Username",
  authority: "Authority",
  // 选项
  code: "Code",
  name: "Name",
  referenced: "Referenced",
  isActive: "Active",
  deleted: "Deleted",
  // 列表页
  chargeInfoCount: "Charge Info",
  costTotals: "Payable Total",
  sellTotals: "Receivable Total",
};

/** 中文标签 -> 上游英文名，供 BilingualLabel 在未显式传 en 时回退。 */
export const LABEL_EN: Record<string, string> = {
  // 货运订单
  货运订单号: "Shipment No.",
  业务状态: "Status",
  状态: "Status",
  操作人: "Operator",
  创建时间: "Created At",
  更新时间: "Updated At",
  操作: "Actions",
  // 费用信息
  费用信息: "Charge Info",
  费用代码: "Charge Code",
  费用: "Charge",
  应付: "Payable",
  应收: "Receivable",
  应付部门: "Department",
  部门: "Department",
  应付分支机构: "Branch",
  分支机构: "Branch",
  应付币种: "Cost Currency",
  应收币种: "Sell Currency",
  币种: "Currency",
  应付金额: "OS Cost Amt",
  应收金额: "OS Sell Amt",
  应付对象: "Creditor",
  应收对象: "Debtor",
  应付合计: "Payable Total",
  应收合计: "Receivable Total",
  // 选项
  代码: "Code",
  名称: "Name",
  被引用: "Referenced",
  启用: "Active",
  停用: "Inactive",
  已删除: "Deleted",
  // 用户
  手机号: "Phone",
  用户名称: "Username",
  权限: "Authority",
};

/** 取英文字段名；既认驼峰字段名，也认中文标签，都没有时回退到原值。 */
export function fieldName(key: string): string {
  return FIELD_NAMES[key] ?? LABEL_EN[key] ?? key;
}
