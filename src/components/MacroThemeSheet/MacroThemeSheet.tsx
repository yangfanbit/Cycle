import { useMemo } from 'react';
import type { ThemeAnnualRow } from '../../data/timeline/themeAnnualWindow';
import { mainRiseOf } from '../../data/timeline/themeAnnualWindow';
import { LIFECYCLE_LABEL } from '../labels';
import type { Selection } from '../Timeline/Timeline';

/**
 * Macro Theme 附页（drill-down）。
 *
 * 首页是「地图」，这里是「明细库」—— 数据库级细节**只在这里**展示：
 * 按年份列出该主题下的具体历史 Campaign / Research Candidate，
 * 可进入 CampaignDetail（完整生命周期 / 驱动因素 / 事件证据 / 冲突 / Structural Analogy）。
 */

interface MacroThemeSheetProps {
  row: ThemeAnnualRow;
  onClose: () => void;
  onOpenCampaign: (id: string, year: number) => void;
}

export function MacroThemeSheet({ row, onClose, onOpenCampaign }: MacroThemeSheetProps) {
  const byYear = useMemo(() => {
    const m = new Map<number, ThemeAnnualRow['objects']>();
    for (const o of row.objects) {
      const y = Number(o.start.slice(0, 4));
      const arr = m.get(y);
      if (arr) arr.push(o);
      else m.set(y, [o]);
    }
    return [...m.entries()].sort((a, b) => a[0] - b[0]);
  }, [row]);

  return (
    <div className="theme-sheet" role="dialog" aria-label={`${row.label} 历史视图`}>
      <div className="ts-head">
        <div>
          <h2 className="ts-title">{row.label}</h2>
          <p className="ts-sub">
            历史出现 {row.occurrences} 次 · 覆盖 {row.comparableYears} 个可比年份
            {row.years.length > 0 ? `（${row.years[0]}–${row.years[row.years.length - 1]}）` : ''} ·{' '}
            {row.campaignCount} Campaign / {row.candidateCount} Research Candidate
          </p>
        </div>
        <button className="ts-close" onClick={onClose} aria-label="关闭">
          ×
        </button>
      </div>

      <p className="ts-note">
        以下为研究记录明细（按起始年份分组）。完整生命周期、驱动因素、事件证据、
        日期分歧与结构类比在点击任一对象后进入「完整历史案例」查看。
        本页是历史记录，**不是概率、胜率、推荐分或预测**。
      </p>

      {row.theme === null && (
        <p className="ts-note">
          研究未把这些对象归属到具体行业 / 板块。此处<strong>不编造行业名</strong>，
          只按「未标注大主题」归组 —— 这是 Research 标注的缺口，不是产品推断。
        </p>
      )}

      {byYear.map(([y, list]) => (
        <div className="ts-year" key={y}>
          <h3 className="ts-year-h">{y}</h3>
          <ul className="ts-list">
            {list.map((o) => {
              const mr = mainRiseOf(o);
              const isRc = o.kind === 'candidate';
              return (
                <li key={o.campaign_id} className={`ts-item${isRc ? ' rc' : ''}`}>
                  <button className="ts-open" onClick={() => onOpenCampaign(o.campaign_id, y)}>
                    <span className="ts-item-title">
                      {isRc && <em className="rc-badge">RC</em>}
                      {o.title}
                    </span>
                    <span className="ts-item-meta">
                      {o.start} → {o.end}
                      {o.openEnded ? '（结束未确定）' : ''}
                    </span>
                    <span className="ts-item-meta dim">
                      {mr
                        ? `主要炒作 ${mr.start} → ${mr.end}`
                        : '主要炒作：研究未标注'}
                      {(o.lifecycle ?? []).length > 0
                        ? ` · 生命周期 ${(o.lifecycle ?? [])
                            .map((s) => LIFECYCLE_LABEL[s.stage as keyof typeof LIFECYCLE_LABEL] ?? s.stage)
                            .join(' → ')}`
                        : ' · 生命周期：研究未标注'}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
