import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import ElementPlus from "element-plus";
import { createPinia } from "pinia";
import ChargeInfoDialog from "@/components/ChargeInfoDialog.vue";
import ShipmentFormView from "@/views/ShipmentFormView.vue";
import { useOptionsStore } from "@/stores/options";

const createChargeInfo = vi.fn();
const updateChargeInfo = vi.fn();

vi.mock("@/api/chargeInfos", async () => {
  const actual = await vi.importActual<typeof import("@/api/chargeInfos")>(
    "@/api/chargeInfos",
  );
  return {
    ...actual,
    createChargeInfo: (...args: unknown[]) => createChargeInfo(...args),
    updateChargeInfo: (...args: unknown[]) => updateChargeInfo(...args),
  };
});

const createShipment = vi.fn();
const updateShipment = vi.fn();
const fetchShipment = vi.fn();

vi.mock("@/api/shipments", async () => {
  const actual = await vi.importActual<typeof import("@/api/shipments")>(
    "@/api/shipments",
  );
  return {
    ...actual,
    createShipment: (...args: unknown[]) => createShipment(...args),
    updateShipment: (...args: unknown[]) => updateShipment(...args),
    fetchShipment: (...args: unknown[]) => fetchShipment(...args),
  };
});

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useRoute: () => ({ params: {} }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

function mountDialog(props: Record<string, unknown> = {}) {
  return mount(ChargeInfoDialog, {
    props: { modelValue: true, shipmentId: 1, ...props },
    global: { plugins: [ElementPlus, createPinia()] },
    attachTo: document.body,
  });
}

describe("费用信息弹窗", () => {
  it("应付与应收分两组，字段标签中英双语", async () => {
    const w = mountDialog();
    await flushPromises();
    const text = w.text();
    for (const [cn, en] of [
      ["费用代码", "Charge Code"],
      ["应付部门", "Department"],
      ["应付分支机构", "Branch"],
      ["应付币种", "Cost Currency"],
      ["应付金额", "OS Cost Amt"],
      ["应付对象", "Creditor"],
      ["应收币种", "Sell Currency"],
      ["应收金额", "OS Sell Amt"],
      ["应收对象", "Debtor"],
    ]) {
      expect(text).toContain(cn);
      expect(text).toContain(en);
    }
  });

  it("不展示任务码字段（只在脚注里说明它由订单带出）", async () => {
    const w = mountDialog();
    await flushPromises();
    // 任务码不作为表单字段出现
    expect(
      w.findAll("label").filter((l) => l.text().includes("任务码")),
    ).toHaveLength(0);
    expect(w.findAll("label").filter((l) => l.text().includes("Job No."))).toHaveLength(0);
  });

  it("必填项没填时不发请求", async () => {
    const w = mountDialog();
    await flushPromises();
    await w.findAll("button").find((b) => b.text() === "保存")!.trigger("click");
    await flushPromises();
    expect(createChargeInfo).not.toHaveBeenCalled();
  });

  it("费用代码旁边有描述输入框", async () => {
    const w = mountDialog();
    await flushPromises();
    const fields = w.findAll("label").filter((l) => l.text().includes("描述"));
    expect(fields.length).toBe(1);
    expect(fields[0].text()).toContain("Description");
    // 描述框与费用代码框在同一组（费用组）里
    const grp = w.findAll(".grp")[0];
    expect(grp.text()).toContain("费用代码");
    expect(grp.text()).toContain("Description");
  });

  it("选了费用代码就带出该代码的描述", async () => {
    const w = mountDialog();
    await flushPromises();
    const store = useOptionsStore();
    store.kinds = {
      charge_codes: [
        { code: "DHLF", description: "快递国际" } as never,
        { code: "OCUC", description: "清关费" } as never,
      ],
    } as never;

    const vm = w.vm as unknown as {
      form: Record<string, string | null>;
      onChargeCodeChange: (code: string | null) => void;
    };
    vm.onChargeCodeChange("OCUC");
    await flushPromises();
    expect(vm.form.description).toBe("清关费");
  });

  it("提交时带上页面填的描述", async () => {
    createChargeInfo.mockResolvedValue([{ id: 5 }, { id: 6 }]);
    const w = mountDialog();
    await flushPromises();
    const store = useOptionsStore();
    store.kinds = {
      charge_codes: [{ code: "DHLF", description: "快递国际" } as never],
      departments: [{ code: "FIS" } as never],
      branches: [{ code: "SHL" } as never],
      currencies: [{ code: "USD" }, { code: "CNY" }] as never,
      creditors: [{ code: "CNSHL" } as never],
      debtors: [{ code: "CNSHO" } as never],
    };

    const vm = w.vm as unknown as { form: Record<string, string | null> };
    Object.assign(vm.form, {
      charge_code: "DHLF",
      description: "快递国际",
      department: "FIS",
      branch: "SHL",
      cost_currency: "USD",
      os_cost_amt: "8600.00",
      creditor: "CNSHL",
      sell_currency: "CNY",
      os_sell_amt: "61400.00",
      debtor: "CNSHO",
    });

    await w.findAll("button").find((b) => b.text() === "保存")!.trigger("click");
    await flushPromises();

    expect(createChargeInfo).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ description: "快递国际" }),
    );
  });

  it("填齐两侧后提交完整载荷（一次写入两条）", async () => {
    createChargeInfo.mockResolvedValue([{ id: 5 }, { id: 6 }]);
    const w = mountDialog();
    await flushPromises();

    const store = useOptionsStore();
    store.kinds = {
      charge_codes: [{ code: "DHLF" } as never],
      departments: [{ code: "FIS" } as never],
      branches: [{ code: "SHL" } as never],
      currencies: [{ code: "USD" }, { code: "CNY" }] as never,
      creditors: [{ code: "CNSHL" } as never],
      debtors: [{ code: "CNSHO" } as never],
    };

    // 直接改表单状态：下拉交互在单测里太重，这里验证提交载荷的组装
    const vm = w.vm as unknown as { form: Record<string, string | null> };
    vm.form.charge_code = "DHLF";
    vm.form.department = "FIS";
    vm.form.branch = "SHL";
    vm.form.cost_currency = "USD";
    vm.form.os_cost_amt = "8600.00";
    vm.form.creditor = "CNSHL";
    vm.form.sell_currency = "CNY";
    vm.form.os_sell_amt = "61400.00";
    vm.form.debtor = "CNSHO";

    await w.findAll("button").find((b) => b.text() === "保存")!.trigger("click");
    await flushPromises();

    expect(createChargeInfo).toHaveBeenCalledWith(1, {
      charge_code: "DHLF",
      description: "",
      department: "FIS",
      branch: "SHL",
      cost_currency: "USD",
      os_cost_amt: "8600.00",
      creditor: "CNSHL",
      sell_currency: "CNY",
      os_sell_amt: "61400.00",
      debtor: "CNSHO",
    });
  });
});

describe("货运订单表单", () => {
  it("新建时提交货运订单号并跳到详情", async () => {
    createShipment.mockResolvedValue({ id: 9, shipment_num: "SH-1" });
    const w = mount(ShipmentFormView, {
      global: { plugins: [ElementPlus, createPinia()] },
    });
    await flushPromises();

    const input = w.find("input");
    await input.setValue("SH-1");
    await w.findAll("button").find((b) => b.text() === "保存")!.trigger("click");
    await flushPromises();

    expect(createShipment).toHaveBeenCalledWith({ shipment_num: "SH-1" });
  });

  it("货运订单号为空时不发请求", async () => {
    const w = mount(ShipmentFormView, {
      global: { plugins: [ElementPlus, createPinia()] },
    });
    await flushPromises();
    await w.findAll("button").find((b) => b.text() === "保存")!.trigger("click");
    await flushPromises();
    expect(createShipment).not.toHaveBeenCalled();
  });
});
