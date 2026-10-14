/**
 * 外部季节性观察雷达 —— **外部研究线索**视图（与历史 SeasonalMap 并列但**来源分离**）。
 *
 * ★ 与上方 SeasonalMap 的**根本区别**（页面上必须可见）：
 *   - SeasonalMap：ThreeC **从历史数据中得到的**窗口（研究结果）
 *   - 本视图：**外部资料声称的**季节性线索（未验证）
 *
 * ★ 本组件**不**引入分数、排名、概率；窗口活跃**不**提升成熟度。
 * ★ 无映射时直接展示 `UNMAPPED` 与原因，**不隐藏空白**。
 */
import { useMemo, useState } from 'react';
import { FluEventMap } from './FluEventMap';
import {
  EXTERNAL_CALENDAR_NOTE,
  EXTERNAL_SOURCE_LABEL,
  MATURITY_LABEL,
  RELATION_LABEL,
  externalCalendarDoc,
  externalCalendarEntries,
  externalSourceById,
  windowRelationOf,
  windowTextOf,
  type ExternalCalendarEntry,
  type WindowRelation,
} from '../../data/timeline/externalSeasonalCalendar';

/** 用户 2026-10-13 指定的优先展示四项 */
const PRIORITY_IDS = ['EXT-11', 'EXT-08', 'EXT-12', 'EXT-09'];

/**
 * ★ 哪些外部线索**已有**历史事件地图（2026-10-14 起）。
 * 只有已建成 `flu_historical_events_v0_1.json` 的主题才显示入口 ——
 * 其余主题**不显示空壳**（避免暗示「已研究过」）。
 */
const EVENT_MAP_IDS = ['EXT-12'];

const RELATION_CLASS: Record<WindowRelation, string> = {
  IN_WINDOW: 'esr-rel-in',
  UPCOMING: 'esr-rel-soon',
  PASSED: 'esr-rel-past',
  NO_FIXED_WINDOW: 'esr-rel-none',
  INSUFFICIENT_DATE: 'esr-rel-none',
};

function EntryCard({ e, today }: { e: ExternalCalendarEntry; today: string }) {
  const rel = windowRelationOf(e, today);
  const sources = e.source_ids.map((s) => externalSourceById(s)).filter(Boolean);
  return (
    <li className="esr-card" data-entry-id={e.id} data-relation={rel}>
      <div className="esr-card-head">
        <span className="esr-name">{e.name}</span>
        <span className={`esr-rel ${RELATION_CLASS[rel]}`}>{RELATION_LABEL[rel]}</span>
      </div>

      <dl className="esr-meta">
        <dt>原始窗口</dt>
        <dd className="esr-window">{windowTextOf(e)}</dd>

        <dt>外部来源</dt>
        <dd className="esr-source">
          {sources.map((s) => (
            <span key={s!.source_id} className="esr-src-tag" title={s!.note}>
              {s!.title}
            </span>
          ))}
        </dd>

        <dt>ThreeC 映射</dt>
        <dd className="esr-map">
          {e.mapping.status === 'MAPPED' ? (
            <>
              <span className="esr-theme">{e.mapping.macro_theme}</span>
              <span className="esr-map-basis">{e.mapping.basis}</span>
            </>
          ) : (
            <span className="esr-unmapped">
              未映射 —— {e.mapping.reason}
            </span>
          )}
        </dd>

        <dt>研究成熟度</dt>
        <dd className="esr-maturity">
          <span className="esr-mat-tag">{MATURITY_LABEL[e.maturity]}</span>
          <span className="esr-mat-note">（未经 ThreeC 验证）</span>
        </dd>

        {e.source_note && (
          <>
            <dt>不确定性</dt>
            <dd className="esr-caveat">{e.source_note}</dd>
          </>
        )}
      </dl>

      {EVENT_MAP_IDS.includes(e.id) && <FluEventMap />}

      <div className="esr-foot">
        <span className="esr-id">{e.id}</span>
        <span className="esr-rev">
          更新 {e.revision[e.revision.length - 1].date}
        </span>
      </div>
    </li>
  );
}

export function ExternalSeasonalRadar({ today }: { today: string }) {
  const [showAll, setShowAll] = useState(false);
  const [catFilter, setCatFilter] = useState<string>('ALL');

  const doc = externalCalendarDoc();
  const all = externalCalendarEntries();

  const categories = useMemo(
    () => ['ALL', ...Array.from(new Set(all.map((e) => e.category)))],
    [all],
  );

  const priority = all.filter((e) => PRIORITY_IDS.includes(e.id));
  const rest = all.filter((e) => !PRIORITY_IDS.includes(e.id));
  const restShown = catFilter === 'ALL'
    ? rest
    : rest.filter((e) => e.category === catFilter);

  return (
    <section className="esr" aria-label="外部季节性观察雷达">
      <div className="esr-head">
        <h2 className="esr-title">外部季节性观察雷达</h2>
        <span className="esr-source-badge">{EXTERNAL_SOURCE_LABEL}</span>
      </div>

      <p className="esr-note">{EXTERNAL_CALENDAR_NOTE}</p>
      <p className="esr-count">
        共 <strong>{all.length}</strong> 项外部线索 · 版本 <code>{doc.artifact_version}</code> ·
        生成 {doc.generated_at}
        <span className="esr-vs">
          （上方地图是 ThreeC <strong>从历史数据得到</strong>的窗口；本视图是
          <strong>外部资料声称</strong>的窗口，两者来源不同）
        </span>
      </p>

      <h3 className="esr-sub">当前优先观察（{priority.length} 项）</h3>
      <ul className="esr-list">
        {priority.map((e) => <EntryCard key={e.id} e={e} today={today} />)}
      </ul>

      <div className="esr-rest-head">
        <h3 className="esr-sub">全部线索（{all.length} 项）</h3>
        <button
          type="button"
          className="esr-toggle"
          aria-expanded={showAll}
          onClick={() => setShowAll((v) => !v)}
        >
          {showAll ? '收起其余线索' : `展开其余 ${rest.length} 项`}
        </button>
      </div>

      {showAll && (
        <>
          <div className="esr-filters" role="group" aria-label="按类别筛选（不是排序）">
            {categories.map((c) => (
              <button
                key={c}
                type="button"
                className={`esr-chip${catFilter === c ? ' is-on' : ''}`}
                aria-pressed={catFilter === c}
                onClick={() => setCatFilter(c)}
              >
                {c === 'ALL' ? '全部类别' : c}
              </button>
            ))}
          </div>
          <ul className="esr-list">
            {restShown.map((e) => <EntryCard key={e.id} e={e} today={today} />)}
          </ul>
          {restShown.length === 0 && (
            <p className="esr-empty">该类别下暂无线索。</p>
          )}
        </>
      )}

      <p className="esr-foot-note">
        ★ 本视图的窗口<strong>不代表</strong>该题材会上涨；「窗口内」只是**时间事实**，
        <strong>不提升</strong>研究成熟度。所有条目当前均为<strong>外部参考</strong>。
      </p>
    </section>
  );
}
