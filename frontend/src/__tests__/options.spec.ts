import { describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useOptionsStore } from "@/stores/options";
import * as optionsApi from "@/api/options";
import { optionLabel } from "@/api/options";

describe("选项候选缓存", () => {
  it("首次访问触发请求，之后命中缓存", async () => {
    setActivePinia(createPinia());
    const store = useOptionsStore();

    let calls = 0;
    const spy = vi
      .spyOn(optionsApi, "fetchCandidates")
      .mockImplementation(async () => {
        calls += 1;
        return {
          charge_codes: [],
          departments: [],
          branches: [],
          currencies: [],
          creditors: [],
          debtors: [],
        };
      });

    await store.ensureLoaded();
    expect(calls).toBe(1);
    expect(store.loaded).toBe(true);

    await store.ensureLoaded();
    expect(calls).toBe(1); // 缓存命中，不再请求

    spy.mockRestore();
  });

  it("未加载时按类型取候选返回空数组", () => {
    setActivePinia(createPinia());
    const store = useOptionsStore();
    expect(store.candidates("currencies")).toEqual([]);
  });
});

describe("选项项的展示标签", () => {
  it("费用代码表用描述，其余五类用名称", () => {
    const cc = { code: "DHLF", name: null, description: "快递国际" } as never;
    expect(optionLabel("charge_codes", cc)).toBe("快递国际");
    const dept = { code: "FIS", name: "应付部门", description: null } as never;
    expect(optionLabel("departments", dept)).toBe("应付部门");
  });

  it("标签为空时用代码本身", () => {
    const cc = { code: "DHLF", name: null, description: null } as never;
    expect(optionLabel("charge_codes", cc)).toBe("DHLF");
  });
});
