<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";
import BilingualLabel from "@/components/BilingualLabel.vue";

const auth = useAuthStore();
const router = useRouter();

const phone = ref("");
const loading = ref(false);

async function onSubmit() {
  if (!/^\d{11}$/.test(phone.value)) {
    ElMessage.error("请输入 11 位手机号");
    return;
  }
  loading.value = true;
  try {
    await auth.login(phone.value);
    ElMessage.success("登录成功");
    router.push("/shipments");
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-sheet">
    <div class="copy-edge" aria-hidden="true">
      <i class="ce ce-pink"></i>
      <i class="ce ce-blue"></i>
      <i class="ce ce-green"></i>
    </div>
    <div class="login-body">
      <p class="org">内部系统 · 货运运营</p>
      <h1 class="login-title">货运订单费用管理</h1>
      <p class="login-sub">录入一笔货运订单的应付与应收</p>

      <form class="login-form" @submit.prevent="onSubmit">
        <label class="field">
          <BilingualLabel label="手机号" en="Phone" />
          <el-input
            v-model="phone"
            placeholder="11 位手机号"
            maxlength="11"
            inputmode="numeric"
            size="large"
          />
        </label>
        <el-button
          type="primary"
          native-type="submit"
          size="large"
          class="login-btn"
          :loading="loading"
        >
          登录
        </el-button>
      </form>

      <p class="login-note">
        账号由管理员开通，输入手机号即可登录。本系统以手机号识别身份，请勿外传同事手机号。
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-sheet {
  width: 100%;
  max-width: 388px;
  background: var(--sheet);
  border: 1px solid var(--rule);
  border-radius: 3px;
  box-shadow:
    0 1px 2px rgb(22 26 25 / 4%),
    0 18px 44px -28px rgb(22 26 25 / 28%);
  overflow: hidden;
}

.copy-edge {
  display: flex;
  height: 4px;
}
.ce {
  flex: 1;
}
.ce-pink {
  background: var(--pay);
}
.ce-blue {
  background: var(--rec);
}
.ce-green {
  background: var(--ok);
}

.login-body {
  padding: 34px 36px 30px;
}

.org {
  margin: 0 0 22px;
  font-size: 12px;
  color: var(--ink-3);
  letter-spacing: 0.04em;
}

.login-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.login-sub {
  margin: 7px 0 26px;
  font-size: 13px;
  color: var(--ink-2);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.login-btn {
  width: 100%;
  margin-top: 4px;
  border-radius: 2px;
  background: var(--ink);
  border-color: var(--ink);
}

.login-btn:hover {
  background: #2c332f;
  border-color: #2c332f;
}

.login-note {
  margin: 22px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--ink-3);
}
</style>
