import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import ElementPlus from "element-plus";
import { createPinia } from "pinia";
import App from "@/App.vue";
import { useAuthStore } from "@/stores/auth";
import { setToken } from "@/api/client";

const fetchCandidates = vi.fn();
const fetchMe = vi.fn();

vi.mock("@/api/options", async () => {
  const actual = await vi.importActual<typeof import("@/api/options")>(
    "@/api/options",
  );
  return {
    ...actual,
    fetchCandidates: (...args: unknown[]) => fetchCandidates(...args),
  };
});

vi.mock("@/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/api/auth")>(
    "@/api/auth",
  );
  return { ...actual, fetchMe: (...args: unknown[]) => fetchMe(...args) };
});

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ name: "shipments", params: {} }),
}));

const USER = {
  id: 1,
  phone: "13800000001",
  username: "管理员",
  authority: "admin" as const,
};

const EMPTY_KINDS = {
  charge_codes: [],
  departments: [],
  branches: [],
  currencies: [],
  creditors: [],
  debtors: [],
};

beforeEach(() => {
  vi.clearAllMocks();
  setToken(null);
  fetchCandidates.mockResolvedValue(EMPTY_KINDS);
});

function mountApp() {
  return mount(App, {
    global: {
      plugins: [ElementPlus, createPinia()],
      stubs: { RouterView: true, RouterLink: true },
    },
  });
}

describe("应用启动后的候选加载", () => {
  it("启动时就有有效令牌：取一次候选", async () => {
    // 浏览器里存着上次登录的令牌
    setToken("saved-token");
    fetchMe.mockResolvedValue(USER);
    mountApp();
    await flushPromises();
    expect(fetchCandidates).toHaveBeenCalledTimes(1);
  });

  it("首次登录：登录成功后补取候选（此前下拉是空的）", async () => {
    // 没有令牌 → restore 直接返回，登录前不该取候选
    fetchMe.mockRejectedValue(new Error("未登录"));
    mountApp();
    await flushPromises();
    expect(fetchCandidates).not.toHaveBeenCalled();

    // 模拟登录成功：登录接口会写入当前用户
    const auth = useAuthStore();
    auth.user = { ...USER };
    await flushPromises();
    expect(fetchCandidates).toHaveBeenCalledTimes(1);
  });

  it("令牌失效后重新登录：候选会重新取一次", async () => {
    // 启动时令牌还在，但已经过期 → 登录态被清掉
    setToken("expired-token");
    fetchMe.mockRejectedValue(new Error("令牌已失效"));
    mountApp();
    await flushPromises();
    expect(fetchCandidates).not.toHaveBeenCalled();

    const auth = useAuthStore();
    auth.user = { ...USER };
    await flushPromises();
    expect(fetchCandidates).toHaveBeenCalledTimes(1);
  });
});
