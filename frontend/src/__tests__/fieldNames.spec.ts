import { describe, expect, it } from "vitest";
import { FIELD_NAMES, LABEL_EN, fieldName } from "@/locales/fieldNames";

describe("字段名映射表", () => {
  it("英文名取自上游字段清单", () => {
    expect(fieldName("shipmentNum")).toBe("Shipment No.");
    expect(fieldName("chargeCode")).toBe("Charge Code");
    expect(fieldName("jobNum")).toBe("Job No.");
    expect(fieldName("osCostAmt")).toBe("OS Cost Amt");
    expect(fieldName("osSellAmt")).toBe("OS Sell Amt");
  });

  it("中文标签也能查到英文名", () => {
    expect(fieldName("货运订单号")).toBe("Shipment No.");
    expect(fieldName("费用代码")).toBe("Charge Code");
    expect(fieldName("应付金额")).toBe("OS Cost Amt");
    expect(fieldName("应收对象")).toBe("Debtor");
  });

  it("没有映射时回退到键名本身", () => {
    expect(fieldName("notExist")).toBe("notExist");
  });

  it("映射表的值没有重复", () => {
    const values = Object.values(FIELD_NAMES);
    expect(new Set(values).size).toBe(values.length);
  });

  it("中文标签表的每一项都有英文名", () => {
    for (const [label, en] of Object.entries(LABEL_EN)) {
      expect(label.length, `中文标签不应为空`).toBeGreaterThan(0);
      expect(en.length, `${label} 缺少英文名`).toBeGreaterThan(0);
    }
  });
});
