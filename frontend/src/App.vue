<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useOptionsStore } from "@/stores/options";

const auth = useAuthStore();
const options = useOptionsStore();
const route = useRoute();
const router = useRouter();

onMounted(async () => {
  // 已有令牌时先取回当前用户，权限判定才准确
  await auth.restore();
});

/**
 * 候选（费用代码、部门、币种……）在登录成功后取一次。
 *
 * 之前只在应用启动、且已经有令牌时取——于是「首次登录」与「令牌过期后
 * 重新登录」这两种情况下都没取过，录入页里的下拉框是空的。
 * 盯住当前用户：登录成功会写入用户信息，这个 watch 就会补取一次。
 */
watch(
  () => auth.user?.id ?? null,
  async (userId) => {
    if (userId === null) {
      return;
    }
    try {
      await options.ensureLoaded();
    } catch {
      // 取不到就先不取：进录入页时还会再试一次
    }
  },
  { immediate: true },
);

function logout() {
  auth.logout();
  router.push("/login");
}
</script>

<template>
  <div v-if="route.name === 'login'" class="login-shell">
    <RouterView />
  </div>

  <div v-else class="app-shell">
    <aside class="rail">
      <div class="rail-brand">
        <span class="brand-mark">运</span>
        <span class="brand-text">货运订单<br />费用管理</span>
      </div>
      <nav class="rail-nav">
        <RouterLink class="rail-item" to="/shipments">
          <span class="rail-icon">运</span>
          <span>货运订单</span>
        </RouterLink>
        <RouterLink
          v-if="auth.isAdmin"
          class="rail-item"
          to="/options"
        >
          <span class="rail-icon">选</span>
          <span>选项维护</span>
        </RouterLink>
        <RouterLink v-if="auth.isAdmin" class="rail-item" to="/users">
          <span class="rail-icon">用</span>
          <span>用户管理</span>
        </RouterLink>
      </nav>
      <div class="rail-foot">
        <div class="who">
          <span class="who-name">{{ auth.user?.username ?? "—" }}</span>
          <span class="who-role">
            {{ auth.isAdmin ? "管理员" : "普通用户" }}
          </span>
        </div>
        <button class="linkish" @click="logout">退出登录</button>
      </div>
    </aside>

    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.login-shell {
  min-height: 100%;
  display: grid;
  place-items: center;
  padding: 32px 20px;
}

.app-shell {
  display: flex;
  min-height: 100%;
}

/* ---- 装订边 ---- */
.rail {
  flex: 0 0 208px;
  background: var(--spine);
  border-right: 1px solid var(--rule);
  display: flex;
  flex-direction: column;
  padding: 26px 0 20px;
}

.rail-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  margin-bottom: 30px;
}

.brand-mark {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  display: grid;
  place-items: center;
  border: 1px solid var(--ink);
  border-radius: 2px;
  font-size: 15px;
  font-weight: 600;
}

.brand-text {
  font-size: 12px;
  line-height: 1.35;
  color: var(--ink-2);
}

.rail-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  font-size: 13.5px;
  color: var(--ink-2);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: background-color 0.12s ease, color 0.12s ease;
}

.rail-item:hover {
  color: var(--ink);
  background: rgba(255, 255, 255, 0.55);
}

.rail-item.router-link-active {
  color: var(--ink);
  background: var(--sheet);
  border-left-color: var(--ink);
  font-weight: 500;
}

.rail-icon {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  font-size: 11px;
  border: 1px solid currentColor;
  border-radius: 2px;
  opacity: 0.7;
}

.rail-foot {
  margin-top: auto;
  padding: 16px 20px 0;
  border-top: 1px solid var(--rule);
}

.who {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.who-name {
  font-size: 13.5px;
  font-weight: 500;
}

.who-role {
  font-size: 11px;
  color: var(--ink-3);
}

.linkish {
  margin-top: 6px;
  padding: 0;
  background: none;
  border: 0;
  font: inherit;
  font-size: 12px;
  color: var(--ink-3);
  cursor: pointer;
  border-bottom: 1px solid transparent;
}

.linkish:hover {
  color: var(--ink);
  border-bottom-color: var(--ink-3);
}

.main {
  flex: 1;
  min-width: 0;
  padding: 30px 34px 48px;
}

@media (max-width: 1080px) {
  .rail {
    flex-basis: 62px;
  }
  .brand-text,
  .rail-item span:not(.rail-icon),
  .who {
    display: none;
  }
  .rail-brand {
    justify-content: center;
    padding: 0;
  }
  .rail-item {
    justify-content: center;
    padding: 11px 0;
  }
  .main {
    padding: 22px 20px 40px;
  }
}
</style>
