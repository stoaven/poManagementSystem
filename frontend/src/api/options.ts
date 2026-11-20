import client from "./client";

/** 六类选项的 kind，与后端路由的 {kind} 对应。 */
export type OptionKind =
  | "charge_codes"
  | "departments"
  | "branches"
  | "currencies"
  | "creditors"
  | "debtors";

export const OPTION_KINDS: OptionKind[] = [
  "charge_codes",
  "departments",
  "branches",
  "currencies",
  "creditors",
  "debtors",
];

export const OPTION_KIND_LABELS: Record<OptionKind, string> = {
  charge_codes: "费用代码",
  departments: "应付部门",
  branches: "应付分支机构",
  currencies: "币种",
  creditors: "应付对象",
  debtors: "应收对象",
};

/** 选项页签的英文名（上游字段名），页签中英双语展示。 */
export const OPTION_KIND_LABELS_EN: Record<OptionKind, string> = {
  charge_codes: "Charge Code",
  departments: "Department",
  branches: "Branch",
  currencies: "Currency",
  creditors: "Creditor",
  debtors: "Debtor",
};

export interface OptionItem {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
  deleted: boolean;
  operator: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface OptionIn {
  code: string;
  name?: string | null;
}

/** 一次取回六类候选（启用且未删除）。 */
export async function fetchCandidates(): Promise<
  Record<OptionKind, OptionItem[]>
> {
  const { data } = await client.get<{
    kinds: Record<OptionKind, OptionItem[]>;
  }>("/options/candidates");
  return data.kinds;
}

/** 管理列表（admin）：可含停用与已删除项。 */
export async function listOptions(
  kind: OptionKind,
  includeDeleted = false,
): Promise<OptionItem[]> {
  const { data } = await client.get<{ items: OptionItem[] }>(
    `/options/${kind}`,
    { params: { include_deleted: includeDeleted } },
  );
  return data.items;
}

export async function createOption(kind: OptionKind, body: OptionIn) {
  const { data } = await client.post(`/options/${kind}`, body);
  return data;
}

export async function updateOption(
  kind: OptionKind,
  id: number,
  body: OptionIn,
) {
  const { data } = await client.patch(`/options/${kind}/${id}`, body);
  return data;
}

export async function setOptionActive(
  kind: OptionKind,
  id: number,
  isActive: boolean,
) {
  const { data } = await client.patch(`/options/${kind}/${id}/status`, {
    is_active: isActive,
  });
  return data;
}

/** 删除前的引用数量预检：用于在真正删除前告知管理员。 */
export async function fetchOptionReferences(
  kind: OptionKind,
  id: number,
): Promise<number> {
  const { data } = await client.get<{ referenced: number }>(
    `/options/${kind}/${id}/references`,
  );
  return data.referenced;
}

/** 删除并返回删除前的引用数量。 */
export async function deleteOption(
  kind: OptionKind,
  id: number,
): Promise<{ ok: boolean; referenced: number }> {
  const { data } = await client.delete<{ ok: boolean; referenced: number }>(
    `/options/${kind}/${id}`,
  );
  return data;
}
