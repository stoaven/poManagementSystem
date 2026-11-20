<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  deleteShipment,
  listShipments,
  type Lifecycle,
  type ShipmentListItem,
} from "@/api/shipments";
import BilingualLabel from "@/components/BilingualLabel.vue";

const router = useRouter();

const LIFECYCLE_LABEL: Record<Lifecycle, string> = {
  draft: "草稿",
  confirmed: "已确认",
  completed: "已完成",
  cancelled: "已取消",
};

const LIFECYCLE_TAG: Record<Lifecycle, string> = {
  draft: "info",
  confirmed: "primary",
  completed: "success",
  cancelled: "info",
};

const items = ref<ShipmentListItem[]>([]);
const total = ref(0);
const loading = ref(false);

const query = reactive({
  keyword: "",
  lifecycle: "",
  page: 1,
  page_size: 20,
});

async function load() {
  loading.value = true;
  try {
    const data = await listShipments({
      keyword: query.keyword || undefined,
      lifecycle: query.lifecycle || undefined,
      page: query.page,
      page_size: query.page_size,
    });
    items.value = data.items;
    total.value = data.total;
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  query.page = 1;
  load();
}

function onReset() {
  query.keyword = "";
  query.lifecycle = "";
  query.page = 1;
  load();
}

async function onDelete(row: ShipmentListItem) {
  try {
    await ElMessageBox.confirm(
      `删除货运订单 ${row.shipment_num}？其下的费用信息将一并不再显示。`,
      "删除确认",
      { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" },
    );
  } catch {
    return; // 用户取消
  }
  try {
    await deleteShipment(row.id);
    ElMessage.success("已删除");
    load();
  } catch (e) {
    ElMessage.error((e as Error).message);
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <header class="page-head">
      <div>
        <h1 class="page-title">货运订单</h1>
        <p class="page-meta">按货运订单号与业务状态检索</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="router.push('/shipments/new')">
          新建货运订单
        </el-button>
      </div>
    </header>

    <form class="filter-band" @submit.prevent="onSearch">
      <label class="f">
        <BilingualLabel label="货运订单号" en="Shipment No." />
        <el-input v-model="query.keyword" placeholder="SH-2026" clearable />
      </label>
      <label class="f">
        <BilingualLabel label="状态" en="Status" />
        <el-select v-model="query.lifecycle" placeholder="全部" clearable>
          <el-option
            v-for="(label, key) in LIFECYCLE_LABEL"
            :key="key"
            :label="label"
            :value="key"
          />
        </el-select>
      </label>
      <div class="f f-btns">
        <el-button type="primary" native-type="submit">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>
    </form>

    <div class="sheet">
      <el-table :data="items" v-loading="loading" style="width: 100%">
        <el-table-column min-width="180">
          <template #header>
            <BilingualLabel label="货运订单号" en="Shipment No." />
          </template>
          <template #default="{ row }">
            <a class="lnk mono" @click="router.push(`/shipments/${row.id}`)">
              {{ row.shipment_num }}
            </a>
          </template>
        </el-table-column>
        <el-table-column width="110" align="right">
          <template #header>
            <BilingualLabel label="费用信息" en="Charge Info" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.charge_info_count }}</span>
          </template>
        </el-table-column>
        <el-table-column width="110">
          <template #header>
            <BilingualLabel label="状态" en="Status" />
          </template>
          <template #default="{ row }">
            <el-tag
              :type="LIFECYCLE_TAG[row.lifecycle as Lifecycle]"
              size="small"
              effect="plain"
            >
              {{ LIFECYCLE_LABEL[row.lifecycle as Lifecycle] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column width="130">
          <template #header>
            <BilingualLabel label="操作人" en="Operator" />
          </template>
          <template #default="{ row }">
            <span class="mono dim">{{ row.operator ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column width="170">
          <template #header>
            <BilingualLabel label="创建时间" en="Created At" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.created_at?.slice(0, 16) ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column width="170">
          <template #header>
            <BilingualLabel label="更新时间" en="Updated At" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.updated_at?.slice(0, 16) ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column width="120" align="right">
          <template #header>
            <BilingualLabel label="操作" en="Actions" />
          </template>
          <template #default="{ row }">
            <a class="lnk lnk-danger" @click="onDelete(row)">删除</a>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <span class="pager-info">共 {{ total }} 条 · 每页 {{ query.page_size }} 条</span>
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.page_size"
          :total="total"
          layout="prev, pager, next"
          background
          @current-change="load"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.page-meta {
  margin: 5px 0 0;
  font-size: 12.5px;
  color: var(--ink-3);
}

.filter-band {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 14px 18px;
  padding: 16px 18px;
  background: var(--sheet);
  border: 1px solid var(--rule);
  border-bottom: 0;
}
.f {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 170px;
}
.f-btns {
  flex-direction: row;
  gap: 8px;
  margin-left: auto;
  min-width: 0;
}

.sheet {
  background: var(--sheet);
  border: 1px solid var(--rule);
}
.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--rule);
}
.pager-info {
  font-size: 12px;
  color: var(--ink-3);
}

.lnk {
  color: var(--ink-2);
  text-decoration: none;
  margin-left: 12px;
  font-size: 13px;
  border-bottom: 1px solid transparent;
  cursor: pointer;
}
.lnk:first-child {
  margin-left: 0;
}
.lnk:hover {
  color: var(--ink);
  border-bottom-color: var(--ink-3);
}
.lnk-danger:hover {
  color: var(--pay);
  border-bottom-color: var(--pay);
}
</style>
