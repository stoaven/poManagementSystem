import { describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useOptionsStore } from "@/stores/options";
import * as optionsApi from "@/api/options";

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
