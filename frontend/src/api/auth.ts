import client from "./client";

export type Authority = "admin" | "normal";

export interface CurrentUser {
  id: number;
  phone: string;
  username: string;
  authority: Authority;
}

export interface LoginResponse {
  token: string;
  user: CurrentUser;
}

/** 登录：只需手机号，无密码无验证码。 */
export async function login(phone: string): Promise<LoginResponse> {
  const { data } = await client.post<LoginResponse>("/auth/login", { phone });
  return data;
}

export async function fetchMe(): Promise<CurrentUser> {
  const { data } = await client.get<CurrentUser>("/auth/me");
  return data;
}
