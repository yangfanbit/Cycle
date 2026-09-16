import { useMemo, useState } from 'react';
import {
  buildTimeObservationLayer,
  defaultTimeObservationDataset,
  mdFractionInYear,
  windowBandsForYear,
  type TimeObservationDataset,
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
 * ## 视觉纪律（不得违反）
 * - Timeline 仍是第一视觉：本层只是一条**很薄的带**，不遮挡、不抢占 Campaign 主体。
 * - 不使用涨跌红绿、不使用买点箭头、不出现「推荐」/「预测」字样。
 * - 用淡底纹 + 点划线边界 + 小标签表达；与既有「提前观察参考区」同一套视觉语言。
 * - 文字一律「历史观察窗口 / 历史复现」，**不出现概率、胜率、买卖建议**。
 *
 * ## 三层信息结构
 *   Level 1  Timeline 上的历史观察窗口带（本层行）
 *   Level 2  点击后就地展开的 Pattern Summary（窗口 / 历史复现 / 年份案例 / 机制 / 限制）
 *   Level 3  点击某个年份 → 既有 Campaign Detail（不新建第四套详情）
 *
 * 没有可展示的窗口时**不渲染本层**（不显示空壳标题）。
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

  const defaultId = model.current.inWindow[0]?.patternId ?? model.current.near[0]?.patternId ?? null;
  const activeId = expandedId === undefined ? defaultId : expandedId;

  const showTodayLine = today.startsWith(`${year}-`);
  const todayFrac = showTodayLine ? yearFraction(today) : 0;

  return (
    <section className="tl-layer layer-time-observation">
      <h3 className="tl-layer-title">
        时间型观察层 · 历史观察窗口
        <span className="ctl-tag">历史样本复现 · 非预测</span>
      </h3>

      {/* 今天与历史观察窗口的日历关系（这是本层最重要的产品信息） */}
      <div className={`tob-current tob-${(model.current.inWindow[0] ?? model.current.near[0])?.proximity.toLowerCase() ?? 'none'}`}>
        <span className="tob-current-date">今天 {today}</span>
        <span className="tob-current-text">{currentText(model, today)}</span>
        <span className="tob-current-warn">
          仅表示日历位置关系，不代表市场状态，也不是买入或卖出信号。
        </span>
      </div>

      {model.views.map((v) => {
        const bands = v.window ? windowBandsForYear(v.window.start, v.window.end, year) : [];
        const yearObs = v.observations.filter((o) => o.year === year);
        const open = activeId === v.patternId;
        return (
          <div key={v.patternId}>
            <div className={`tl-row tob-row${open ? ' open' : ''}`}>
              <div className="tl-row-label">
                <button
                  className="tob-name"
                  onClick={() => setExpandedId(open ? null : v.patternId)}
                  aria-expanded={open}
                >
                  {v.title}
                </button>
                <span className="sub">
                  {v.themeScope} · {v.patternTypeLabel}
                </span>
                {v.proximity !== 'OUTSIDE' && (
                  <span className={`tob-chip tob-chip-${v.proximity.toLowerCase()}`}>
                    {v.proximityLabel}
                  </span>
                )}
                {v.exploratory && (
                  <span className="tob-chip tob-chip-explor" title="样本有限，属探索性历史规律">
                    探索性
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
                              `机制：${v.patternTypeLabel}`,
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
                    className={`tob-obs-dot${o.inWindow === false ? ' outside' : ''}`}
                    style={{ left: pct(mdFractionInYear(o.md, year)) }}
                    onClick={() =>
                      onSelect({ kind: 'campaign', id: o.campaignId, timelineEntryId: o.timelineEntryId })
                    }
                    {...(showTooltip
                      ? {
                          onMouseEnter: (e: React.MouseEvent) =>
                            showTooltip(e, `${o.title} · 研究观察起点`, [
                              `${o.date}（Early Signal）`,
                              o.inWindow === false
                                ? `该年锚点落在典型窗口（${v.windowLabel}）之外`
                                : `落在典型窗口内（${v.windowLabel}）`,
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

            {/* Level 2：Pattern Summary（就地展开，不离开页面、不遮挡 Timeline） */}
            {open && <PatternSummary view={v} onSelect={onSelect} />}
          </div>
        );
      })}

      <p className="tob-foot">
        {model.researchOnlyCount > 0 && (
          <>另有 {model.researchOnlyCount} 条时间规律处于研究层（样本不足或稳定性未达门槛），未进入 Timeline。 </>
        )}
        研究快照：{model.snapshotDate}｜数据为研究样本，未经行情人工最终核验。
      </p>
    </section>
  );
}

/** 今天与窗口关系的文案（纯日历口径；多条同时命中时不人为只保留一个） */
function currentText(
  model: ReturnType<typeof buildTimeObservationLayer>,
  today: string,
): string {
  const { inWindow, near } = model.current;
  const md = today.slice(5);
  if (inWindow.length > 0) {
    return `${md} 位于 ${inWindow
      .map((v) => `「${v.title}」的历史观察窗口（${v.windowLabel}）`)
      .join('、')} 内 —— 该时段在历史研究样本中多次出现主题观察起点。`;
  }
  if (near.length > 0) {
    return `接近 ${near
      .map((v) => `「${v.title}」的历史观察窗口（${v.windowLabel}，距边界 ${v.distanceDays} 天）`)
      .join('、')}。`;
  }
  return model.current.emptyNote ?? '当前没有发现处于历史时间观察窗口的模式。';
}

/** Level 2：Pattern Summary */
function PatternSummary({
  view,
  onSelect,
}: {
  view: TimeObservationView;
  onSelect: (sel: Selection) => void;
}) {
  return (
    <div className="tob-detail" role="region" aria-label={`${view.title} 摘要`}>
      <div className="tob-detail-head">
        <strong>{view.title}</strong>
        <span className="tob-detail-type">
          {view.themeScope} · {view.patternTypeLabel}
        </span>
        <span className="tob-detail-status">
          {view.status}｜研究强度 {view.researchStrength}｜数据质量 {view.dataQualityGrade}
        </span>
      </div>

      <dl className="tob-detail-grid">
        <div>
          <dt>历史观察窗口</dt>
          <dd>
            {view.windowLabel}
            <span className="tob-dim">
              （口径：{view.window.method}；中心 {view.centerDate}）
            </span>
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
          <dt>年份案例</dt>
          <dd className="tob-years">
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
          </dd>
        </div>
      </dl>

      <p className="tob-detail-why">
        <strong>为什么值得看：</strong>
        {view.explanation}
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
