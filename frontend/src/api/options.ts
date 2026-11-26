import client from "./client";
import type {
  OptionCandidatesOut,
  OptionDeleteOut,
  OptionImportOut,
  OptionIn,
  OptionOut,
  ReferencesOut,
} from "./contract";

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

export interface OptionItem extends OptionOut {}

/** 一次取回六类候选（启用且未删除）。 */
export async function fetchCandidates(): Promise<
  Record<OptionKind, OptionItem[]>
> {
  const { data } = await client.get<OptionCandidatesOut>(
    "/options/candidates",
  );
  return data.kinds as Record<OptionKind, OptionItem[]>;
}

/**
 * 管理列表（admin）：**不含已软删除的项**——服务端在请求时就过滤掉了，
 * 页面上永远看不到被删除的数据。
 */
export async function listOptions(kind: OptionKind): Promise<OptionItem[]> {
  const { data } = await client.get<{ items: OptionItem[] }>(
    `/options/${kind}`,
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

/**
 * 批量导入：上传表头为 code 与标签列的 CSV，按 code upsert
 * （已存在则更新标签，不存在则新增）。
 * 费用代码表的标签列是 description，其余五类是 name。
 */
export async function importOptions(
  kind: OptionKind,
  file: File,
): Promise<OptionImportOut> {
  const form = new FormData();
  form.append("file", file);
  // FormData 的 Content-Type 交给浏览器设，不能手动写死 boundary
  const { data } = await client.post<OptionImportOut>(
    `/options/${kind}/import`,
    form,
  );
  return data;
}

/** 删除前的引用数量预检：用于在真正删除前告知管理员。 */
export async function fetchOptionReferences(
  kind: OptionKind,
  id: number,
): Promise<number> {
  const { data } = await client.get<ReferencesOut>(
    `/options/${kind}/${id}/references`,
  );
  return data.referenced;
}

/** 删除并返回删除前的引用数量。 */
export async function deleteOption(
  kind: OptionKind,
  id: number,
): Promise<OptionDeleteOut> {
  const { data } = await client.delete<OptionDeleteOut>(
    `/options/${kind}/${id}`,
  );
  return data;
}
