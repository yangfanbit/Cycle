import { useMemo, useState } from 'react';
import { samePeriodCampaigns, samePeriodWindow } from '../../data/timeline/timelineAdapter';
import type { TimelineDataSource } from '../../data/timeline/timelineTypes';
import { DATA_STATUS_CLASS, DATA_STATUS_LABEL } from '../labels';

interface SamePeriodViewProps {
  dataSource: TimelineDataSource;
  /** A股市场日期基准（Asia/Shanghai） */
  today: string;
}

const MONTH_LABEL = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

/**
 * 历史同周期查看（轻量列表视图，不是统计模型）：
 * 用户选择一个月份 → 显示历史各年份在同一时间窗口（[m-1月15日, m+1月15日]）内出现过的 Campaign。
 */
export function SamePeriodView({ dataSource, today }: SamePeriodViewProps) {
  // 默认选中当前月份（TODAY 只表示日期位置，不代表当前市场状态）
  const [month, setMonth] = useState(() => Number(today.slice(5, 7)));

  const years = useMemo(() => samePeriodCampaigns(dataSource, month), [dataSource, month]);
  const windowSample = samePeriodWindow(2026, month); // 仅用于展示窗口口径

  if (years.length === 0) {
    return (
      <section className="sp-view">
        <h3 className="tl-layer-title">历史同周期查看</h3>
        <p className="phase-text">生产数据暂无已核验历史行情（verified 层为空），无同期可查。</p>
      </section>
    );
  }

  return (
    <section className="sp-view">
      <h3 className="tl-layer-title">历史同周期查看</h3>
      <p className="sp-sub">
        选择月份，查看历史各年在同期窗口（约 {windowSample.start.slice(5)} ~ {windowSample.end.slice(5)}）内出现过哪些行情；
        仅历史列表，不是统计模型，不构成任何预测。
      </p>
      <div className="sp-months">
        {MONTH_LABEL.map((label, i) => (
          <button
            key={label}
            className={`sp-month${month === i + 1 ? ' active' : ''}`}
            onClick={() => setMonth(i + 1)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="sp-years">
        {years.map(({ year, campaigns }) => (
          <div className="sp-year-row" key={year}>
            <span className="sp-year">{year}</span>
            {campaigns.length === 0 ? (
              <span className="phase-text">无同期行情</span>
            ) : (
              campaigns.map((c) => (
                <span
                  key={c.campaign_id}
                  className={`sp-item st-dashed ${DATA_STATUS_CLASS[c.status]}`}
                  title={`${c.title}（${c.start} → ${c.end}）${c.status !== 'verified' ? '；非正式历史事实' : ''}`}
                >
                  {c.kind === 'candidate' && <em className="rc-badge">RC</em>}
                  {c.title}
                  <span className="sp-dates">
                    {c.start.slice(5)}~{c.end.slice(5)}
                  </span>
                  <span className={`st-badge ${DATA_STATUS_CLASS[c.status]}`}>
                    {DATA_STATUS_LABEL[c.status]}
                  </span>
                </span>
              ))
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
