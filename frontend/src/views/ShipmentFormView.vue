<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { createShipment, fetchShipment, updateShipment } from "@/api/shipments";
import BilingualLabel from "@/components/BilingualLabel.vue";

const route = useRoute();
const router = useRouter();

const shipmentNum = ref("");
const loading = ref(false);
const saving = ref(false);
const editing = ref(false);

async function onSave() {
  const num = shipmentNum.value.trim();
  if (!num) {
    ElMessage.error("货运订单号必填");
    return;
  }
  saving.value = true;
  try {
    if (editing.value) {
      await updateShipment(Number(route.params.id), { shipment_num: num });
      ElMessage.success("已保存");
    } else {
      const created = await createShipment({ shipment_num: num });
      ElMessage.success("已创建");
      router.push(`/shipments/${created.id}`);
      return;
    }
    router.push("/shipments");
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  const id = route.params.id;
  if (id) {
    editing.value = true;
    loading.value = true;
    try {
      const data = await fetchShipment(Number(id));
      shipmentNum.value = data.shipment_num;
    } catch (e) {
      ElMessage.error((e as Error).message);
    } finally {
      loading.value = false;
    }
  }
});
</script>

<template>
  <div class="page">
    <header class="page-head">
      <div>
        <h1 class="page-title">
          {{ editing ? "编辑货运订单" : "新建货运订单" }}
        </h1>
        <p class="page-meta">
          货运订单号由内部员工从上游采购系统抄录录入
        </p>
      </div>
    </header>

    <div class="sheet sheet-pad" v-loading="loading">
      <div class="form-grid">
        <label class="field">
          <BilingualLabel label="货运订单号" en="Shipment No." />
          <el-input
            v-model="shipmentNum"
            placeholder="例如 SH-20261119-0007"
            maxlength="64"
          />
          <span class="hint">
            全局唯一，比较时忽略大小写与首尾空格。不限制格式，按上游实际单号填写。
          </span>
        </label>
      </div>

      <div class="form-foot">
        <el-button @click="router.back()">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">
          保存
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 22px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.page-meta {
  margin: 5px 0 0;
  font-size: 12.5px;
  color: var(--ink-3);
}
.sheet {
  background: var(--sheet);
  border: 1px solid var(--rule);
  max-width: 720px;
}
.sheet-pad {
  padding: 22px;
}
.form-grid {
  display: grid;
  gap: 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.hint {
  font-size: 12px;
  color: var(--ink-3);
}
.form-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid var(--rule-soft);
}
</style>
