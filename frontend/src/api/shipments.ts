import client from "./client";
import type {
  ShipmentBrief,
  ShipmentDetailOut,
  ShipmentIn,
  ShipmentListOut,
} from "./contract";

export type Lifecycle = "draft" | "confirmed" | "completed" | "cancelled";

/** 列表行，取自契约。 */
export type ShipmentListItem = ShipmentListOut["items"][number];

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ShipmentParams {
  keyword?: string;
  lifecycle?: string;
  page?: number;
  page_size?: number;
}

export async function listShipments(
  params: ShipmentParams = {},
): Promise<ShipmentListOut> {
  const { data } = await client.get<ShipmentListOut>("/shipments", {
    params,
  });
  return data;
}

export async function fetchShipment(id: number): Promise<ShipmentDetailOut> {
  const { data } = await client.get<ShipmentDetailOut>(`/shipments/${id}`);
  return data;
}

export async function createShipment(body: ShipmentIn): Promise<ShipmentBrief> {
  const { data } = await client.post<ShipmentBrief>("/shipments", body);
  return data;
}

export async function updateShipment(
  id: number,
  body: ShipmentIn,
): Promise<ShipmentBrief> {
  const { data } = await client.patch<ShipmentBrief>(`/shipments/${id}`, body);
  return data;
}

export async function deleteShipment(id: number) {
  const { data } = await client.delete(`/shipments/${id}`);
  return data;
}

export async function transitionShipment(
  id: number,
  action: "confirm" | "complete" | "cancel",
): Promise<ShipmentBrief> {
  const { data } = await client.post<ShipmentBrief>(
    `/shipments/${id}/${action}`,
  );
  return data;
}
