import client from "./client";
import type {
  ChargeInfoDraftOut,
  ChargeInfoIn,
  ChargeInfoOut,
  ChargeInfoPatch,
  ShipmentDetailOut,
} from "./contract";

/** 费用信息记录：两侧共处一条记录，关联生成的一侧可能为空。 */
export type ChargeInfo = ChargeInfoOut;

/** 关联收费用的预填草稿：服务端算好但不落库。 */
export type { ChargeInfoDraftOut };

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

/**
 * 取关联收费用的预填草稿：服务端按规则算好，但**不写库**。
 * 用户在弹窗里补齐未填写的一侧、点确定之后，才通过创建接口落库。
 */
export async function fetchRelatedDraft(
  id: number,
): Promise<ChargeInfoDraftOut> {
  const { data } = await client.get<ChargeInfoDraftOut>(
    `/charge-infos/${id}/related/draft`,
  );
  return data;
}
