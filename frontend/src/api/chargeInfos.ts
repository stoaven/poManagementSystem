import client from "./client";
import type {
  ChargeInfoIn,
  ChargeInfoOut,
  ChargeInfoPatch,
  ShipmentDetailOut,
} from "./contract";

/** 费用信息记录：两侧共处一条记录。 */
export type ChargeInfo = ChargeInfoOut;

/** 新建与编辑费用信息的载荷。 */
export type { ChargeInfoIn, ChargeInfoPatch };

/** 详情页要用的订单详情（含费用信息与按币种分组的合计）。 */
export type ShipmentDetail = ShipmentDetailOut;

export async function fetchShipment(id: number): Promise<ShipmentDetail> {
  const { data } = await client.get<ShipmentDetail>(`/shipments/${id}`);
  return data;
}

/**
 * 新增费用信息：一次写入两条——A（应付侧那条）与 B（镜像分支那条）。
 * 返回值就是这两条记录。
 */
export async function createChargeInfo(
  shipmentId: number,
  body: ChargeInfoIn,
): Promise<ChargeInfo[]> {
  const { data } = await client.post<{ items: ChargeInfo[] }>(
    `/shipments/${shipmentId}/charge-infos`,
    body,
  );
  return data.items;
}

export async function updateChargeInfo(
  id: number,
  body: Partial<ChargeInfoPatch>,
): Promise<ChargeInfo> {
  const { data } = await client.patch<ChargeInfo>(`/charge-infos/${id}`, body);
  return data;
}

export async function deleteChargeInfo(id: number) {
  const { data } = await client.delete(`/charge-infos/${id}`);
  return data;
}
