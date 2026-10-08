import {
  buildWatchboard,
  EVIDENCE_DIMENSIONS,
  EVIDENCE_STATE_LABEL,
  WATCHBOARD_DISCLAIMER,
} from '../../data/timeline/currentWatchboard';

/**
 * 当前观察台（ThreeC 1.2 · Usage-Driven）。
 *
 * ## 它解决什么
 *
 * 用户要的是「**在当下这个时间点，一屏看到该看什么**」，而不是**逐条点开对照**。
 *
 * ## ★★★ 为什么它是「状态陈列」而不是「可能性排序」
 *
 * `AGENTS.md` §1 禁止概率 / 胜率 / 推荐分 / 预测。且**一旦给出排序，它就会被当作推荐使用** ——
 * 项目明令禁止荐股。工具无从阻止这种读法，只能**不生产排序**。
 *
 * 因此本组件：
 * - **按阶段分组**（封闭枚举），组内按**阶段起点时间序**；
 * - **明写「阶段越早 ≠ 越可能」**；
 * - 核心列是 **「还缺什么」** —— 把「提前观察」落到**下一步看什么**，而不是买什么。
 */
export function CurrentWatchboardSection({
  onOpenCandidate,
}: {
  /** 点击对象 → 打开已有的当前对象详情（研究问题入口） */
  onOpenCandidate?: (candidateId: string) => void;
}) {
  const wb = buildWatchboard();
  if (wb.total === 0) return null;

  return (
    <section className="watchboard" aria-label="当前观察台">
      <div className="wb-head">
        <h2 className="wb-title">当前观察台</h2>
        <span className="wb-meta">
          研究侧正在观察 <strong>{wb.total}</strong> 个方向
          {wb.asOf && <>（状态记录于 {wb.asOf}）</>}
        </span>
      </div>

      <p className="wb-note">
        {WATCHBOARD_DISCLAIMER.split('**').map((seg, i) => (i % 2 === 1 ? <strong key={i}>{seg}</strong> : seg))}
      </p>

      {wb.groups.map((g) => (
        <div className="wb-group" key={g.phase}>
          <div className="wb-group-head">
            <span className="wb-phase">{g.phaseLabel}</span>
            <span className="phase-text">{g.items.length} 个</span>
          </div>
          <ul className="wb-list">
            {g.items.map((it) => (
              <li className="wb-item" key={it.candidateId}>
                <div className="wb-item-head">
                  <span className="wb-name">{it.displayName}</span>
                  {it.macroTheme && <span className="wb-theme">{it.macroTheme}</span>}
                  {it.daysSincePhaseStart !== null && (
                    <span className="phase-text">
                      阶段起点 {it.phaseStart}（记录日已过 {it.daysSincePhaseStart} 天）
                    </span>
                  )}
                </div>

                <div className="wb-states">
                  {EVIDENCE_DIMENSIONS.map((d) => (
                    <span className={`wb-state wb-s-${it.evidence[d.key].toLowerCase()}`} key={d.key}>
                      {d.label} {EVIDENCE_STATE_LABEL[it.evidence[d.key]]}
                    </span>
                  ))}
                  <span className="phase-text">
                    证据 {it.evidenceCount} 条 · 未决问题 {it.openIssues} · 研究问题 {it.researchQuestions}
                  </span>
                </div>

                {/* ★ 核心列：还缺什么 —— 这是「下一步看什么」 */}
                <div className="wb-gaps">
                  <span className="wb-gaps-label">还缺什么</span>
                  {it.gaps.length > 0 ? (
                    <span className="wb-gaps-list">{it.gaps.join(' · ')}</span>
                  ) : (
                    <span className="wb-gaps-list">三个维度均已现 —— 缺口在别处（见研究问题）</span>
                  )}
                </div>

                <div className="wb-foot">
                  {it.narrativeTypes.length > 0 && (
                    <span className="phase-text">叙事类型 {it.narrativeTypes.join(' / ')}</span>
                  )}
                  {it.referenceCases.length > 0 && (
                    <span className="phase-text">研究侧参照 {it.referenceCases.join(' · ')}</span>
                  )}
                  {onOpenCandidate && (
                    <button className="wb-open" type="button" onClick={() => onOpenCandidate(it.candidateId)}>
                      看研究问题 →
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}

      <p className="wb-gap-summary">
        三个维度里仍为「初现 / 未标注」的计数（<strong>计数事实</strong>，不是评分）：
        {EVIDENCE_DIMENSIONS.map((d) => `${d.label} ${wb.gapCounts[d.label] ?? 0}`).join(' · ')}
      </p>
    </section>
  );
}
