import { currentMarketOf } from '../../data/timeline/earlyObservation';

/**
 * 当前市场状态（ThreeC 1.2 · 只读描述性产物）。
 *
 * ## ★★ 为什么它必须是**独立组件、且只出现在全局位置**
 *
 * 把「某段历史行情的**启动前**市场状态」与「**当前**市场状态」摆在同一张卡片里，
 * 等于替使用者摆好了「像不像」的题面 —— 即便一个字都没说相似，
 * 两列数字并排本身就构成**隐含的匹配判定**。
 *
 * 因此：
 * - 本组件**只**放在页头等**全局位置**；
 * - **不得**被渲染进任何历史行情的详情面板；
 * - 文案里**明写**「不与任何历史行情并列，也不作任何匹配判定」。
 *
 * ## 红线
 *
 * `AGENTS.md` §1 禁止概率 / 胜率 / 评分 / 排序 / 预测。本组件**只陈述当下状态**。
 */
export function CurrentMarketStrip() {
  const m = currentMarketOf();
  if (!m?.observables) return null;
  const o = m.observables;
  /** 数值展示：缺值显示「—」，不补零、不推断 */
  const num = (v: number | null, digits = 2, suffix = '') =>
    v === null || v === undefined ? '—' : `${v.toFixed(digits)}${suffix}`;

  return (
    <div className="app-market">
      <span className="am-label">当前市场状态</span>
      <span className="am-vals">
        {m.seriesId} {m.asOf} · 量分位 {num(o.volPct60)} · 20 日 {num(o.ret20Pct, 1, '%')} · 波动率比{' '}
        {num(o.volRatio)} · MA20 {o.aboveMa20 ? '上' : '下'} · MA60 {o.aboveMa60 ? '上' : '下'}
      </span>
      <span className="am-note">仅陈述当下状态；不与任何历史行情并列，也不作任何匹配判定</span>
    </div>
  );
}
