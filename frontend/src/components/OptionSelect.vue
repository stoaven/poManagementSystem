<script setup lang="ts">
import { computed } from "vue";
import {
  OPTION_KIND_LABELS,
  optionLabel,
  type OptionKind,
} from "@/api/options";
import { useOptionsStore } from "@/stores/options";

const props = defineProps<{
  kind: OptionKind;
  modelValue: string | null;
  /** 允许直接输入表外新值（本期所有分类字段均为封闭集合，默认 false）。 */
  allowCreate?: boolean;
  placeholder?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: string | null): void;
  /** 用户在下拉里选了别的值——只有用户操作才发，程序赋值不发。 */
  (e: "change", v: string | null): void;
}>();

const options = useOptionsStore();

const items = computed(() => options.candidates(props.kind));

const label = computed(
  () => props.placeholder ?? OPTION_KIND_LABELS[props.kind] ?? "请选择",
);

function onChange(v: string | null) {
  emit("update:modelValue", v);
  emit("change", v);
}
</script>

<template>
  <el-select
    :model-value="modelValue"
    :placeholder="label"
    :allow-create="allowCreate"
    :filterable="true"
    default-first-option
    clearable
    style="width: 100%"
    @update:model-value="onChange"
  >
    <el-option
      v-for="item in items"
      :key="item.code"
      :label="
        optionLabel(props.kind, item) === item.code
          ? item.code
          : `${item.code} · ${optionLabel(props.kind, item)}`
      "
      :value="item.code"
    />
  </el-select>
</template>
