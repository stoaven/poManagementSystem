import { defineStore } from "pinia";
import {
  fetchCandidates,
  type OptionItem,
  type OptionKind,
} from "@/api/options";

export const useOptionsStore = defineStore("options", {
  state: () => ({
    loaded: false,
    kinds: {} as Record<OptionKind, OptionItem[]>,
  }),
  getters: {
    /** 按字段标识取候选（费用信息表单的七个分类字段用它）。 */
    candidates: (s) => (kind: OptionKind) => s.kinds[kind] ?? [],
  },
  actions: {
    /** 首次访问时拉取一次，之后命中缓存不再请求。 */
    async ensureLoaded() {
      if (this.loaded) {
        return;
      }
      this.kinds = await fetchCandidates();
      this.loaded = true;
    },
  },
});
