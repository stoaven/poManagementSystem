<script setup lang="ts">
import { computed } from "vue";
import { fieldName } from "@/locales/fieldNames";

const props = withDefaults(
  defineProps<{ label: string; en?: string; cn?: string }>(),
  {},
);

/** 英文名优先取传入值，否则按中文标签查映射表。 */
const en = computed(() => props.en ?? fieldName(props.label));
</script>

<template>
  <span class="bi-label">
    <span class="bi-cn">{{ cn ?? label }}</span>
    <span class="bi-en">{{ en }}</span>
  </span>
</template>

<style scoped>
.bi-label {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.25;
}
.bi-cn {
  font-size: 13px;
  color: var(--ink);
  white-space: nowrap;
}
.bi-en {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-3);
  letter-spacing: 0.01em;
  white-space: nowrap;
}
</style>
