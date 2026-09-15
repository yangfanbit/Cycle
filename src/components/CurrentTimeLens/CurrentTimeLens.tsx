import { useMemo } from 'react';
import { currentTimeLens, type LensHistoricalEntry } from '../../data/timeline/currentTimeLens';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import { timelineEntryId } from '../../data/timeline/entryIdentity';
import type { Selection } from '../Timeline/Timeline';
import { isEntrySelected } from '../Timeline/Timeline';
import { DATA_STATUS_CLASS, DATA_STATUS_LABEL } from '../labels';
import { isInPreObservation, PRE_OBSERVATION_LABEL } from '../../data/timeline/preObservation';
import {
  ATTENTION_LABEL,
  PATTERN_LABEL,
  PHASE_LABEL,
  buildCurrentLensV2,
  type AttentionItem,
  type CurrentLensV2,
} from '../../data/timeline/researchAttention';

interface CurrentTimeLensProps {
  dataSource: TimelineDataSource;
  /** A股市场日期基准（Asia/Shanghai） */
  today: string;
  /** 现有选中态（与 Timeline 共用，不新建 state management） */
  selection: Selection;
  /** 现有选中回调（点击 Lens 条目 → 打开 Campaign Detail） */
  onSelect: (sel: Selection) => void;
}

/**
 * Current Time Lens v0（V1.8.1 起：降级为「当前时间上下文」补充摘要，不再是页面第一视觉）。
 *
 * 回答：「今天这个时间点，历史上附近发生过什么？」
 * 呈现：A 时间定位 → B 同期行情（按年份，压缩为一行一年）→ C/D 可能相关因素。
 *
 * 刻意不做：预测（今年一定会发生什么）、交易建议（现在应该买什么）、
 * 概率 / 频次统计（把「N 次」当视觉重点）。
 *
 * 一切数据来自 App 注入的 TimelineDataSource（= exports/timeline_export_v1.json）。
 * 不做网络请求、不新建数据结构、不写库。
 */
export function CurrentTimeLens({ dataSource, today, selection, onSelect }: CurrentTimeLensProps) {
  const lens = useMemo(() => currentTimeLens(dataSource, today), [dataSource, today]);
  // v2 三层：A. A股整体环境 / B. 当前 Theme · Theme Cycle / C. Research Attention
  const v2 = useMemo(() => buildCurrentLensV2(dataSource, today), [dataSource, today]);

  // 无数据源年份（生产 verified 为空）→ 明确说明，不伪装成「历史没有机会」
  if (dataSource.years().length === 0) {
    return (
      <section className="ctl-view" aria-label="当前时间上下文">
        <h3 className="tl-layer-title">
          当前时间上下文
          <span className="ctl-tag">补充查看 · 非主视图</span>
        </h3>
        <p className="ctl-sub">
          今天（{lens.position.today}）位于约 {lens.position.windowLabel} 这一时间窗口。
        </p>
        <p className="ctl-empty">
          当前研究数据未覆盖：暂无已核验的同周期历史行情可比对（不是「历史没有机会」）。
        </p>
      </section>
    );
  }

  const yearsWithData = lens.samePeriod.filter((r) => r.entries.length > 0);

  // 提前观察参考区（V1.8.2 / V1.8.2.1）：今天是否落在某历史行情 / 主题的提前观察参考区内。
  // 语义严格为「历史研究位置」，必须同时给出「不代表本年度预测」的限定。
  const preObsHits = yearsWithData.flatMap((row) =>
    row.entries.filter((e) => isInPreObservation(e.campaign, today)),
  );

  return (
    <section className="ctl-view" aria-label="当前时间研究导航">
      <h3 className="tl-layer-title">
        当前时间研究导航
        <span className="ctl-tag">研究导航 · 非预测</span>
      </h3>

      {/* ============ v2 三层（研究导航核心） ============ */}
      <LensV2 v2={v2} selection={selection} onSelect={onSelect} />

      {/* ============ 附：日历同期（Calendar Lens） ============ */}
      <h4 className="ctl2-sublayer">
        日历同期视角
        <span className="ctl-hint">（与「历史同期（日历）」章节同口径的紧凑呈现）</span>
      </h4>

      {/* ---------- A. 时间定位 ---------- */}
      <div className="ctl-position">
        <span className="ctl-date">{lens.position.today}</span>
        <span className="ctl-month">{lens.position.monthLabel}</span>
        <span className="ctl-window">
          同期窗口 <em>{lens.position.windowLabel}</em>
          <span className="ctl-hint">（{lens.position.window.start} ~ {lens.position.window.end}）</span>
        </span>
      </div>
      <p className="ctl-question">历史上这个时间窗口附近，出现过哪些主题？</p>

      {/* 提前观察参考区提示（若有）：今天落在历史某主题的提前观察参考区内 */}
      {preObsHits.length > 0 && (
        <div className="ctl-pre-obs" role="note">
          <strong>{PRE_OBSERVATION_LABEL}</strong>
          <span className="ctl-pre-obs-body">
            今天处于历史主题「{preObsHits.map((e) => e.title).join('、')}」的{PRE_OBSERVATION_LABEL}
            内（主题形成前 30 个自然日的研究浏览参考）。
          </span>
          <span className="ctl-pre-obs-warn">
            仅为历史研究位置，不代表本年度预测，也不是买入建议。
          </span>
        </div>
      )}

      {/* ---------- B + C. 历史同期（按年份，压缩呈现） ---------- */}
      {lens.uncovered ? (
        <p className="ctl-empty">
          当前研究数据未覆盖：历史各年的同期窗口内均无研究数据（不是「历史没有机会」）。
        </p>
      ) : (
        <>
          <div className="ctl-years">
            {yearsWithData.map((row) => (
              <div className="ctl-year" key={row.year}>
                <span className="ctl-year-label">{row.year}</span>
                <div className="ctl-entries">
                  {row.entries.map((e) => (
                    <LensEntry
                      key={e.entryId}
                      entry={e}
                      // 高亮按展示实例（entryId）比较：跨年 Campaign 不会在多个年份同时高亮（F-MED-6）
                      active={isEntrySelected(selection, e.entryId)}
                      onClick={() =>
                        onSelect({
                          kind: 'campaign',
                          id: e.campaign_id,
                          timelineEntryId: e.entryId,
                        })
                      }
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="ctl-coverage">
            历史同期共覆盖 {yearsWithData.length} 个年份的研究数据（仅表示数据覆盖情况，不构成任何概率或预测）。
          </p>
        </>
      )}

      {/* ---------- D. 可能相关因素（标签从「可调驱动」改为「可能相关因素」） ---------- */}
      <div className="ctl-drivers">
        <h4 className="ctl-drivers-title">可能相关因素</h4>
        {lens.possibleDrivers.length === 0 ? (
          <p className="ctl-empty">当前研究数据未覆盖：暂无可用归因（不编造）。</p>
        ) : (
          <>
            <p className="ctl-drivers-sub">
              以下为历史同期行情在 Research 层记录的相关因素，语义为「可能相关因素」，不是因果结论、不是交易建议。
            </p>
            <ul className="ctl-driver-list">
              {lens.possibleDrivers.map((d) => (
                <li className="ctl-driver-row" key={timelineEntryId(d.campaign_id, d.year)}>
                  <span className="ctl-driver-year">{d.year}</span>
                  <button
                    className="ctl-driver-title"
                    onClick={() => onSelect({ kind: 'campaign', id: d.campaign_id })}
                  >
                    {d.title}
                  </button>
                  <span className="ctl-driver-labels">
                    {d.labels.map((l) => (
                      <span className="ctl-driver-chip" key={l}>
                        {l}
                      </span>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}

/** 单条历史同期条目：Year + Campaign + Phase 为历史事实主体（不做「N 次」强调） */
function LensEntry({
  entry,
  active,
  onClick,
}: {
  entry: LensHistoricalEntry;
  active: boolean;
  onClick: () => void;
}) {
  const statusLabel = DATA_STATUS_LABEL[entry.status];
  const dateRange = `${entry.start.slice(5)} ~ ${entry.end.slice(5)}${entry.openEnded ? '（观察中）' : ''}`;
  return (
    <button
      className={`ctl-entry ${active ? 'on' : ''} ${DATA_STATUS_CLASS[entry.status]}`}
      onClick={onClick}
      title={`${entry.title}｜历史区间 ${entry.start} → ${entry.end}\n${
        entry.phaseLabel ? `当时处于：${entry.phaseLabel}` : '历史阶段未标注'
      }\n数据状态：${statusLabel}${entry.status !== 'verified' ? '（非正式历史事实）' : ''}`}
    >
      {entry.kind === 'candidate' && <em className="rc-badge">RC</em>}
      <span className="ctl-entry-title">{entry.title}</span>
      <span className="ctl-entry-dates">{dateRange}</span>
      {/* C. 历史阶段映射：明确写成「当时处于」——历史上那个窗口的阶段，不是当前阶段 */}
      <span className="ctl-entry-phase">
        {entry.phaseLabel ? (
          <>
            当时处于：<strong>{entry.phaseLabel}</strong>
            {entry.phaseHit && (
              <span className="ctl-phase-hit">
                （{entry.phaseHit.start.slice(5)}~{entry.phaseHit.end.slice(5)}）
              </span>
            )}
            {entry.phaseAlso.length > 0 && (
              <span className="ctl-phase-also">，另有 {entry.phaseAlso.join(' / ')}</span>
            )}
          </>
        ) : (
          <span className="ctl-phase-none">历史阶段未标注</span>
        )}
      </span>
      <span className={`st-badge ${DATA_STATUS_CLASS[entry.status]}`}>{statusLabel}</span>
    </button>
  );
}

/* ================= Current Time Lens v2 三层（研究导航） ================= */

/**
 * v2 三层：
 *   A. A股整体环境 —— 无整体市场周期模型 → Unknown（**绝不**从行业 Campaign 反推大盘牛熊）
 *   B. 当前 Theme / Theme Cycle —— 无当前年份数据时**诚实空态**；NO LOOK-AHEAD
 *   C. Research Attention —— 状态分类（不是评分 / 概率 / 买卖信号）
 */
function LensV2({
  v2,
  selection,
  onSelect,
}: {
  v2: CurrentLensV2;
  selection: Selection;
  onSelect: (sel: Selection) => void;
}) {
  const isSelected = (item: AttentionItem) =>
    selection?.kind === 'campaign' && selection.id === item.campaign_id;

  return (
    <>
      {/* ---------- Layer A：A股整体环境 ---------- */}
      <div className="ctl2-layer">
        <h4 className="ctl2-layer-title">A · A股整体环境</h4>
        <p className="ctl2-unknown">{v2.layerA.label}</p>
        <p className="ctl2-note">{v2.layerA.note}</p>
      </div>

      {/* ---------- Layer B：当前 Theme / Theme Cycle ---------- */}
      <div className="ctl2-layer">
        <h4 className="ctl2-layer-title">
          B · 当前 Theme / Theme Cycle
          <span className="ctl2-badge">{v2.currentYear}</span>
        </h4>
        <p className={`ctl2-note${v2.layerB.hasCurrentData ? '' : ' ctl2-note-empty'}`}>
          {v2.layerB.note}
        </p>
        <p className="ctl2-sub">
          研究覆盖内的 Theme Cycle（{v2.layerB.coverage.from ?? '—'}–{v2.layerB.coverage.to ?? '—'}，
          历史参考，不是当前状态）
        </p>
        <div className="ctl2-cycles">
          {v2.layerB.cycles.map((c) => (
            <div className="ctl2-cycle" key={c.key}>
              <div className="ctl2-cycle-head">
                <span className="ctl2-cycle-name">
                  {c.macroTheme ?? c.themeCycleId ?? '未标注 Theme Cycle'}
                </span>
                <span className="ctl2-cycle-pattern">{PATTERN_LABEL[c.pattern]}</span>
                <span className="ctl2-cycle-count">{c.components.length} 条</span>
              </div>
              <ul className="ctl2-components">
                {c.components.map((comp) => (
                  <li
                    key={comp.campaign.campaign_id}
                    className={`ctl2-comp att-${comp.attention.state.toLowerCase()}`}
                  >
                    <button
                      className="ctl2-comp-title"
                      onClick={() => onSelect({ kind: 'campaign', id: comp.campaign.campaign_id })}
                    >
                      {comp.campaign.kind === 'candidate' && <em className="rc-badge">RC</em>}
                      {comp.campaign.title}
                    </button>
                    <span className="ctl2-comp-phase">{PHASE_LABEL[comp.phase]}</span>
                    <span className="ctl2-comp-att">{ATTENTION_LABEL[comp.attention.state]}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* ---------- Layer C：Research Attention ---------- */}
      <div className="ctl2-layer">
        <h4 className="ctl2-layer-title">C · Research Attention（研究关注）</h4>
        <p className="ctl2-note">{v2.layerC.note}</p>
        <div className="ctl2-att-grid">
          <AttentionColumn
            state="ACTIVE_RESEARCH"
            items={v2.layerC.active}
            emptyNote={
              '现有研究数据中没有处于形成 / 确认 / 扩张阶段的正式 Campaign。' +
              `这不是错误 —— 研究数据覆盖至 ${v2.layerB.coverage.to ?? '—'}，其记录的正式 Campaign 均已走到结束阶段。`
            }
            isSelected={isSelected}
            onSelect={onSelect}
          />
          <AttentionColumn
            state="WATCH"
            items={v2.layerC.watch}
            emptyNote="当前没有需要保持观察的研究对象。"
            isSelected={isSelected}
            onSelect={onSelect}
          />
          <AttentionColumn
            state="HISTORICAL_REFERENCE"
            items={v2.layerC.reference.slice(0, 6)}
            emptyNote="无历史参考条目。"
            isSelected={isSelected}
            onSelect={onSelect}
            moreCount={Math.max(v2.layerC.referenceTotal - 6, 0)}
          />
        </div>
      </div>
    </>
  );
}

/** Research Attention 的一列（状态分类；不是评分榜） */
function AttentionColumn({
  state,
  items,
  emptyNote,
  isSelected,
  onSelect,
  moreCount = 0,
}: {
  state: 'ACTIVE_RESEARCH' | 'WATCH' | 'HISTORICAL_REFERENCE';
  items: AttentionItem[];
  emptyNote: string;
  isSelected: (item: AttentionItem) => boolean;
  onSelect: (sel: Selection) => void;
  moreCount?: number;
}) {
  return (
    <div className={`ctl2-att-col att-${state.toLowerCase()}`}>
      <h5 className="ctl2-att-title">{ATTENTION_LABEL[state]}</h5>
      {items.length === 0 ? (
        <p className="ctl2-att-empty">{emptyNote}</p>
      ) : (
        <ul className="ctl2-att-list">
          {items.map((i) => (
            <li key={i.campaign_id}>
              <button
                className={`ctl2-att-item${isSelected(i) ? ' on' : ''}`}
                onClick={() => onSelect({ kind: 'campaign', id: i.campaign_id })}
              >
                <span className="ctl2-att-name">
                  {i.kind === 'candidate' && <em className="rc-badge">RC</em>}
                  {i.title}
                </span>
                <span className="ctl2-att-meta">
                  {i.year} · {i.phaseLabel}
                  {i.macroTheme ? ` · ${i.macroTheme}` : ''}
                </span>
                <span className="ctl2-att-why">{i.reasons.slice(1).join('；') || '—'}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {moreCount > 0 && <p className="ctl2-att-more">另有 {moreCount} 条历史参考（未展开）。</p>}
    </div>
  );
}
