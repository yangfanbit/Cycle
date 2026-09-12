import { useMemo } from 'react';
import { anchorResolver, rules, windowsOfRule } from '../../data';
import { computeWindowStatus, diffDays, type WindowPhase } from '../../utils';

interface RadarItem {
  ruleId: string;
  name: string;
  phase: WindowPhase;
  /** 距提前观察区开始天数（<=0 表示已进入） */
  daysToPreheat: number;
  /** 距典型窗口开始天数（<=0 表示已在窗口内） */
  daysToStart: number;
  windowRange: string;
}

const BUCKETS = [
  { label: '未来 7 天', days: 7 },
  { label: '未来 30 天', days: 30 },
  { label: '未来 60 天', days: 60 },
  { label: '未来 90 天', days: 90 },
];

interface OpportunityRadarProps {
  today: string;
  onSelectRule: (ruleId: string) => void;
}

/**
 * 未来关注窗口：按"距离提前观察区"分桶展示候选规律。
 * 不叫"买入机会"，不提供任何买卖信号。
 */
export function OpportunityRadar({ today, onSelectRule }: OpportunityRadarProps) {
  const items = useMemo(() => {
    const list: RadarItem[] = [];
    for (const rule of rules) {
      const window = windowsOfRule(rule.rule_id)[0];
      if (!window) continue;
      const status = computeWindowStatus(window, today, anchorResolver);
      if (!status) continue;
      const { occurrence, phase } = status;
      const daysToPreheat = diffDays(today, occurrence.preheatStart);
      const daysToStart = diffDays(today, occurrence.start);
      // 已过窗口的规则：下一次窗口在明年，daysToPreheat 已由 NOT_ACTIVE 分支给出未来值
      if (phase === 'ENDED') continue;
      list.push({
        ruleId: rule.rule_id,
        name: rule.base_sector,
        phase,
        daysToPreheat,
        daysToStart,
        windowRange: `${occurrence.start} → ${occurrence.end}`,
      });
    }
    return list;
  }, [today]);

  return (
    <section className="radar">
      <h3 className="tl-layer-title">未来关注窗口（提前观察）</h3>
      <div className="radar-grid">
        {BUCKETS.map((bucket) => {
          const inBucket = items.filter((it) => {
            const key = it.phase === 'PRE_HEAT' || it.phase === 'ACTIVE' ? 0 : it.daysToPreheat;
            return key <= bucket.days && (bucket.days === 7 || !isInSmallerBucket(key, bucket.days));
          });
          return (
            <div className="radar-col" key={bucket.days}>
              <h3>{bucket.label}</h3>
              {inBucket.length === 0 && <div className="empty-note">暂无</div>}
              {inBucket.map((it) => (
                <div
                  className="radar-item"
                  key={it.ruleId}
                  onClick={() => onSelectRule(it.ruleId)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="r-name">
                    {it.phase === 'ACTIVE' ? '🟢' : it.phase === 'PRE_HEAT' ? '🟡' : '⚪'} {it.name}
                  </div>
                  <div className="r-meta">
                    {it.phase === 'ACTIVE'
                      ? '当前窗口'
                      : it.phase === 'PRE_HEAT'
                        ? `提前观察中 ｜ 约 ${it.daysToStart} 天后进入窗口`
                        : `距离典型窗口 ${it.daysToStart} 天`}
                  </div>
                  <div className="r-meta">{it.windowRange}</div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
      <p className="disclaimer">
        以上为候选规律的日历状态提示，代表"历史上值得提前观察的时间窗口"，不构成买卖建议。
      </p>
    </section>
  );
}

function isInSmallerBucket(key: number, bucketDays: number): boolean {
  const smaller = BUCKETS.filter((b) => b.days < bucketDays).map((b) => b.days);
  return smaller.some((d) => key <= d);
}
