import { describe, expect, it } from "vitest";
import { displayMoney, formatMoney, isValidMoney } from "@/utils/money";

describe("金额格式化", () => {
  it("把一位小数补成两位", () => {
    expect(formatMoney("100.1")).toBe("100.10");
  });

  it("保持两位小数不变", () => {
    expect(formatMoney("100.10")).toBe("100.10");
  });

  it("空值返回空串", () => {
    expect(formatMoney("")).toBe("");
    expect(formatMoney(null)).toBe("");
    expect(formatMoney(undefined)).toBe("");
  });

  it("格式化过程不产生浮点尾差", () => {
    // 0.1 + 0.2 在浮点下是 0.30000000000000004
    expect(formatMoney(0.1 + 0.2)).toBe("0.30");
    expect(formatMoney("8600")).toBe("8600.00");
  });

  it("展示用千分位", () => {
    expect(displayMoney("1234567.5")).toBe("1,234,567.50");
    expect(displayMoney(null)).toBe("-");
  });
});

describe("金额校验", () => {
  it("接受零与两位小数", () => {
    expect(isValidMoney("0")).toBe(true);
    expect(isValidMoney("0.00")).toBe(true);
    expect(isValidMoney("1234.56")).toBe(true);
  });

  it("拒绝三位小数", () => {
    expect(isValidMoney("100.125")).toBe(false);
  });

  it("拒绝负数", () => {
    expect(isValidMoney("-5")).toBe(false);
  });

  it("拒绝非数字", () => {
    expect(isValidMoney("abc")).toBe(false);
    expect(isValidMoney("")).toBe(false);
  });
});
