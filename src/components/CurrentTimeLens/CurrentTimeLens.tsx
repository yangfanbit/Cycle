import { useMemo } from 'react';
import { currentTimeLens, type LensHistoricalEntry } from '../../data/timeline/currentTimeLens';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import type { Selection } from '../Timeline/Timeline';
import { DATA_STATUS_CLASS, DATA_STATUS_LABEL } from '../labels';
import { isInPreObservation, PRE_OBSERVATION_LABEL } from '../../data/timeline/preObservation';

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
    <section className="ctl-view" aria-label="当前时间上下文">
      <h3 className="tl-layer-title">
        当前时间上下文
        <span className="ctl-tag">补充查看 · 非主视图</span>
      </h3>

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
                      key={e.campaign_id}
                      entry={e}
                      active={selection?.kind === 'campaign' && selection.id === e.campaign_id}
                      onClick={() => onSelect({ kind: 'campaign', id: e.campaign_id })}
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
                <li className="ctl-driver-row" key={`${d.year}-${d.campaign_id}`}>
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
