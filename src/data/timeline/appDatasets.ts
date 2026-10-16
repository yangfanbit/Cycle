/**
 * App 层数据集的**唯一选取入口**（ThreeC 1.3 · v0.6 修复）。
 *
 * ## 为什么单独成一个模块
 * 2026-10-16 v0.6 的 D 工作流发现一个 **P0 接线 bug**：
 *   `App.tsx` 给「方向查询」传的 `dataset` 默认是 **`null`**（只有 `?candidates=example`
 *   才注入 fixture），于是默认页面上查「汽车」得到「只有历史案例」，
 *   **而同页 Watchboard 明明展示着汽车当前候选** —— 同一页两个相反答案。
 *
 * 根因不是某个组件写错，而是**「谁提供默认数据集」只存在于 App.tsx 的接线约定里**：
 * 组件测试都直接注入 dataset，所以这个错误**永远逃过测试**。
 * → 把选取规则抽成**纯函数**，让「默认必须是 canonical」变成**可断言的事实**。
 *
 * ★ 语义：本函数只做**数据集选取**，不改写数据、不做推断。
 */
import currentCandidateFixtureJson from '@current/fixtures/example_candidates.json';
import {
  defaultCurrentCandidateDataset,
  parseCurrentCandidateDataset,
  type CurrentCandidateDataset,
} from './currentCandidate';

/**
 * 选取当前研究对象数据集。
 *
 * @param opts.exampleFixture `true` → 示例 fixture（仅 `?candidates=example` 时）；
 *                            `false`（默认）→ **canonical** 数据集（`current_candidates.json`）。
 *                            ★ 任何情况下**都不返回 null** —— 默认必须是 canonical。
 */
export function selectCurrentCandidateDataset(opts: { exampleFixture: boolean }): CurrentCandidateDataset {
  return opts.exampleFixture
    ? parseCurrentCandidateDataset(currentCandidateFixtureJson).dataset
    : defaultCurrentCandidateDataset();
}
