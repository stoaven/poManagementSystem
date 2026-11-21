/**
 * 接口类型一律从 OpenAPI 契约生成，不再手写。
 *
 * 后端改了响应形状，重新生成一次类型即可；前端类型检查会立刻指出用错的地方，
 * 不必等到运行时才发现字段对不上（design D1/D19）。
 *
 * 重新生成：npm run generate:types
 */
import type { components } from "@/types/api";

export type LoginIn = components["schemas"]["LoginIn"];
export type LoginOut = components["schemas"]["LoginOut"];
export type MeOut = components["schemas"]["MeOut"];

export type UserIn = components["schemas"]["UserIn"];
export type UserOut = components["schemas"]["UserOut"];

export type OptionIn = components["schemas"]["OptionIn"];
export type OptionOut = components["schemas"]["OptionOut"];
export type OptionCandidatesOut = components["schemas"]["OptionCandidatesOut"];
export type OptionDeleteOut = components["schemas"]["OptionDeleteOut"];
export type OptionImportOut = components["schemas"]["OptionImportOut"];
export type ReferencesOut = components["schemas"]["ReferencesOut"];

export type ShipmentIn = components["schemas"]["ShipmentIn"];
export type ShipmentBrief = components["schemas"]["ShipmentBrief"];
export type ShipmentListOut = components["schemas"]["ShipmentListOut"];
export type ShipmentDetailOut = components["schemas"]["ShipmentDetailOut"];

export type ChargeInfoIn = components["schemas"]["ChargeInfoIn"];
export type ChargeInfoPatch = components["schemas"]["ChargeInfoPatch"];
export type ChargeInfoOut = components["schemas"]["ChargeInfoOut"];
