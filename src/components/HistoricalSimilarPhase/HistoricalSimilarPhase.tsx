import { useMemo } from 'react';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import {
  TIER_LABEL,
  TIER_STARS,
  defaultSimilarTargetId,
  similarPhaseOf,
} from '../../data/timeline/historicalSimilarPhase';
import { DRIVER_LABEL, PATTERN_LABEL, PHASE_LABEL } from '../../data/timeline/researchAttention';
import type { Selection } from '../Timeline/Timeline';

interface HistoricalSimilarPhaseProps {
  dataSource: TimelineDataSource;
  /** 现有选中态（与 Timeline / SamePeriodView / Lens 共用） */
  selection: Selection;
  /** 现有选中回调（打开 Level 2 完整历史案例） */
  onSelect: (sel: Selection) => void;
}

/**
 * ③ 历史相似阶段（Historical Similar Phase v1）—— **生命周期相似**检索（Lifecycle Lens）。
 *
 * 与「历史同期（日历）」并存、不互相替代：
 *   历史同期      = 日历同期搜索（去年的这个月）
 *   历史相似阶段  = 生命周期位置搜索（历史上处于类似阶段的机会）
 *
 * 严格边界：
 *   - 只用既有研究数据（TimelineDataSource），不联网、不取实时数据。
 *   - 不做预测 / 不给概率 / 不给买卖信号；相似度是**研究结构相似度**。
 *   - 找不到足够相似 → 输出空态，**不强行凑数**。
 *   - NO LOOK-AHEAD：不使用未来数据；参照对象若取默认值，必须显式标注为「研究数据覆盖内最新案例」。
 */
export function HistoricalSimilarPhase({
  dataSource,
  selection,
  onSelect,
}: HistoricalSimilarPhaseProps) {
  // 参照对象：显式选中优先；否则回退到研究数据覆盖内最新案例（下方会显式标注，不表述为当前市场状态）
  const selectedId = selection?.kind === 'campaign' ? selection.id : null;
  const fallbackId = useMemo(() => defaultSimilarTargetId(dataSource), [dataSource]);
  const effectiveId = selectedId ?? fallbackId;
  const view = useMemo(() => similarPhaseOf(dataSource, effectiveId), [dataSource, effectiveId]);
  const isFallback = selectedId === null;

  if (!view.target) {
    return (
      <section className="hsp-view" aria-label="历史相似阶段">
        <h3 className="tl-layer-title">
          历史相似阶段
          <span className="hsp-tag">Lifecycle Lens</span>
        </h3>
        <p className="hsp-note">
          历史上处于<strong>类似生命周期位置</strong>的研究案例。相似度是研究结构相似度，不是未来走势概率。
        </p>
        <p className="hsp-empty">{view.note}</p>
      </section>
    );
  }

  const t = view.target;

  return (
    <section className="hsp-view" aria-label="历史相似阶段">
      <h3 className="tl-layer-title">
        历史相似阶段
        <span className="hsp-tag">Lifecycle Lens</span>
      </h3>
      <p className="hsp-note">
        历史上处于<strong>类似生命周期位置</strong>的研究案例 —— 按「阶段 → Theme Cycle Pattern →
        Drivers 重叠」排序的<strong>研究结构相似度</strong>，不是未来走势概率，也不是买卖建议。
      </p>

      {/* 参照对象 */}
      <div className="hsp-target">
        <span className="hsp-target-kicker">
          参照对象{isFallback ? '（研究数据覆盖内最新案例，非当前市场状态）' : '（当前选中）'}
        </span>
        <span className="hsp-target-title">{t.title}</span>
        <span className="hsp-target-meta">
          {t.year} · 当时阶段：{t.phaseLabel} · {PATTERN_LABEL[t.pattern]}
          {t.drivers.length > 0 ? ` · ${t.drivers.map((d) => DRIVER_LABEL[d]).join('、')}` : ''}
        </span>
      </div>

      {view.insufficient ? (
        <p className="hsp-empty">{view.note}</p>
      ) : (
        <>
          <ol className="hsp-list">
            {view.results.map((r) => (
              <li className={`hsp-item tier-${r.tier.toLowerCase()}`} key={r.campaign_id}>
                <div className="hsp-item-head">
                  <span className="hsp-item-title">
                    {r.kind === 'candidate' && <em className="rc-badge">RC</em>}
                    {r.title}
                  </span>
                  <span className="hsp-item-year">{r.year}</span>
                  <span className="hsp-tier" title="研究结构相似度（不是概率）">
                    {TIER_STARS[r.tier]} {TIER_LABEL[r.tier]}
                  </span>
                </div>
                <dl className="hsp-kv">
                  <dt>当时阶段</dt>
                  <dd>
                    {r.phaseLabel}
                    <span className="hsp-dim">（参照对象阶段：{PHASE_LABEL[t.phase]}）</span>
                  </dd>
                  <dt>Pattern</dt>
                  <dd>{PATTERN_LABEL[r.pattern]}</dd>
                  <dt>Drivers</dt>
                  <dd>
                    {r.drivers.length > 0
                      ? r.drivers.map((d) => DRIVER_LABEL[d]).join('、')
                      : '研究未记录可用归类'}
                  </dd>
                </dl>
                <div className="hsp-why">
                  <span className="hsp-why-title">为什么类似</span>
                  <ul className="hsp-why-list">
                    {r.reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>
                <div className="hsp-actions">
                  <span className="hsp-range">
                    历史区间 {r.start} → {r.end}
                    {r.macroTheme ? ` · ${r.macroTheme}` : ''}
                  </span>
                  <button
                    className="hsp-open"
                    onClick={() => onSelect({ kind: 'campaign', id: r.campaign_id })}
                  >
                    查看完整历史案例 →
                  </button>
                </div>
              </li>
            ))}
          </ol>
          <p className="hsp-foot">
            {view.note} 最多显示 3 条；与「历史同期（日历）」是两个不同视角，可结合使用。
          </p>
        </>
      )}
    </section>
  );
}
