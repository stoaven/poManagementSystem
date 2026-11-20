<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  createOption,
  deleteOption,
  fetchOptionReferences,
  listOptions,
  OPTION_KIND_LABELS,
  OPTION_KIND_LABELS_EN,
  OPTION_KINDS,
  setOptionActive,
  updateOption,
  type OptionItem,
  type OptionKind,
} from "@/api/options";
import BilingualLabel from "@/components/BilingualLabel.vue";

const kind = ref<OptionKind>("charge_codes");
const items = ref<OptionItem[]>([]);
const loading = ref(false);

const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const form = ref({ code: "", name: "" });
const saving = ref(false);

async function load() {
  loading.value = true;
  try {
    items.value = await listOptions(kind.value, true);
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    loading.value = false;
  }
}

function onKindChange() {
  load();
}

function openCreate() {
  editingId.value = null;
  form.value = { code: "", name: "" };
  dialogVisible.value = true;
}

function openEdit(row: OptionItem) {
  editingId.value = row.id;
  form.value = { code: row.code, name: row.name === row.code ? "" : row.name };
  dialogVisible.value = true;
}

async function onSave() {
  const code = form.value.code.trim();
  if (!code) {
    ElMessage.error("代码必填");
    return;
  }
  saving.value = true;
  try {
    if (editingId.value !== null) {
      await updateOption(kind.value, editingId.value, {
        code,
        name: form.value.name.trim() || null,
      });
      ElMessage.success("已保存");
    } else {
      await createOption(kind.value, {
        code,
        name: form.value.name.trim() || null,
      });
      ElMessage.success("已新增");
    }
    dialogVisible.value = false;
    load();
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    saving.value = false;
  }
}

async function onToggleActive(row: OptionItem) {
  try {
    await setOptionActive(kind.value, row.id, !row.is_active);
    ElMessage.success(row.is_active ? "已停用" : "已启用");
    load();
  } catch (e) {
    ElMessage.error((e as Error).message);
  }
}

/** 删除前先拿到引用数量，提示管理员后再真正删除。 */
async function onDelete(row: OptionItem) {
  let referenced = 0;
  try {
    referenced = await fetchOptionReferences(kind.value, row.id);
  } catch (e) {
    ElMessage.error((e as Error).message);
    return;
  }
  try {
    await ElMessageBox.confirm(
      referenced > 0
        ? `选项 ${row.code} 被 ${referenced} 条费用信息引用，删除后这些记录无法再保存。确认删除？`
        : `确认删除选项 ${row.code}？`,
      "删除确认",
      { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" },
    );
  } catch {
    return; // 用户取消
  }
  try {
    await deleteOption(kind.value, row.id);
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
        <h1 class="page-title">选项维护</h1>
        <p class="page-meta">六类可选值 · 仅管理员可修改</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="openCreate">新增选项</el-button>
      </div>
    </header>

    <div class="tabs">
      <button
        v-for="k in OPTION_KINDS"
        :key="k"
        class="tab"
        :class="{ 'is-on': kind === k }"
        @click="kind = k; onKindChange()"
      >
        <span class="bi-cn">{{ OPTION_KIND_LABELS[k] }}</span>
        <span class="bi-en">{{ OPTION_KIND_LABELS_EN[k] }}</span>
      </button>
    </div>

    <div class="sheet">
      <el-table :data="items" v-loading="loading" style="width: 100%">
        <el-table-column width="140">
          <template #header>
            <BilingualLabel label="代码" en="Code" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.code }}</span>
          </template>
        </el-table-column>
        <el-table-column min-width="160">
          <template #header>
            <BilingualLabel label="名称" en="Name" />
          </template>
          <template #default="{ row }">
            <span>{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column width="110">
          <template #header>
            <BilingualLabel label="状态" en="Status" />
          </template>
          <template #default="{ row }">
            <el-tag
              v-if="row.deleted"
              type="info"
              size="small"
              effect="plain"
            >
              已删除
            </el-tag>
            <el-tag
              v-else-if="row.is_active"
              type="success"
              size="small"
              effect="plain"
            >
              启用
            </el-tag>
            <el-tag v-else type="info" size="small" effect="plain">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column width="100" align="right">
          <template #header>
            <BilingualLabel label="被引用" en="Referenced" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.referenced ?? 0 }}</span>
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
            <BilingualLabel label="更新时间" en="Updated At" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.updated_at?.slice(0, 16) ?? "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column width="190" align="right">
          <template #header>
            <BilingualLabel label="操作" en="Actions" />
          </template>
          <template #default="{ row }">
            <template v-if="!row.deleted">
              <a class="lnk" @click="openEdit(row)">编辑</a>
              <a class="lnk" @click="onToggleActive(row)">
                {{ row.is_active ? "停用" : "启用" }}
              </a>
              <a class="lnk lnk-danger" @click="onDelete(row)">删除</a>
            </template>
            <span v-else class="dim">已删除</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <span class="pager-info">
          共 {{ items.length }} 项 · 删除前会提示被引用的记录数
        </span>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId !== null ? '编辑选项' : '新增选项'"
      width="460px"
      destroy-on-close
    >
      <div class="form">
        <label class="field">
          <BilingualLabel label="代码" en="Code" />
          <el-input
            v-model="form.code"
            :disabled="editingId !== null"
            placeholder="唯一代码，创建后不可修改"
          />
          <span v-if="editingId !== null" class="hint">
            代码一经创建不可修改，只可改名称。
          </span>
        </label>
        <label class="field">
          <BilingualLabel label="名称" en="Name" />
          <el-input v-model="form.name" placeholder="留空时以代码呈现" />
        </label>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
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

.tabs {
  display: flex;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--rule);
  margin-bottom: 16px;
}
.tab {
  font: inherit;
  font-size: 13px;
  padding: 8px 14px 10px;
  background: transparent;
  border: 0;
  border-bottom: 2px solid transparent;
  color: var(--ink-2);
  cursor: pointer;
  margin-bottom: -1px;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.25;
}
.tab .bi-en {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-3);
}
.tab:hover {
  color: var(--ink);
}
.tab.is-on {
  color: var(--ink);
  font-weight: 500;
  border-bottom-color: var(--ink);
}

.sheet {
  background: var(--sheet);
  border: 1px solid var(--rule);
}
.pager {
  padding: 12px 16px;
  border-top: 1px solid var(--rule);
}
.pager-info {
  font-size: 12px;
  color: var(--ink-3);
}

.form {
  display: flex;
  flex-direction: column;
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
