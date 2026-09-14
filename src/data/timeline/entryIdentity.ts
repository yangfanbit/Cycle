/**
 * Timeline Entry Identity（V1.9.0）—— **纯 UI / ViewModel 概念**。
 *
 * ## 背景
 * 一个 Campaign 可以跨多个年份（如 `C-2019-PHARMA-INNOV` 2019-01-02 ~ 2022-10-31）。
 * Timeline 会在 **2019 / 2020 / 2021 / 2022 各展示年份行**各生成一条【明细（entry）】。
 * 因此 UI 层不能用 `campaign_id` 作为明细身份，否则会出现：
 *   - React key 重复；
 *   - `focusEntryId` 无法区分同 Campaign 的不同年份；
 *   - 年份页签可能同时高亮；
 *   - `find(campaign_id)` 只能返回第一条。
 *
 * ## 规则（唯一 identity）
 * ```
 * entryId = `${campaign_id}@${display_year}`      例如 C-2019-PHARMA-INNOV@2021
 * ```
 * 同一个 Campaign 的不同【展示年份】必须拥有不同 `entryId`。
 *
 * 汽车（单年度 Campaign，`campaign_year === display_year`）→ `entryId` 与 `campaign_id`
 * 一一对应，视觉与行为**不变**（恒等变换）。
 *
 * ## 严格边界（不得越界）
 * - 仅供 UI / ViewModel 使用；**不是持久化标识**，不得写入 DB / Export / Contract。
 * - 不改 schema / DB / Export / Research Model / Campaign 数据。
 * - **不改变 selection 语义**：打开 Campaign Detail（`selection = {kind:'campaign', id}`）
 *   仍以 `campaign_id` 为准 —— `entryId` 只解决【明细级 UI 身份】，
 *   因为「完整历史案例」本身是 Campaign 级、不分年份。
 */

/** Timeline 明细身份（字符串别名，仅用于表达语义；格式 `${campaign_id}@${display_year}`） */
export type TimelineEntryId = string;

/** 由 `campaign_id` + 展示年份构造唯一明细身份。 */
export function timelineEntryId(campaignId: string, displayYear: number): TimelineEntryId {
  return `${campaignId}@${displayYear}`;
}
