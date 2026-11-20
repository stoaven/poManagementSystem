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
  async (error) => {
    const status = error?.response?.status;
    const data = error?.response?.data;
    let message = error?.message || "请求失败";
    if (data && typeof data === "object" && typeof data.detail === "string") {
      message = data.detail;
    } else if (data instanceof Blob) {
      // 导出这类二进制请求，出错时响应体也是 Blob，取出里面的 detail
      try {
        const parsed = JSON.parse(await data.text());
        if (typeof parsed?.detail === "string") {
          message = parsed.detail;
        }
      } catch {
        /* 不是 JSON 就沿用默认文案 */
      }
    }
    if (status === 401) {
      setToken(null);
      if (!location.hash.startsWith("#/login")) {
        location.hash = "#/login";
      }
    }
    return Promise.reject(new Error(message));
  },
);

export default client;
