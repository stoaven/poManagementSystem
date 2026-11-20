import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import ElementPlus, { ElMessageBox } from "element-plus";
import { createPinia } from "pinia";
import OptionListView from "@/views/OptionListView.vue";
import UserManagementView from "@/views/UserManagementView.vue";
import { useAuthStore } from "@/stores/auth";

const listOptions = vi.fn();
const createOption = vi.fn();
const updateOption = vi.fn();
const deleteOption = vi.fn();
const setOptionActive = vi.fn();
const fetchOptionReferences = vi.fn();

vi.mock("@/api/options", async () => {
  const actual = await vi.importActual<typeof import("@/api/options")>(
    "@/api/options",
  );
  return {
    ...actual,
    listOptions: (...args: unknown[]) => listOptions(...args),
    createOption: (...args: unknown[]) => createOption(...args),
    updateOption: (...args: unknown[]) => updateOption(...args),
    deleteOption: (...args: unknown[]) => deleteOption(...args),
    setOptionActive: (...args: unknown[]) => setOptionActive(...args),
    fetchOptionReferences: (...args: unknown[]) =>
      fetchOptionReferences(...args),
  };
});

const listUsers = vi.fn();
const setUserActive = vi.fn();
const deleteUser = vi.fn();

vi.mock("@/api/users", async () => {
  const actual = await vi.importActual<typeof import("@/api/users")>(
    "@/api/users",
  );
  return {
    ...actual,
    listUsers: (...args: unknown[]) => listUsers(...args),
    setUserActive: (...args: unknown[]) => setUserActive(...args),
    deleteUser: (...args: unknown[]) => deleteUser(...args),
  };
});

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useRoute: () => ({ params: {} }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  listOptions.mockResolvedValue([]);
  listUsers.mockResolvedValue([]);
});

function mountView(component: unknown, pinia = createPinia()) {
  return mount(component as never, {
    global: { plugins: [ElementPlus, pinia] },
  });
}

const OPTION = {
  id: 1,
  code: "DHLF",
  name: "DHLF",
  is_active: true,
  deleted: false,
  status: 0,
  operator: "13800000001",
  created_at: "2026-11-18 16:02:00",
  updated_at: "2026-11-18 16:02:00",
  referenced: 12,
};

describe("选项维护页", () => {
  it("六个页签中英双语", async () => {
    listOptions.mockResolvedValue([OPTION]);
    const w = mountView(OptionListView);
    await flushPromises();
    const text = w.text();
    for (const [cn, en] of [
      ["费用代码", "Charge Code"],
      ["应付部门", "Department"],
      ["应付分支机构", "Branch"],
      ["币种", "Currency"],
      ["应付对象", "Creditor"],
      ["应收对象", "Debtor"],
    ]) {
      expect(text).toContain(cn);
      expect(text).toContain(en);
    }
  });

  it("没有排序列", async () => {
    listOptions.mockResolvedValue([OPTION]);
    const w = mountView(OptionListView);
    await flushPromises();
    expect(w.text()).not.toContain("排序");
    expect(w.text()).not.toContain("Sort");
  });

  it("表头中英双语", async () => {
    listOptions.mockResolvedValue([OPTION]);
    const w = mountView(OptionListView);
    await flushPromises();
    const text = w.text();
    expect(text).toContain("代码");
    expect(text).toContain("Code");
    expect(text).toContain("被引用");
    expect(text).toContain("Referenced");
  });

  it("切换页签会按新的 kind 重新取数", async () => {
    listOptions.mockResolvedValue([OPTION]);
    const w = mountView(OptionListView);
    await flushPromises();
    listOptions.mockClear();

    const tabs = w.findAll(".tab");
    await tabs[1].trigger("click");
    await flushPromises();
    expect(listOptions).toHaveBeenCalledWith("departments");
  });

  it("请求时不带 include_deleted——已删除项由服务端过滤", async () => {
    listOptions.mockResolvedValue([OPTION]);
    const w = mountView(OptionListView);
    await flushPromises();
    expect(listOptions).toHaveBeenCalledWith("charge_codes");
  });

  it("页面上不出现「已删除」", async () => {
    listOptions.mockResolvedValue([OPTION]);
    const w = mountView(OptionListView);
    await flushPromises();
    expect(w.text()).not.toContain("已删除");
  });

  it("删除前先问引用数量，确认后才删", async () => {
    listOptions.mockResolvedValue([OPTION]);
    fetchOptionReferences.mockResolvedValue(12);
    deleteOption.mockResolvedValue({ ok: true, referenced: 12 });
    const confirm = vi
      .spyOn(ElMessageBox, "confirm")
      .mockResolvedValue("confirm" as never);

    const w = mountView(OptionListView);
    await flushPromises();
    await w.findAll("a.lnk").find((a) => a.text() === "删除")!.trigger("click");
    await flushPromises();

    expect(fetchOptionReferences).toHaveBeenCalledWith("charge_codes", 1);
    expect(confirm.mock.calls[0][0]).toContain("12");
    expect(deleteOption).toHaveBeenCalledWith("charge_codes", 1);
    confirm.mockRestore();
  });

  it("用户取消删除就不删", async () => {
    listOptions.mockResolvedValue([OPTION]);
    fetchOptionReferences.mockResolvedValue(0);
    const confirm = vi
      .spyOn(ElMessageBox, "confirm")
      .mockRejectedValue(new Error("cancel"));

    const w = mountView(OptionListView);
    await flushPromises();
    await w.findAll("a.lnk").find((a) => a.text() === "删除")!.trigger("click");
    await flushPromises();

    expect(deleteOption).not.toHaveBeenCalled();
    confirm.mockRestore();
  });
});

describe("用户管理页", () => {
  const ADMIN = {
    id: 1,
    phone: "13800000001",
    username: "张明",
    authority: "admin" as const,
    is_active: true,
    status: 0,
    operator: "13800000001",
    created_at: "2026-11-06 10:02:00",
    updated_at: "2026-11-08 09:31:00",
  };

  it("表头中英双语并渲染用户", async () => {
    listUsers.mockResolvedValue([ADMIN]);
    const w = mountView(UserManagementView);
    await flushPromises();
    const text = w.text();
    expect(text).toContain("手机号");
    expect(text).toContain("Phone");
    expect(text).toContain("用户名称");
    expect(text).toContain("Username");
    expect(text).toContain("13800000001");
  });

  it("当前登录用户的停用入口不可用", async () => {
    listUsers.mockResolvedValue([ADMIN]);
    const pinia = createPinia();
    const auth = useAuthStore(pinia);
    auth.user = ADMIN;
    const w = mountView(UserManagementView, pinia);
    await flushPromises();

    const toggle = w
      .findAll("a.lnk")
      .find((a) => a.text() === "停用" || a.text() === "启用");
    expect(toggle).toBeDefined();
    expect(toggle!.classes()).toContain("lnk-mute");
  });

  it("普通用户的停用入口可点", async () => {
    listUsers.mockResolvedValue([
      { ...ADMIN, id: 2, phone: "13902136688", username: "李静", authority: "normal" },
    ]);
    const pinia = createPinia();
    const auth = useAuthStore(pinia);
    auth.user = { ...ADMIN, id: 9, phone: "13700000009", username: "王磊", authority: "normal" };
    const w = mountView(UserManagementView, pinia);
    await flushPromises();

    const toggle = w.findAll("a.lnk").find((a) => a.text() === "停用");
    expect(toggle).toBeDefined();
    expect(toggle!.classes()).not.toContain("lnk-mute");
  });
});
