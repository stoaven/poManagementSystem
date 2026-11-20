import { describe, expect, it } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { router } from "@/router";
import { useAuthStore } from "@/stores/auth";
import { getToken, setToken } from "@/api/client";

describe("路由守卫", () => {
  it("未登录访问业务路由跳登录页", async () => {
    setToken(null);
    setActivePinia(createPinia());
    await router.push("/shipments");
    expect(router.currentRoute.value.path).toBe("/login");
  });

  it("已登录访问登录页跳货运订单列表", async () => {
    setToken("fake-token");
    setActivePinia(createPinia());
    const auth = useAuthStore();
    auth.token = "fake-token";
    // 路由是全局单例：先离开 /login，push 到同一路径才会触发守卫
    await router.push("/shipments");
    await router.push("/login");
    expect(router.currentRoute.value.path).toBe("/shipments");
  });

  it("普通用户访问 admin 页面被拦回列表", async () => {
    setToken("fake-token");
    setActivePinia(createPinia());
    const auth = useAuthStore();
    auth.token = "fake-token";
    auth.user = {
      id: 2,
      phone: "13900000002",
      username: "普通用户",
      authority: "normal",
    };
    await router.push("/users");
    expect(router.currentRoute.value.path).toBe("/shipments");
  });

  it("管理员可以访问 admin 页面", async () => {
    setToken("fake-token");
    setActivePinia(createPinia());
    const auth = useAuthStore();
    auth.token = "fake-token";
    auth.user = {
      id: 1,
      phone: "13800000001",
      username: "管理员",
      authority: "admin",
    };
    await router.push("/users");
    expect(router.currentRoute.value.path).toBe("/users");
  });

  it("令牌读写正常", () => {
    setToken("abc");
    expect(getToken()).toBe("abc");
    setToken(null);
    expect(getToken()).toBeNull();
  });
});
