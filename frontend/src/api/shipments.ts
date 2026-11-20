import client from "./client";

export type Lifecycle = "draft" | "confirmed" | "completed" | "cancelled";

export interface ShipmentListItem {
  id: number;
  shipment_num: string;
  lifecycle: Lifecycle;
  status: number;
  operator: string | null;
  created_at: string | null;
  updated_at: string | null;
  charge_info_count: number;
}

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
): Promise<Page<ShipmentListItem>> {
  const { data } = await client.get<Page<ShipmentListItem>>("/shipments", {
    params,
  });
  return data;
}

export interface CreateShipmentIn {
  shipment_num: string;
}

export interface ShipmentDetail {
  id: number;
  shipment_num: string;
  lifecycle: string;
  status: number;
  operator: string | null;
  created_at: string | null;
  updated_at: string | null;
  charge_info_count?: number;
}

export async function fetchShipment(id: number): Promise<ShipmentDetail> {
  const { data } = await client.get<ShipmentDetail>(`/shipments/${id}`);
  return data;
}

export async function createShipment(body: CreateShipmentIn) {
  const { data } = await client.post("/shipments", body);
  return data;
}

export async function updateShipment(id: number, body: CreateShipmentIn) {
  const { data } = await client.patch(`/shipments/${id}`, body);
  return data;
}

export async function deleteShipment(id: number) {
  const { data } = await client.delete(`/shipments/${id}`);
  return data;
}

export async function transitionShipment(
  id: number,
  action: "confirm" | "complete" | "cancel",
) {
  const { data } = await client.post(`/shipments/${id}/${action}`);
  return data;
}
