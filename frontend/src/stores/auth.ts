import { defineStore } from "pinia";
import { fetchMe, login as apiLogin, type CurrentUser } from "@/api/auth";
import { getToken, setToken } from "@/api/client";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: getToken(),
    user: null as CurrentUser | null,
  }),
  getters: {
    isLoggedIn: (s) => Boolean(s.token),
    isAdmin: (s) => s.user?.authority === "admin",
  },
  actions: {
    async login(phone: string) {
      const res = await apiLogin(phone);
      this.token = res.token;
      this.user = res.user;
      setToken(res.token);
    },
    /** 用已有令牌换取当前用户；令牌失效时清空登录态。 */
    async restore() {
      if (!this.token) {
        return;
      }
      try {
        this.user = await fetchMe();
      } catch {
        this.logout();
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      setToken(null);
    },
  },
});
