<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  createUser,
  deleteUser,
  listUsers,
  setUserActive,
  updateUser,
  type UserItem,
} from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import BilingualLabel from "@/components/BilingualLabel.vue";

const auth = useAuthStore();

const items = ref<UserItem[]>([]);
const loading = ref(false);

const query = reactive({ keyword: "", authority: "" });

const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const saving = ref(false);
const form = reactive<{
  phone: string;
  username: string;
  authority: "admin" | "normal";
}>({ phone: "", username: "", authority: "normal" });

async function load() {
  loading.value = true;
  try {
    items.value = await listUsers({
      keyword: query.keyword || undefined,
      authority: query.authority || undefined,
    });
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  load();
}

function onReset() {
  query.keyword = "";
  query.authority = "";
  load();
}

function openCreate() {
  editingId.value = null;
  form.phone = "";
  form.username = "";
  form.authority = "normal";
  dialogVisible.value = true;
}

function openEdit(row: UserItem) {
  editingId.value = row.id;
  form.phone = row.phone;
  form.username = row.username;
  form.authority = row.authority;
  dialogVisible.value = true;
}

async function onSave() {
  if (!/^\d{11}$/.test(form.phone)) {
    ElMessage.error("手机号格式非法（11 位数字）");
    return;
  }
  if (!form.username.trim()) {
    ElMessage.error("用户名称必填");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      phone: form.phone.trim(),
      username: form.username.trim(),
      authority: form.authority,
    };
    if (editingId.value !== null) {
      await updateUser(editingId.value, payload);
      ElMessage.success("已保存");
    } else {
      await createUser(payload);
      ElMessage.success("已新增用户");
    }
    dialogVisible.value = false;
    load();
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    saving.value = false;
  }
}

async function onToggleActive(row: UserItem) {
  try {
    await setUserActive(row.id, !row.is_active);
    ElMessage.success(row.is_active ? "已停用" : "已启用");
    load();
  } catch (e) {
    ElMessage.error((e as Error).message);
  }
}

async function onDelete(row: UserItem) {
  try {
    await ElMessageBox.confirm(
      `删除用户 ${row.username}（${row.phone}）？其已创建的货运订单与费用信息不受影响。`,
      "删除确认",
      { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  try {
    await deleteUser(row.id);
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
        <h1 class="page-title">用户管理</h1>
        <p class="page-meta">手机号是唯一标识 · 仅管理员可见</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="openCreate">新增用户</el-button>
      </div>
    </header>

    <form class="filter-band" @submit.prevent="onSearch">
      <label class="f">
        <BilingualLabel label="手机号 / 用户名称" en="Phone / Username" />
        <el-input v-model="query.keyword" placeholder="关键字" clearable />
      </label>
      <label class="f">
        <BilingualLabel label="权限" en="Authority" />
        <el-select v-model="query.authority" placeholder="全部" clearable>
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="normal" />
        </el-select>
      </label>
      <div class="f f-btns">
        <el-button type="primary" native-type="submit">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </div>
    </form>

    <div class="sheet">
      <el-table :data="items" v-loading="loading" style="width: 100%">
        <el-table-column width="150">
          <template #header>
            <BilingualLabel label="手机号" en="Phone" />
          </template>
          <template #default="{ row }">
            <span class="mono">{{ row.phone }}</span>
          </template>
        </el-table-column>
        <el-table-column width="130">
          <template #header>
            <BilingualLabel label="用户名称" en="Username" />
          </template>
          <template #default="{ row }">
            {{ row.username }}
          </template>
        </el-table-column>
        <el-table-column width="120">
          <template #header>
            <BilingualLabel label="权限" en="Authority" />
          </template>
          <template #default="{ row }">
            <span
              class="role"
              :class="row.authority === 'admin' ? 'role-admin' : 'role-normal'"
            >
              {{ row.authority === "admin" ? "管理员" : "普通用户" }}
            </span>
          </template>
        </el-table-column>
        <el-table-column width="100">
          <template #header>
            <BilingualLabel label="状态" en="Status" />
          </template>
          <template #default="{ row }">
            <el-tag
              :type="row.is_active ? 'success' : 'info'"
              size="small"
              effect="plain"
            >
              {{ row.is_active ? "启用" : "停用" }}
            </el-tag>
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
        <el-table-column width="240" align="right">
          <template #header>
            <BilingualLabel label="操作" en="Actions" />
          </template>
          <template #default="{ row: u }">
            <a class="lnk" @click="openEdit(u)">编辑</a>
            <!-- 不能停用自己：避免系统失去最后一个管理员 -->
            <a
              v-if="u.id === auth.user?.id || u.is_active"
              class="lnk"
              :class="{ 'lnk-mute': u.id === auth.user?.id }"
              @click="u.id === auth.user?.id ? undefined : onToggleActive(u)"
            >
              {{ u.is_active ? "停用" : "启用" }}
            </a>
            <a class="lnk lnk-danger" @click="onDelete(u)">删除</a>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <span class="pager-info">共 {{ items.length }} 人</span>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId !== null ? '编辑用户' : '新增用户'"
      width="460px"
      destroy-on-close
    >
      <div class="form">
        <label class="field">
          <BilingualLabel label="手机号" en="Phone" />
          <el-input
            v-model="form.phone"
            placeholder="11 位手机号"
            maxlength="11"
            inputmode="numeric"
          />
          <span class="hint">手机号是唯一标识，也是登录凭证。</span>
        </label>
        <label class="field">
          <BilingualLabel label="用户名称" en="Username" />
          <el-input v-model="form.username" placeholder="姓名或昵称" />
        </label>
        <label class="field">
          <BilingualLabel label="权限" en="Authority" />
          <el-radio-group v-model="form.authority">
            <el-radio value="admin">管理员</el-radio>
            <el-radio value="normal">普通用户</el-radio>
          </el-radio-group>
          <span class="hint">
            管理员可维护选项与用户；普通用户两者都不行，但都能录入与查看货运订单。
          </span>
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
  min-width: 190px;
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
  padding: 12px 16px;
  border-top: 1px solid var(--rule);
}
.pager-info {
  font-size: 12px;
  color: var(--ink-3);
}

.role {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 2px;
  white-space: nowrap;
}
.role-admin {
  color: var(--pay);
  background: var(--pay-wash);
}
.role-normal {
  color: var(--ink-2);
  background: #f2f4f2;
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
.lnk-mute {
  color: var(--ink-3);
  cursor: not-allowed;
}
.lnk-mute:hover {
  color: var(--ink-3);
  border-bottom-color: transparent;
}
.lnk-danger:hover {
  color: var(--pay);
  border-bottom-color: var(--pay);
}
</style>
