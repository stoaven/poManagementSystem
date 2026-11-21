<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  deleteChargeInfo,
  fetchShipment,
  type ChargeInfo,
  type ShipmentDetail,
} from "@/api/chargeInfos";
import { deleteShipment, exportChargeInfos } from "@/api/shipments";
import { displayMoney } from "@/utils/money";
import BilingualLabel from "@/components/BilingualLabel.vue";
import ChargeInfoDialog from "@/components/ChargeInfoDialog.vue";

const route = useRoute();
const router = useRouter();

const LIFECYCLE_LABEL: Record<string, string> = {
  draft: "草稿",
  confirmed: "已确认",
  completed: "已完成",
  cancelled: "已取消",
};

const detail = ref<ShipmentDetail | null>(null);
const loading = ref(false);

const dialogVisible = ref(false);
const editing = ref<ChargeInfo | null>(null);

async function load() {
  loading.value = true;
  try {
    detail.value = await fetchShipment(Number(route.params.id));
  } catch (e) {
    // 清掉上一张单的数据：否则订单不存在时会一直显示别人的单
    detail.value = null;
    ElMessage.error((e as Error).message);
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editing.value = null;
  dialogVisible.value = true;
}

function openEdit(row: ChargeInfo) {
  editing.value = row;
  dialogVisible.value = true;
}

async function onDeleteCharge(row: ChargeInfo) {
  try {
    await ElMessageBox.confirm("删除这条费用信息？", "删除确认", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  try {
    await deleteChargeInfo(row.id);
    ElMessage.success("已删除");
    load();
  } catch (e) {
    ElMessage.error((e as Error).message);
  }
}


/** 导出该订单的全部费用信息为 Excel（英文表头）。 */
async function onExport() {
  if (!detail.value) {
    return;
  }
  try {
    const blob = await exportChargeInfos(detail.value.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `charge-info-${detail.value.shipment_num}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    ElMessage.success("已导出 Excel");
  } catch (e) {
    ElMessage.error((e as Error).message);
  }
}

async function onDeleteShipment() {
  if (!detail.value) {
    return;
  }
  try {
    await ElMessageBox.confirm(
      `删除货运订单 ${detail.value.shipment_num}？其下的费用信息将一并不再显示。`,
      "删除确认",
      { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  try {
    await deleteShipment(detail.value.id);
    ElMessage.success("已删除");
    router.push("/shipments");
  } catch (e) {
    ElMessage.error((e as Error).message);
  }
}

onMounted(load);

/**
 * 切换到另一个订单时重新加载——同一个路由组件会被复用，
 * 只在 onMounted 里取数的话，从 A 单跳到 B 单会一直显示 A 单的数据。
 */
watch(() => route.params.id, load);
</script>

<template>
  <div class="page" v-loading="loading">
    <p v-if="!loading && !detail" class="empty-note">
      该货运订单不存在，或已被删除。
    </p>
    <header class="page-head">
      <div class="doc">
        <p class="doc-kicker">货运订单</p>
        <h1 class="doc-no">
          <span class="mono">{{ detail?.shipment_num ?? "—" }}</span>
          <el-tag
            v-if="detail"
            :type="detail.lifecycle === 'completed' ? 'success' : 'primary'"
            size="small"
            effect="plain"
          >
            {{ LIFECYCLE_LABEL[detail.lifecycle] }}
          </el-tag>
        </h1>
        <div class="doc-meta">
          <span class="kv">
            <span class="kv-k"><BilingualLabel label="业务日期" en="Business Date" /></span>
            <span class="kv-v mono">{{ detail?.created_at?.slice(0, 10) ?? "—" }}</span>
          </span>
          <span class="kv">
            <span class="kv-k"><BilingualLabel label="操作人" en="Operator" /></span>
            <span class="kv-v mono">{{ detail?.operator ?? "—" }}</span>
          </span>
          <span class="kv">
            <span class="kv-k"><BilingualLabel label="创建时间" en="Created At" /></span>
            <span class="kv-v mono">{{ detail?.created_at?.slice(0, 16) ?? "—" }}</span>
          </span>
          <span class="kv">
            <span class="kv-k"><BilingualLabel label="更新时间" en="Updated At" /></span>
            <span class="kv-v mono">{{ detail?.updated_at?.slice(0, 16) ?? "—" }}</span>
          </span>
        </div>
      </div>
      <div class="page-actions">
        <el-button @click="router.push('/shipments')">返回列表</el-button>
        <el-button
          v-if="detail"
          @click="router.push(`/shipments/${detail.id}/edit`)"
        >
          编辑订单
        </el-button>
        <el-button type="danger" plain @click="onDeleteShipment">
          删除订单
        </el-button>
      </div>
    </header>

    <!-- 费用信息表 -->
    <div class="sheet">
      <div class="sheet-head">
        <h2 class="sheet-title"><BilingualLabel label="费用信息" en="Charge Info" /></h2>
        <div class="sheet-actions">
          <el-button :disabled="!detail?.charge_info?.length" @click="onExport">
            导出 Excel
          </el-button>
          <el-button type="primary" @click="openCreate">新增费用信息</el-button>
        </div>
      </div>

      <el-table :data="detail?.charge_info ?? []" style="width: 100%">
        <el-table-column width="110">
          <template #header>
            <BilingualLabel label="费用代码" en="Charge Code" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.charge_code }}</span>
          </template>
        </el-table-column>

        <!-- 应付带 -->
        <el-table-column width="78">
          <template #header>
            <BilingualLabel label="部门" en="Department" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.department }}</span>
          </template>
        </el-table-column>
        <el-table-column width="90">
          <template #header>
            <BilingualLabel label="分支机构" en="Branch" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.branch }}</span>
          </template>
        </el-table-column>
        <el-table-column width="110" align="left">
          <template #header>
            <BilingualLabel label="应付币种" en="Cost Currency" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.cost_currency ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column width="114" align="left">
          <template #header>
            <BilingualLabel label="应付金额" en="OS Cost Amt" />
          </template>
          <template #default="{ row }">
            <span class="amt amt-pay">{{ displayMoney(row.os_cost_amt) }}</span>
          </template>
        </el-table-column>
        <el-table-column min-width="130">
          <template #header>
            <BilingualLabel label="应付对象" en="Creditor" />
          </template>
          <template #default="{ row }">
            <span>{{ row.creditor ?? "—" }}</span>
          </template>
        </el-table-column>

        <!-- 应收带 -->
        <el-table-column width="110" align="left">
          <template #header>
            <BilingualLabel label="应收币种" en="Sell Currency" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.sell_currency ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column width="114" align="left">
          <template #header>
            <BilingualLabel label="应收金额" en="OS Sell Amt" />
          </template>
          <template #default="{ row }">
            <span class="amt amt-rec">{{ displayMoney(row.os_sell_amt) }}</span>
          </template>
        </el-table-column>
        <el-table-column min-width="130">
          <template #header>
            <BilingualLabel label="应收对象" en="Debtor" />
          </template>
          <template #default="{ row }">
            <span>{{ row.debtor ?? "—" }}</span>
          </template>
        </el-table-column>

        <el-table-column width="330" align="right">
          <template #header>
            <BilingualLabel label="操作" en="Actions" />
          </template>
          <template #default="{ row }">
            <a class="lnk" @click="openEdit(row)">编辑</a>
            <a class="lnk lnk-danger" @click="onDeleteCharge(row)">删除</a>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <ChargeInfoDialog
      v-model="dialogVisible"
      :shipment-id="Number(route.params.id)"
      :charge-info="editing"
      @saved="load"
    />
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}
.doc-kicker {
  margin: 0 0 4px;
  font-size: 11.5px;
  color: var(--ink-3);
  letter-spacing: 0.1em;
}
.doc-no {
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 25px;
  font-weight: 500;
}
.doc-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 28px;
}
.kv {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 12.5px;
}
.kv-k {
  color: var(--ink-3);
}
.page-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
/*
 * Element Plus 给相邻按钮自带 12px 左边距，与 flex 的 gap 叠加会让
 * 间距忽宽忽窄（中间插了 .flow 的地方尤其明显）——这里统一由 gap 决定。
 */
.page-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

/* ---- 表格 ---- */
.sheet {
  background: var(--sheet);
  border: 1px solid var(--rule);
}
.empty-note {
  margin: 0 0 16px;
  padding: 12px 16px;
  border: 1px solid var(--rule);
  background: var(--sheet);
  border-radius: 3px;
  color: var(--ink-2);
  font-size: 13px;
}
.sheet-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 18px;
  border-bottom: 1px solid var(--rule);
}
.sheet-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.hint {
  font-size: 11.5px;
  color: var(--ink-3);
}
.band {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  padding: 2px 8px;
  border-radius: 2px;
}
.band-pay {
  color: var(--pay);
  background: var(--pay-wash);
  border: 1px solid var(--pay-rule);
}
.band-rec {
  color: var(--rec);
  background: var(--rec-wash);
  border: 1px solid var(--rec-rule);
}
.amt-pay {
  color: var(--pay);
  font-weight: 500;
}
.amt-rec {
  color: var(--rec-amt);
  font-weight: 500;
}
.amt {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
.cur {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  border: 1px solid var(--rule);
  border-radius: 2px;
  padding: 1px 3px;
  margin-right: 4px;
}
.tag-rel {
  display: inline-block;
  margin-left: 5px;
  padding: 0 4px;
  font-size: 10px;
  color: var(--rec);
  border: 1px solid var(--rec-rule);
  border-radius: 2px;
  background: var(--rec-wash);
}
.lnk {
  color: var(--ink-2);
  text-decoration: none;
  margin-left: 12px;
  font-size: 13px;
  border-bottom: 1px solid transparent;
  cursor: pointer;
}
.lnk:hover {
  color: var(--ink);
  border-bottom-color: var(--ink-3);
}
.lnk-danger:hover {
  color: var(--pay);
  border-bottom-color: var(--pay);
}
.lnk-rel {
  color: var(--rec);
}
.lnk-rel:hover {
  color: var(--rec);
  border-bottom-color: var(--rec);
}
</style>
