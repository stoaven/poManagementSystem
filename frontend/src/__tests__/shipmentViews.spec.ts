import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import ElementPlus from "element-plus";
import { createPinia } from "pinia";
import ShipmentListView from "@/views/ShipmentListView.vue";
import ShipmentDetailView from "@/views/ShipmentDetailView.vue";

const push = vi.fn();
const fetchDetail = vi.fn();
const transitionShipment = vi.fn();

vi.mock("vue-router", () => ({
  useRouter: () => ({ push }),
  useRoute: () => ({ params: { id: "1" } }),
}));

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
}));

vi.mock("@/api/chargeInfos", () => ({
  fetchShipment: (...args: unknown[]) => fetchDetail(...args),
  createChargeInfo: vi.fn(),
  updateChargeInfo: vi.fn(),
  deleteChargeInfo: vi.fn(),
  createRelatedChargeInfo: vi.fn(),
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
    cost_totals: [],
    sell_totals: [],
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
        related_source_id: null,
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

  it("满足条件的行提供「新增关联收费用」操作", async () => {
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    expect(w.text()).toContain("新增关联收费用");
  });

  it("详情页展示按币种分组的应付/应收合计带", async () => {
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    expect(w.text()).toContain("应付合计");
    expect(w.text()).toContain("Payable Total");
  });
});

describe("货运订单详情页的状态流转按钮", () => {
  function buttons(text: string) {
    return text.split("\n");
  }

  it("草稿状态给确认与取消", async () => {
    fetchDetail.mockResolvedValue(detailPayload("draft"));
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    const labels = w.findAll("button").map((b) => b.text());
    expect(labels).toContain("确认");
    expect(labels).toContain("取消");
    expect(labels).not.toContain("完成");
  });

  it("已确认状态给完成与取消", async () => {
    fetchDetail.mockResolvedValue(detailPayload("confirmed"));
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    const labels = w.findAll("button").map((b) => b.text());
    expect(labels).toContain("完成");
    expect(labels).toContain("取消");
    expect(labels).not.toContain("确认");
  });

  it("终态不再给流转按钮", async () => {
    fetchDetail.mockResolvedValue(detailPayload("completed"));
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    const labels = w.findAll("button").map((b) => b.text());
    expect(labels).not.toContain("确认");
    expect(labels).not.toContain("完成");
    expect(labels).not.toContain("取消");
    expect(buttons(w.text()).length).toBeGreaterThan(0);
  });

  it("点击确认调用流转接口", async () => {
    fetchDetail.mockResolvedValue(detailPayload("draft"));
    transitionShipment.mockResolvedValue({ id: 1 });
    const w = mountView(ShipmentDetailView);
    await flushPromises();
    await w.findAll("button").find((b) => b.text() === "确认")!.trigger("click");
    await flushPromises();
    expect(transitionShipment).toHaveBeenCalledWith(1, "confirm");
  });
});
