import client from "./client";
import type { Authority } from "./auth";
import type {
  UserIn as UserInContract,
  UserOut as UserOutContract,
} from "./contract";

/** 权限级别在契约里是 string，后端只接受 admin/normal，这里收窄一次。 */
export type UserItem = Omit<UserOutContract, "authority"> & {
  authority: Authority;
};

export type UserIn = Omit<UserInContract, "authority"> & {
  authority: Authority;
};

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
