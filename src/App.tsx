import { useMemo, useState } from 'react';
import { CampaignDetail } from './components/CampaignDetail/CampaignDetail';
import { OpportunityRadar } from './components/OpportunityRadar/OpportunityRadar';
import { RuleDetail } from './components/RuleDetail/RuleDetail';
import { Timeline, type Selection } from './components/Timeline/Timeline';
import { allCampaigns, campaignById, ruleById } from './data';
import { previewTimelineSource, verifiedTimelineSource } from './data/timeline/timelineAdapter';
import type { TimelineCampaign } from './data/timeline/timelineTypes';
import { marketTodayISO } from './utils';

/** ?preview=1 启用 Research 开发预览；默认生产数据（不做运行时网络访问，保持静态 PWA） */
function previewEnabled(): boolean {
  return new URLSearchParams(window.location.search).get('preview') === '1';
}

export default function App() {
  // A股市场日期基准：Asia/Shanghai（不随用户机器时区漂移）
  const today = useMemo(() => marketTodayISO(), []);
  const preview = useMemo(() => previewEnabled(), []);

  // Timeline 数据源：verified（生产）或 preview（Cycle-Research 研究预览）。
  // 未来 preview → provisional → verified 的切换只改 Adapter，不改 UI。
  const dataSource = useMemo(
    () => (preview ? previewTimelineSource() : verifiedTimelineSource()),
    [preview],
  );
  const availableYears = useMemo(() => dataSource.years(), [dataSource]);

  const [year, setYear] = useState(() => Number(today.slice(0, 4)));
  const [selection, setSelection] = useState<Selection>(null);

  const yearData = useMemo(() => dataSource.yearData(year), [dataSource, year]);

  // 预览 Campaign 索引（供详情面板解析；预览数据不进入生产 allCampaigns）
  const previewCampaignsById = useMemo(() => {
    const map = new Map<string, TimelineCampaign>();
    for (const y of dataSource.years()) {
      for (const c of dataSource.yearData(y).campaigns) map.set(c.campaign_id, c);
    }
    return map;
  }, [dataSource]);

  const selectedRule = selection?.kind === 'rule' ? ruleById.get(selection.id) : undefined;
  // 生产 verified 优先；预览 Campaign 仅在预览模式下解析
  const selectedCampaign =
    selection?.kind === 'campaign'
      ? campaignById.get(selection.id) ?? (preview ? previewCampaignsById.get(selection.id) : undefined)
      : undefined;

  return (
    <>
      <header className="app-header">
        <h1 className="app-title">A股机会时间轴</h1>
        <p className="app-subtitle">历史规律 × 题材轮动 × 事件节奏 × 提前观察</p>
        <div className="app-today">
          <span className="year-switch">
            <button onClick={() => setYear((y) => y - 1)} aria-label="上一年">
              ‹
            </button>
            <span className="year-label">{year}</span>
            <button onClick={() => setYear((y) => y + 1)} aria-label="下一年">
              ›
            </button>
          </span>
          {/* 数据源可展示年份（不硬编码：来自 TimelineDataSource.years()） */}
          {availableYears.length > 0 && (
            <span className="year-chips">
              {availableYears.map((y) => (
                <button
                  key={y}
                  className={`year-chip${y === year ? ' on' : ''}`}
                  onClick={() => setYear(y)}
                >
                  {y}
                </button>
              ))}
            </span>
          )}
          <span>{today}</span>
        </div>
      </header>

      {/* 预览模式横幅：开发预览数据，非正式历史事实 */}
      {preview && (
        <div className="preview-banner" role="status">
          <strong>开发预览数据</strong>
          <span>
            数据来自 Cycle-Research，尚未全部完成人工最终核验，仅用于界面与历史模式探索；非正式历史事实。
          </span>
          <a className="banner-link" href={window.location.pathname}>
            返回生产数据
          </a>
        </div>
      )}

      <main className="app-main">
        <Timeline
          year={year}
          today={today}
          selection={selection}
          onSelect={setSelection}
          campaigns={yearData.campaigns}
          sourceKind={dataSource.kind}
        />
        {/* 生产模式且 verified 为空：提供开发预览入口（不把 preview 当生产数据） */}
        {!preview && allCampaigns.length === 0 && (
          <div className="prod-empty-note">
            当前暂无已核验历史行情（历史核验尚未开始）。
            <a className="banner-link" href={`${window.location.pathname}?preview=1`}>
              开发预览：查看 Research Preview
            </a>
          </div>
        )}
        <OpportunityRadar
          today={today}
          onSelectRule={(id) => setSelection({ kind: 'rule', id })}
        />
      </main>

      {selectedRule && (
        <RuleDetail
          rule={selectedRule}
          today={today}
          onOpenCampaign={(id) => setSelection({ kind: 'campaign', id })}
          onClose={() => setSelection(null)}
        />
      )}
      {selectedCampaign && (
        <CampaignDetail
          campaign={selectedCampaign}
          onOpenRule={(id) => setSelection({ kind: 'rule', id })}
          onClose={() => setSelection(null)}
        />
      )}
    </>
  );
}
