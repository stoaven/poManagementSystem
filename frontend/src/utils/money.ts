/** 金额格式化与校验：全程用字符串，不做浮点运算。 */

/** 把任意输入格式化为两位小数的字符串；空值返回空串。 */
export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return String(value);
  }
  return num.toFixed(2);
}

/** 是否是合法金额：非负、最多两位小数。 */
export function isValidMoney(value: string): boolean {
  if (!value || !/^\d+(\.\d{0,2})?$/.test(value)) {
    return false;
  }
  return Number(value) >= 0;
}

/** 千分位显示（仅用于展示，不用于计算）。 */
export function displayMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return String(value);
  }
  return num
    .toFixed(2)
    .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
