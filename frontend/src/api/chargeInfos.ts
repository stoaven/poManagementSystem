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
  body: Partial<ChargeInfoPatch>,
): Promise<ChargeInfo> {
  const { data } = await client.patch<ChargeInfo>(`/charge-infos/${id}`, body);
  return data;
}

export async function deleteChargeInfo(id: number) {
  const { data } = await client.delete(`/charge-infos/${id}`);
  return data;
}
