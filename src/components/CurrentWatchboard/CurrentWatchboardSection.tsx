import {
  buildWatchboard,
  WATCHBOARD_DISCLAIMER,
} from '../../data/timeline/currentWatchboard';

/**
 * 当前观察台（ThreeC 1.2 · Usage-Driven）。
 *
 * ## ★★★ 阶段值的来源（**不得绕过**）
 *
 * 阶段**不是**研究侧声明的 `attention_state`，而是**产品端规则引擎**由证据矩阵**推导**的权威值
 * （`currentPhaseInference`）。研究与推导不一致时，本组件**两者并列显示**并标注 —— 引擎明令
 * 「不一致时 UI 必须并列显示，不得静默取一」。
 *
 * ## ★★ 它是什么，不是什么
 *
 * 是**研究侧观察状态的陈列**；**不是**「可能性排序」——
 * 项目禁止概率 / 评分 / 预测，且**一旦排序就会被当作推荐**。因此按阶段分组、组内按时间序，
 * 核心列是「**还缺哪些维度**」（引擎给的，不是本组件自算）。
 */
export function CurrentWatchboardSection({
  onOpenCandidate,
}: {
  /** 点击对象 → 展开已有的当前时间透镜（只导航，不做判定） */
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
          {wb.disagreementCount > 0 && (
            <> · 其中 <strong>{wb.disagreementCount}</strong> 个「推导阶段 ≠ 研究声明」</>
          )}
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
                  <span className="phase-text">
                    阶段起点 {it.phaseStart ?? '未记录'}
                    {it.daysSincePhaseStart !== null && <>（记录日已过 {it.daysSincePhaseStart} 天）</>}
                  </span>
                </div>

                {/* ★★ 推导阶段 vs 研究声明：不一致时**必须并列**，不静默取一 */}
                <div className="wb-phase-line">
                  <span className="wb-phase-src">推导阶段（权威）</span>
                  <span className={`wb-phase-val wb-p-${it.phase.toLowerCase()}`}>{it.phaseLabel}</span>
                  <span className="phase-text">
                    命中规则 {it.matchedRule} · {it.ruleLabel}
                  </span>
                  {it.agreesWithDeclared ? (
                    <span className="phase-text">与研究声明一致</span>
                  ) : (
                    <span className="wb-disagree">
                      研究声明为「{it.declaredPhaseLabel}」—— 两者并列，不静默取一
                    </span>
                  )}
                </div>

                {/* ★ 核心列：还缺哪些维度（引擎给的） */}
                <div className="wb-gaps">
                  <span className="wb-gaps-label">还缺哪些维度</span>
                  {it.missingDimensions.length > 0 ? (
                    <span className="wb-gaps-list">{it.missingDimensions.join(' · ')}</span>
                  ) : (
                    <span className="wb-gaps-list">八个维度均已明确</span>
                  )}
                  <span className="phase-text">
                    覆盖 {it.coverage.known}/{it.coverage.total}（{it.coverage.label}）
                  </span>
                </div>

                {/* 研究侧叙事原文可能含 `**` 强调符（全库既有约定：渲染为加粗，不丢弃、不字面显示） */}
                {it.oneLiner && (
                  <p className="wb-oneliner">
                    {it.oneLiner.split('**').map((seg, i) => (i % 2 === 1 ? <strong key={i}>{seg}</strong> : seg))}
                  </p>
                )}

                <div className="wb-foot">
                  <span className="phase-text">
                    研究问题 {it.researchQuestions}
                    {!it.researchReady && ' · 尚不具备进入研究的最低条件'}
                    {it.researchReady && !it.similarityReady && ' · 阶段未推导出，不可作相似度参照'}
                  </span>
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

      {wb.gapCounts.length > 0 && (
        <p className="wb-gap-summary">
          「尚未明确」的维度分布（<strong>计数事实</strong>，不是评分）：
          {wb.gapCounts.map((x) => `${x.dimension} ${x.count}`).join(' · ')}
        </p>
      )}
    </section>
  );
}
