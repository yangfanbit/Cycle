import { useMemo, useState } from 'react';
import { CampaignDetail } from './components/CampaignDetail/CampaignDetail';
import { OpportunityRadar } from './components/OpportunityRadar/OpportunityRadar';
import { RuleDetail } from './components/RuleDetail/RuleDetail';
import { Timeline, type Selection } from './components/Timeline/Timeline';
import { campaignById, ruleById } from './data';
import { todayISO } from './utils';

export default function App() {
  const today = useMemo(() => todayISO(), []);
  const [year, setYear] = useState(() => Number(today.slice(0, 4)));
  const [selection, setSelection] = useState<Selection>(null);

  const selectedRule = selection?.kind === 'rule' ? ruleById.get(selection.id) : undefined;
  const selectedCampaign = selection?.kind === 'campaign' ? campaignById.get(selection.id) : undefined;

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
          <span>{today}</span>
        </div>
      </header>

      <main className="app-main">
        <Timeline year={year} today={today} selection={selection} onSelect={setSelection} />
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
