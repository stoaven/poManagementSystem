import client from "./client";

export interface ChargeInfo {
  id: number;
  shipment_id: number;
  job_num: string;
  charge_code: string;
  department: string;
  branch: string;
  cost_currency: string | null;
  os_cost_amt: string | null;
  creditor: string | null;
  sell_currency: string | null;
  os_sell_amt: string | null;
  debtor: string | null;
  related_source_id: number | null;
  operator: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/** 创建时的必填载荷；编辑时同一结构但字段可选。 */
export interface ChargeInfoIn {
  charge_code: string;
  department: string;
  branch: string;
  cost_currency: string | null;
  os_cost_amt: string | null;
  creditor: string | null;
  sell_currency: string | null;
  os_sell_amt: string | null;
  debtor: string | null;
}

export interface ShipmentDetail {
  id: number;
  shipment_num: string;
  lifecycle: string;
  status: number;
  operator: string | null;
  created_at: string | null;
  updated_at: string | null;
  charge_info: ChargeInfo[];
  cost_totals: CurrencyTotal[];
  sell_totals: CurrencyTotal[];
}

export interface CurrencyTotal {
  currency: string;
  amount: string;
}

export async function fetchShipment(id: number): Promise<ShipmentDetail> {
  const { data } = await client.get<ShipmentDetail>(`/shipments/${id}`);
  return data;
}

export async function createChargeInfo(
  shipmentId: number,
  body: ChargeInfoIn,
): Promise<ChargeInfo> {
  const { data } = await client.post<ChargeInfo>(
    `/shipments/${shipmentId}/charge-infos`,
    body,
  );
  return data;
}

export async function updateChargeInfo(
  id: number,
  body: Partial<ChargeInfoIn>,
): Promise<ChargeInfo> {
  const { data } = await client.patch<ChargeInfo>(`/charge-infos/${id}`, body);
  return data;
}

export async function deleteChargeInfo(id: number) {
  const { data } = await client.delete(`/charge-infos/${id}`);
  return data;
}

/** 由源记录生成一条关联费用信息。 */
export async function createRelatedChargeInfo(id: number): Promise<ChargeInfo> {
  const { data } = await client.post<ChargeInfo>(`/charge-infos/${id}/related`);
  return data;
}
