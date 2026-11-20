import axios, { type AxiosInstance } from "axios";

const TOKEN_KEY = "shipment_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

const client: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  timeout: 15000,
});

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * 401 = 未登录或令牌失效 -> 跳登录页
 * 403 = 已登录但权限不足 -> 提示，不跳登录（跳了也进不去，体验更差）
 */
client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error?.response?.status;
    const message =
      error?.response?.data?.detail || error?.message || "请求失败";
    if (status === 401) {
      setToken(null);
      if (!location.hash.startsWith("#/login")) {
        location.hash = "#/login";
      }
      return Promise.reject(new Error(message));
    }
    if (status === 403) {
      return Promise.reject(new Error(message));
    }
    return Promise.reject(new Error(message));
  },
);

export default client;
