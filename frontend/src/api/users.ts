import client from "./client";
import type { Authority } from "./auth";

export interface UserItem {
  id: number;
  phone: string;
  username: string;
  authority: Authority;
  is_active: boolean;
  status: number;
  operator: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface UserIn {
  phone: string;
  username: string;
  authority: Authority;
}

export async function listUsers(params: {
  keyword?: string;
  authority?: string;
} = {}): Promise<UserItem[]> {
  const { data } = await client.get<{ items: UserItem[] }>("/users", { params });
  return data.items;
}

export async function createUser(body: UserIn): Promise<UserItem> {
  const { data } = await client.post<UserItem>("/users", body);
  return data;
}

export async function updateUser(
  id: number,
  body: UserIn,
): Promise<UserItem> {
  const { data } = await client.patch<UserItem>(`/users/${id}`, body);
  return data;
}

export async function setUserActive(id: number, isActive: boolean) {
  const { data } = await client.patch(`/users/${id}/status`, {
    is_active: isActive,
  });
  return data;
}

export async function deleteUser(id: number) {
  const { data } = await client.delete(`/users/${id}`);
  return data;
}
