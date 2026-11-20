import { createRouter, createWebHashHistory } from "vue-router";
import { getToken } from "@/api/client";
import { useAuthStore } from "@/stores/auth";

const routes = [
  { path: "/login", name: "login", component: () => import("@/views/LoginView.vue") },
  {
    path: "/shipments",
    name: "shipments",
    component: () => import("@/views/ShipmentListView.vue"),
  },
  {
    path: "/shipments/new",
    name: "shipment-new",
    component: () => import("@/views/ShipmentFormView.vue"),
  },
  {
    path: "/shipments/:id",
    name: "shipment-detail",
    component: () => import("@/views/ShipmentDetailView.vue"),
  },
  {
    path: "/shipments/:id/edit",
    name: "shipment-edit",
    component: () => import("@/views/ShipmentFormView.vue"),
  },
  {
    path: "/options",
    name: "options",
    component: () => import("@/views/OptionListView.vue"),
    meta: { requiresAdmin: true },
  },
  {
    path: "/users",
    name: "users",
    component: () => import("@/views/UserManagementView.vue"),
    meta: { requiresAdmin: true },
  },
  { path: "/", redirect: "/shipments" },
  { path: "/:pathMatch(.*)*", redirect: "/shipments" },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

/**
 * 路由守卫：
 * - 未登录 -> 跳登录页
 * - 已登录访问登录页 -> 跳货运订单列表
 * - admin-only 页面（选项维护、用户管理）：普通用户被拦回列表
 *
 * 权限判定必须用当前库里的权限（D18：权限实时生效），
 * 因此守卫里先 restore() 一次拿用户信息。
 */
router.beforeEach(async (to) => {
  const auth = useAuthStore();

  if (to.path === "/login") {
    return auth.isLoggedIn ? "/shipments" : true;
  }
  if (!auth.isLoggedIn) {
    return "/login";
  }

  if (to.meta.requiresAdmin) {
    if (!auth.user) {
      await auth.restore();
    }
    if (!auth.isAdmin) {
      return "/shipments";
    }
  }
  return true;
});
