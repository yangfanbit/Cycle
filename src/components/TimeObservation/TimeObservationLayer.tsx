import { useMemo, useState } from 'react';
import {
  buildTimeObservationLayer,
  defaultTimeObservationDataset,
  mdFractionInYear,
  windowBandsForYear,
  type TimeObservationDataset,
  type TimeObservationLayerModel,
  type TimeObservationView,
} from '../../data/timeline/timeObservationPatterns';
import { yearFraction } from '../../utils';
import { MonthGrid, TodayLine, pct } from '../Timeline/trackPrimitives';
import type { Selection } from '../Timeline/Timeline';

/**
 * 时间型观察层（Time-based Observation Layer）—— Timeline 内的极轻一层。
 *
 * 回答：**「历史上，一年中的这个时间位置附近，反复出现过值得研究的主题启动吗？」**
 *
 * ## 三层信息结构（Phase 7.3 起）
 *   Level 1  Timeline 上的历史观察窗口带 + **A. 当前时间匹配**（今天是否在窗口附近）
 *   Level 2  **B. 历史观察回溯**（不论今天是否在窗口内都可用：中心 / 窗口 / 年份案例）
 *            + 就地展开的 Pattern Summary（口径 / 复现 / 核验状态 / 机制 / 限制 / 免责）
 *   Level 3  点击某个年份 → **既有** Campaign Detail（不新建第四套详情）
 *
 * ## 视觉纪律（不得违反）
 * - Timeline 仍是第一视觉：本层只是一条**很薄的带**，不遮挡、不抢占 Campaign 主体。
 * - 不使用涨跌红绿、不使用买点箭头、不出现「推荐」/「预测」/「信号」字样。
 * - 用淡底纹 + 点划线边界 + 小标签表达；与既有「提前观察参考区」同一套视觉语言。
 * - 措辞只允许「历史观察窗口 / 历史复现 / 核验状态」，**不得**出现概率、胜率、买卖建议。
 *
 * 没有可展示的窗口时**不渲染本层**（不显示空壳）。
 */
interface TimeObservationLayerProps {
  year: number;
  today: string;
  onSelect: (sel: Selection) => void;
  /** Timeline 的 tooltip 回调（可选；缺省时退化为原生 title） */
  showTooltip?: (e: React.MouseEvent, title: string, lines: string[]) => void;
  hideTooltip?: () => void;
  /** 数据集注入（缺省 = canonical Artifact；测试可注入） */
  dataset?: TimeObservationDataset;
}

export function TimeObservationLayer({
  year,
  today,
  onSelect,
  showTooltip,
  hideTooltip,
  dataset,
}: TimeObservationLayerProps) {
  const model = useMemo(
    () => buildTimeObservationLayer(dataset ?? defaultTimeObservationDataset(), today),
    [dataset, today],
  );

  // undefined = 用户未干预 → 用默认展开（今天处于/接近窗口的最相关一条）；null = 用户主动折叠
  const [expandedId, setExpandedId] = useState<string | null | undefined>(undefined);
  if (model.views.length === 0) return null;

  const defaultId =
    model.currentMatch.inWindow[0]?.patternId ?? model.currentMatch.near[0]?.patternId ?? null;
  const activeId = expandedId === undefined ? defaultId : expandedId;

  const showTodayLine = today.startsWith(`${year}-`);
  const todayFrac = showTodayLine ? yearFraction(today) : 0;

  return (
    <section className="tl-layer layer-time-observation">
      <h3 className="tl-layer-title">
        时间型观察层 · 历史观察窗口
        <span className="ctl-tag">历史样本复现 · 非预测</span>
      </h3>

      {/* ---------- A. 当前时间匹配：今天与历史观察窗口的日历关系 ---------- */}
      <div className={`tob-current tob-${model.currentMatch.state.toLowerCase()}`}>
        <span className="tob-current-head">
          <span className="tob-current-tag">{model.currentMatchLabel}</span>
          <span className="tob-current-date">今天 {today}</span>
        </span>
        <span className="tob-current-text">{model.currentMatch.text}</span>
        <span className="tob-current-warn">
          仅表示日历位置关系，不代表市场状态，也不是买入或卖出信号。
        </span>
      </div>

      {model.views.map((v) => {
        const bands = v.window ? windowBandsForYear(v.window.start, v.window.end, year) : [];
        const yearObs = v.observations.filter((o) => o.year === year);
        const open = activeId === v.patternId;
        return (
          <div key={v.patternId} className="tob-block">
            <div className={`tl-row tob-row${open ? ' open' : ''}`}>
              <div className="tl-row-label">
                <button
                  className="tob-name"
                  onClick={() => setExpandedId(open ? null : v.patternId)}
                  aria-expanded={open}
                >
                  {v.title}
                </button>
                {/* 主题族（Phase 7.3）：缺失时回退到 themeScope */}
                <span className="sub">
                  {v.themeFamilyName ?? v.themeScope} · {v.patternTypeLabel}
                </span>
                {v.proximity !== 'OUTSIDE' && (
                  <span className={`tob-chip tob-chip-${v.proximity.toLowerCase()}`}>
                    {v.proximityLabel}
                  </span>
                )}
                {v.exploratory && (
                  <span className="tob-chip tob-chip-explor" title={model.exploratoryNote}>
                    {model.exploratoryLabel}
                  </span>
                )}
              </div>
              <div className="tl-track tob-track">
                <MonthGrid year={year} />
                {/* 历史观察窗口：淡底纹 + 点划线边界（不抢 Campaign 主体） */}
                {bands.map((b, i) => (
                  <div
                    key={`band-${i}`}
                    className={`tob-band${b.continuesFromPrevYear ? ' cont-prev' : ''}${
                      b.continuesIntoNextYear ? ' cont-next' : ''
                    }${open ? ' on' : ''}`}
                    style={{ left: pct(b.left), width: pct(b.width) }}
                    onClick={() => setExpandedId(open ? null : v.patternId)}
                    {...(showTooltip
                      ? {
                          onMouseEnter: (e: React.MouseEvent) =>
                            showTooltip(e, `${v.title} · 历史观察窗口`, [
                              `窗口：${v.windowLabel}（${v.window.widthDays} 天，中心 ${v.centerDate}）`,
                              `口径：${v.window.method}`,
                              `${v.recurrenceLabel}`,
                              `${model.verificationPrefix}：${v.verification.label}`,
                              model.disclaimer,
                            ]),
                          onMouseLeave: hideTooltip,
                        }
                      : { title: `${v.title} · 历史观察窗口 ${v.windowLabel}` })}
                  >
                    <span className="tob-band-label">{v.windowLabel}</span>
                  </div>
                ))}
                {/* 该年的研究观察起点（Early Signal 落在时间轴上的位置） */}
                {yearObs.map((o) => (
                  <span
                    key={o.campaignId}
                    className={`tob-obs-dot${o.inWindow === false ? ' outside' : ''}${
                      o.verification.status === 'VERIFIED' ? ' verified' : ''
                    }`}
                    style={{ left: pct(mdFractionInYear(o.md, year)) }}
                    onClick={() =>
                      onSelect({ kind: 'campaign', id: o.campaignId, timelineEntryId: o.timelineEntryId })
                    }
                    {...(showTooltip
                      ? {
                          onMouseEnter: (e: React.MouseEvent) =>
                            showTooltip(e, `${o.title} · 研究观察起点`, [
                              `${o.date}（${o.anchorType}）`,
                              o.inWindow === false
                                ? `该年锚点落在典型窗口（${v.windowLabel}）之外`
                                : `落在典型窗口内（${v.windowLabel}）`,
                              `${model.verificationPrefix}：${o.verification.status === 'VERIFIED' ? '已核验' : '未核验'}${
                                o.verification.note ? ` — ${o.verification.note}` : ''
                              }`,
                              '研究观察起点是研究口径的起点，不是正式行情起点。',
                            ]),
                          onMouseLeave: hideTooltip,
                        }
                      : { title: `${o.title} · ${o.date}（研究观察起点）` })}
                  >
                    {o.year}
                  </span>
                ))}
                {showTodayLine && <TodayLine frac={todayFrac} />}
              </div>
            </div>

            {/* ---------- B. 历史观察回溯：与「当前匹配」独立，始终可见 ---------- */}
            <div className="tob-recall" role="note">
              <span className="tob-recall-label">{model.historicalRecallLabel}</span>
              <span className="tob-recall-meta">
                中心 {v.centerDate} · 窗口 {v.windowLabel} · {v.recurrenceLabel}
              </span>
              <span className="tob-recall-years">
                {v.observations.map((o) => (
                  <button
                    key={o.campaignId}
                    className={`tob-year${o.inWindow === false ? ' outside' : ''}`}
                    onClick={() =>
                      onSelect({ kind: 'campaign', id: o.campaignId, timelineEntryId: o.timelineEntryId })
                    }
                    title={`${o.title}（研究观察起点 ${o.date}）—— 打开完整历史案例`}
                  >
                    {o.year}
                  </button>
                ))}
              </span>
            </div>

            {/* Level 2：Pattern Summary（就地展开，不离开页面、不遮挡 Timeline） */}
            {open && <PatternSummary view={v} model={model} onSelect={onSelect} />}
          </div>
        );
      })}

      <p className="tob-foot">
        {model.researchOnlyCount > 0 && (
          <>
            另有 {model.researchOnlyCount} 条时间规律处于研究层（样本不足或稳定性未达门槛），未进入 Timeline。{' '}
          </>
        )}
        研究快照：{model.snapshotDate}｜数据为研究样本，锚点核验状态见各模式详情。
      </p>
    </section>
  );
}

/** Level 2：Pattern Summary（窗口 / 复现 / 核验 / 机制 / 限制 / 免责） */
function PatternSummary({
  view,
  model,
  onSelect,
}: {
  view: TimeObservationView;
  model: TimeObservationLayerModel;
  onSelect: (sel: Selection) => void;
}) {
  return (
    <div className="tob-detail" role="region" aria-label={`${view.title} 摘要`}>
      <div className="tob-detail-head">
        <strong>{view.title}</strong>
        <span className="tob-detail-type">
          {(view.themeFamilyName ?? view.themeScope)} · {view.patternTypeLabel}
        </span>
        <span className="tob-detail-status">
          {view.promotionLabel}｜研究强度 {view.researchStrength}｜数据质量 {view.dataQualityGrade}
        </span>
      </div>

      <dl className="tob-detail-grid">
        <div>
          <dt>历史观察窗口</dt>
          <dd>
            {view.windowLabel}
            <span className="tob-dim">（口径：{view.window.method}；中心 {view.centerDate}）</span>
          </dd>
        </div>
        <div>
          <dt>历史复现</dt>
          <dd>
            {view.matchedCount} / {view.eligibleYears} 个观测年份
            <span className="tob-dim">（只用过去样本计数，不是未来概率）</span>
          </dd>
        </div>
        <div>
          <dt>{model.verificationPrefix}</dt>
          <dd>
            {view.verification.label}
            {view.verification.methods.length > 0 && (
              <span className="tob-dim">（方法：{view.verification.methods.join('、')}）</span>
            )}
            <span className="tob-dim">{view.verification.note}</span>
          </dd>
        </div>
      </dl>

      <div className="tob-detail-years">
        <span className="tob-detail-years-label">历史年份</span>
        {view.observations.map((o) => (
          <button
            key={o.campaignId}
            className={`tob-year${o.inWindow === false ? ' outside' : ''}`}
            onClick={() =>
              onSelect({ kind: 'campaign', id: o.campaignId, timelineEntryId: o.timelineEntryId })
            }
            title={`${o.title}（研究观察起点 ${o.date}）—— 打开完整历史案例`}
          >
            {o.year} · {o.md}
          </button>
        ))}
      </div>

      <p className="tob-detail-why">
        <strong>为什么值得看：</strong>
        {view.explanation}
      </p>

      <p className="tob-detail-mech">
        <strong>观察机制：</strong>
        {view.patternTypeLabel}（
        {view.driftFlag === 'STABLE' ? '前后半段稳定' : `漂移 ${view.driftFlag ?? '未判定'}`}）
      </p>

      <p className="tob-detail-limit">
        <strong>注意：</strong>
        {view.limitations.map((l, i) => (
          <span key={i} className="tob-limit-item">
            {l}
          </span>
        ))}
      </p>

      <p className="tob-detail-disc">{view.disclaimer}</p>
    </div>
  );
}
