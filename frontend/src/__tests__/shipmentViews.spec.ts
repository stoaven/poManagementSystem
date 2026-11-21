import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import ElementPlus from "element-plus";
import { createPinia } from "pinia";
import ShipmentListView from "@/views/ShipmentListView.vue";
import ShipmentDetailView from "@/views/ShipmentDetailView.vue";

const push = vi.fn();
const fetchDetail = vi.fn();
const transitionShipment = vi.fn();
const exportChargeInfos = vi.fn();

vi.mock("vue-router", async () => {
  // 路由参数要是响应式的，组件才能监听到「换了一个订单」
  const { reactive } = await import("vue");
  const params = reactive({ id: "1" });
  return {
    useRouter: () => ({ push }),
    useRoute: () => ({ params }),
    __routeParams: params,
  };
});

vi.mock("@/api/shipments", () => ({
  listShipments: vi.fn(async () => ({
    items: [
      {
        id: 1,
        shipment_num: "SH-20261119-0007",
        lifecycle: "draft",
        status: 0,
        operator: "13800000001",
        created_at: "2026-11-19 09:24:00",
        updated_at: "2026-11-19 10:12:00",
        charge_info_count: 2,
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  })),
  deleteShipment: vi.fn(),
  transitionShipment: (...args: unknown[]) => transitionShipment(...args),
  fetchShipment: vi.fn(),
  exportChargeInfos: (...args: unknown[]) => exportChargeInfos(...args),
}));

vi.mock("@/api/chargeInfos", () => ({
  fetchShipment: (...args: unknown[]) => fetchDetail(...args),
  createChargeInfo: vi.fn(),
  updateChargeInfo: vi.fn(),
  deleteChargeInfo: vi.fn(),
}));

function detailPayload(lifecycle: string) {
  return {
    id: 1,
    shipment_num: "SH-20261119-0007",
    lifecycle,
    status: 0,
    operator: "13800000001",
    created_at: "2026-11-19 09:24:00",
    updated_at: "2026-11-19 10:12:00",
    charge_info: [
      {
        id: 11,
        shipment_id: 1,
        job_num: "SH-20261119-0007",
        charge_code: "DHLF",
        department: "FIS",
        branch: "SHL",
        cost_currency: "USD",
        os_cost_amt: "8600.00",
        creditor: "CNSHL",
        sell_currency: "CNY",
        os_sell_amt: "61400.00",
        debtor: "CNSHO",
        operator: "13800000001",
        created_at: "2026-11-19 09:24:00",
        updated_at: "2026-11-19 10:12:00",
      },
    ],
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  fetchDetail.mockResolvedValue(detailPayload("draft"));
});

function mountView(component: unknown) {
  return mount(component as never, {
    global: { plugins: [ElementPlus, createPinia()] },
  });
}

describe("货运订单列表页", () => {
  it("没有「查看」按钮，点货运订单号才进详情", async () => {
    const w = mountView(ShipmentListView);
    await flushPromises();
    const text = w.text();
    expect(text).not.toContain("查看");
    expect(text).toContain("SH-20261119-0007");
  });

  it("表头中英双语", async () => {
    const w = mountView(ShipmentListView);
    await flushPromises();
    const text = w.text();
    expect(text).toContain("货运订单号");
    expect(text).toContain("Shipment No.");
    expect(text).toContain("Created At");
  });

  it("不展示应付合计与应收合计", async () => {
    const w = mountView(ShipmentListView);
    await flushPromises();
    expect(w.text()).not.toContain("应付合计");
    expect(w.text()).not.toContain("应收合计");
  });
});

describe("货运订单详情页", () => {
  it("费用信息表不展示任务码列", async () => {
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    expect(w.text()).not.toContain("任务码");
    expect(w.text()).not.toContain("Job No.");
  });

  it("不再提供「添加关联费用」操作", async () => {
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    expect(w.text()).not.toContain("添加关联费用");
  });

  it("币种单独成列，表头中英双语", async () => {
  const w = mountView(ShipmentDetailView);
  await flushPromises();
  const text = w.text();
  expect(text).toContain("应付币种");
  expect(text).toContain("Cost Currency");
  expect(text).toContain("应收币种");
  expect(text).toContain("Sell Currency");
});

it("不再展示合计带", async () => {
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    const text = w.text();
    expect(text).not.toContain("应付合计");
    expect(text).not.toContain("Payable Total");
    expect(text).not.toContain("应收合计");
    expect(text).not.toContain("Receivable Total");
  });
});

describe("货运订单详情页的导出", () => {
  it("点「导出 Excel」调用导出接口并触发下载", async () => {
    exportChargeInfos.mockResolvedValue(new Blob(["xlsx"]));
    // jsdom 没有 createObjectURL，补一个
    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    (URL as unknown as { createObjectURL: unknown }).createObjectURL =
      createObjectURL;
    (URL as unknown as { revokeObjectURL: unknown }).revokeObjectURL =
      revokeObjectURL;

    const w = mountView(ShipmentDetailView);
    await flushPromises();

    const btn = w
      .findAll("button")
      .find((b) => b.text().replace(/\s+/g, "") === "导出Excel");
    expect(btn).toBeDefined();
    await btn!.trigger("click");
    await flushPromises();

    expect(exportChargeInfos).toHaveBeenCalledWith(1);
    expect(createObjectURL).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalled();
  });

  it("没有费用信息时导出按钮不可用", async () => {
    fetchDetail.mockResolvedValue({ ...detailPayload("draft"), charge_info: [] });
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    const btn = w
      .findAll("button")
      .find((b) => b.text().replace(/\s+/g, "") === "导出Excel");
    expect(btn).toBeDefined();
    expect(btn!.attributes("disabled")).toBeDefined();
  });
});

describe("货运订单详情页的取数", () => {
  it("切换到另一个订单会重新取数", async () => {
    const { __routeParams } = (await import("vue-router")) as unknown as {
      __routeParams: { id: string };
    };
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    const callsBefore = fetchDetail.mock.calls.length;

    __routeParams.id = "6";
    await flushPromises();
    await flushPromises();

    expect(fetchDetail.mock.calls.length).toBeGreaterThan(callsBefore);
    const lastCall = fetchDetail.mock.calls[fetchDetail.mock.calls.length - 1];
    expect(lastCall?.[0]).toBe(6);
    expect(w.text()).not.toContain("该货运订单不存在");
  });

  it("订单不存在时清掉上一张单的数据", async () => {
    const { __routeParams } = (await import("vue-router")) as unknown as {
      __routeParams: { id: string };
    };
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    expect(w.text()).toContain("SH-20261119-0007");

    fetchDetail.mockRejectedValue(new Error("该货运订单不存在"));
    __routeParams.id = "999";
    await flushPromises();
    await flushPromises();

    expect(w.text()).not.toContain("SH-20261119-0007");
    expect(w.text()).toContain("该货运订单不存在");
  });
});

describe("货运订单详情页的状态流转按钮", () => {
  function buttons(text: string) {
    return text.split("\n");
  }

  it("任何状态下都不给流转按钮（确认/完成/取消已移除）", async () => {
    for (const lc of ["draft", "confirmed", "completed", "cancelled"]) {
      fetchDetail.mockResolvedValue(detailPayload(lc));
      const w = mountView(ShipmentDetailView);
      await flushPromises();
      const labels = w.findAll("button").map((b) => b.text());
      expect(labels).not.toContain("确认");
      expect(labels).not.toContain("完成");
      expect(labels).not.toContain("取消");
      expect(buttons(w.text()).length).toBeGreaterThan(0);
    }
  });
});
