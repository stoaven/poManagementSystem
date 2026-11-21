<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import {
  createChargeInfo,
  updateChargeInfo,
  type ChargeInfo,
  type ChargeInfoIn,
  type ChargeInfoPatch,
} from "@/api/chargeInfos";
import { useOptionsStore } from "@/stores/options";
import { isValidMoney } from "@/utils/money";
import BilingualLabel from "@/components/BilingualLabel.vue";
import OptionSelect from "@/components/OptionSelect.vue";

const props = defineProps<{
  modelValue: boolean;
  shipmentId: number;
  /** 传入则为编辑既有记录 */
  chargeInfo?: ChargeInfo | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void;
  (e: "saved"): void;
}>();

const options = useOptionsStore();
const saving = ref(false);

/**
 * 表单状态一律按「可空」处理：编辑时可能只有一侧有值（关联生成的记录），
 * 创建时的完整性由下面的校验把关，提交前再组装成两侧齐备的载荷。
 */
type ChargeInfoForm = { [K in keyof ChargeInfoPatch]-?: string | null };

const form = reactive<ChargeInfoForm>({
  charge_code: "",
  department: "",
  branch: "",
  cost_currency: null,
  os_cost_amt: null,
  creditor: null,
  sell_currency: null,
  os_sell_amt: null,
  debtor: null,
});

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

const isEdit = computed(() => Boolean(props.chargeInfo));
const title = computed(() => (isEdit.value ? "编辑费用信息" : "新增费用信息"));

/** 关联生成的记录可能有一侧为空，编辑时该侧不强制必填。 */
const partialSide = computed(() => {
  const c = props.chargeInfo;
  if (!c) {
    return false;
  }
  return !c.sell_currency || !c.os_sell_amt || !c.debtor;
});

watch(
  () => props.modelValue,
  (open) => {
    if (!open) {
      return;
    }
    const c = props.chargeInfo;
    if (c) {
      form.charge_code = c.charge_code;
      form.department = c.department;
      form.branch = c.branch;
      form.cost_currency = c.cost_currency ?? null;
      form.os_cost_amt = c.os_cost_amt ?? null;
      form.creditor = c.creditor ?? null;
      form.sell_currency = c.sell_currency ?? null;
      form.os_sell_amt = c.os_sell_amt ?? null;
      form.debtor = c.debtor ?? null;
    } else {
      form.charge_code = "";
      form.department = "";
      form.branch = "";
      form.cost_currency = null;
      form.os_cost_amt = null;
      form.creditor = null;
      form.sell_currency = null;
      form.os_sell_amt = null;
      form.debtor = null;
    }
  },
  // 打开时立刻按当前记录（或关联草稿）预填，弹窗若以打开状态挂载也一样
  { immediate: true },
);

function validate(): boolean {
  const required: Array<[keyof ChargeInfoPatch, string]> = [
    ["charge_code", "费用代码"],
    ["department", "应付部门"],
    ["branch", "应付分支机构"],
    ["cost_currency", "应付币种"],
    ["os_cost_amt", "应付金额"],
    ["creditor", "应付对象"],
    ["sell_currency", "应收币种"],
    ["os_sell_amt", "应收金额"],
    ["debtor", "应收对象"],
  ];
  for (const [key, label] of required) {
    const v = form[key];
    if (v === null || v === undefined || String(v).trim() === "") {
      ElMessage.error(`${label}必填`);
      return false;
    }
  }
  if (!isValidMoney(String(form.os_cost_amt))) {
    ElMessage.error("应付金额必须是非负数、最多两位小数");
    return false;
  }
  if (!isValidMoney(String(form.os_sell_amt))) {
    ElMessage.error("应收金额必须是非负数、最多两位小数");
    return false;
  }
  return true;
}

async function onSave() {
  if (!validate()) {
    return;
  }
  saving.value = true;
  try {
    // 校验通过后两侧齐备，组装成创建用的载荷（编辑用同一个载荷即可）
    const payload: ChargeInfoIn = {
      charge_code: String(form.charge_code),
      department: String(form.department),
      branch: String(form.branch),
      cost_currency: String(form.cost_currency),
      os_cost_amt: String(form.os_cost_amt),
      creditor: String(form.creditor),
      sell_currency: String(form.sell_currency),
      os_sell_amt: String(form.os_sell_amt),
      debtor: String(form.debtor),
    };
    if (isEdit.value && props.chargeInfo) {
      await updateChargeInfo(props.chargeInfo.id, payload);
      ElMessage.success("已保存");
    } else {
      const created = await createChargeInfo(props.shipmentId, payload);
      ElMessage.success(`已新增 ${created.length} 条费用信息`);
    }
    visible.value = false;
    emit("saved");
  } catch (e) {
    ElMessage.error((e as Error).message);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="860px"
    destroy-on-close
  >
    <div class="grp">
      <p class="grp-title"><BilingualLabel label="费用" en="Charge" /></p>
      <div class="grid">
        <label class="field">
          <BilingualLabel label="费用代码" en="Charge Code" />
          <OptionSelect kind="charge_codes" v-model="form.charge_code" />
        </label>
      </div>
    </div>

    <div class="grp grp-pay">
      <p class="grp-title"><BilingualLabel label="应付" en="Payable" /></p>
      <div class="grid">
        <label class="field">
          <BilingualLabel label="应付部门" en="Department" />
          <OptionSelect kind="departments" v-model="form.department" />
        </label>
        <label class="field">
          <BilingualLabel label="应付分支机构" en="Branch" />
          <OptionSelect kind="branches" v-model="form.branch" />
        </label>
        <label class="field">
          <BilingualLabel label="应付币种" en="Cost Currency" />
          <OptionSelect kind="currencies" v-model="form.cost_currency" />
        </label>
        <label class="field">
          <BilingualLabel label="应付金额" en="OS Cost Amt" />
          <el-input
            v-model="form.os_cost_amt"
            placeholder="0.00"
            inputmode="decimal"
          />
        </label>
        <label class="field">
          <BilingualLabel label="应付对象" en="Creditor" />
          <OptionSelect kind="creditors" v-model="form.creditor" />
        </label>
      </div>
    </div>

    <div class="grp grp-rec">
      <p class="grp-title"><BilingualLabel label="应收" en="Receivable" /></p>
      <div class="grid">
        <label class="field">
          <BilingualLabel label="应收币种" en="Sell Currency" />
          <OptionSelect kind="currencies" v-model="form.sell_currency" />
        </label>
        <label class="field">
          <BilingualLabel label="应收金额" en="OS Sell Amt" />
          <el-input
            v-model="form.os_sell_amt"
            placeholder="0.00"
            inputmode="decimal"
          />
        </label>
        <label class="field">
          <BilingualLabel label="应收对象" en="Debtor" />
          <OptionSelect kind="debtors" v-model="form.debtor" />
        </label>
      </div>
    </div>

    <p class="note">
      应付与应收两侧的币种各自独立，不做汇率折算。任务码由所属货运订单带出，无需填写。
    </p>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="onSave">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.grp {
  margin-bottom: 20px;
}
.grp-title {
  margin: 0 0 10px;
  padding-bottom: 7px;
  border-bottom: 1px solid var(--rule);
}
.grp-pay .grp-title {
  border-bottom-color: var(--pay-rule);
}
.grp-rec .grp-title {
  border-bottom-color: var(--rec-rule);
}
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 13px 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.note {
  margin: 0;
  font-size: 12px;
  color: var(--ink-3);
}
</style>
