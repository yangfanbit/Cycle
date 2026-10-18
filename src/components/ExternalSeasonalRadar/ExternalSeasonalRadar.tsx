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
import { eventMapByExternalId } from '../../data/timeline/historicalEventMaps';
import type { ThemeAnnualRow } from '../../data/timeline/themeAnnualWindow';
import { ExternalSeasonTimeline } from './ExternalSeasonTimeline';
import { RichText } from '../RichText';
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
 * ★★ 事件地图入口改为**数据驱动**（2026-10-14 通用化）：
 *   由 `research/current/historical_event_maps_index.json` 的 `external_entry_ids` 决定
 *   哪个外部线索显示事件地图 —— **不再硬编码题材 ID**。
 *   ★ 无数据文件的题材**不显示空壳**（避免暗示「已研究过」）。
 */

const RELATION_CLASS: Record<WindowRelation, string> = {
  IN_WINDOW: 'esr-rel-in',
  UPCOMING: 'esr-rel-soon',
  PASSED: 'esr-rel-past',
  NO_FIXED_WINDOW: 'esr-rel-none',
  INSUFFICIENT_DATE: 'esr-rel-none',
};

function EntryCard({ e, today, onOpenMap }: {
  e: ExternalCalendarEntry; today: string; onOpenMap?: (themeId: string) => void;
}) {
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

      {/* ★ v0.10：**不再内嵌**完整历史地图 —— 雷达的职责是「外部线索」。
          已有地图的线索给出跳转指针（地图本身在首页「历史题材地图」区，可切换题材）。
          这样同一批 13 个事件不会在页面上渲染两遍。 */}
      {(() => {
        const map = eventMapByExternalId(e.id);
        if (!map) return null;
        return (
          <p className="esr-map-link">
            ★ 该线索已有<strong>历史事件地图</strong>（{map.doc.events.length} 个事件，事后重建）
            {onOpenMap && (
              <button type="button" className="esr-map-open"
                      onClick={() => onOpenMap(map.theme_id)}>
                在「历史题材地图」中查看 →
              </button>
            )}
          </p>
        );
      })()}

      <div className="esr-foot">
        <span className="esr-id">{e.id}</span>
        <span className="esr-rev">
          更新 {e.revision[e.revision.length - 1].date}
        </span>
      </div>
    </li>
  );
}

export function ExternalSeasonalRadar({ today, onOpenMap, onRequestDraft, macroRows }: {
  today: string;
  /** ★ v0.10：跳转到首页「历史题材地图」并选中该题材（由 App 注入） */
  onOpenMap?: (themeId: string) => void;
  /** ★ v0.13：未映射线索 → 带入现有研究请求草稿 */
  onRequestDraft?: (entry: ExternalCalendarEntry) => void;
  /** ★ v0.13：**宏观粒度**主题行（历史窗口对照；与首页当前粒度无关） */
  macroRows?: readonly ThemeAnnualRow[];
}) {
  // ★ v0.13：时间轴已默认展示全部 25 条 → 详细卡片改回**按需展开**
  //   （减少与时间轴重复铺开；来源 / 线索正文 / 交互全部保留）
  const [showAll, setShowAll] = useState(false);
  const [catFilter, setCatFilter] = useState<string>('ALL');

  const doc = externalCalendarDoc();
  const all = externalCalendarEntries();

  const categories = useMemo(
    () => ['ALL', ...Array.from(new Set(all.map((e) => e.category)))],
    [all],
  );

  // ★ 一个筛选器同时作用于「时间轴」与「详细卡片」，避免两处口径不一致
  const filtered = catFilter === 'ALL' ? all : all.filter((e) => e.category === catFilter);
  const priority = filtered.filter((e) => PRIORITY_IDS.includes(e.id));
  const rest = filtered.filter((e) => !PRIORITY_IDS.includes(e.id));

  return (
    <section className="esr" aria-label="外部季节性观察雷达">
      <div className="esr-head">
        <h2 className="esr-title">外部季节性观察雷达</h2>
        <span className="esr-source-badge">{EXTERNAL_SOURCE_LABEL}</span>
      </div>

      <p className="esr-note"><RichText text={EXTERNAL_CALENDAR_NOTE} /></p>
      <p className="esr-count">
        共 <strong>{all.length}</strong> 项外部线索 · 版本 <code>{doc.artifact_version}</code> ·
        生成 {doc.generated_at}
        <span className="esr-vs">
          （上方地图是 ThreeC <strong>从历史数据得到</strong>的窗口；本视图是
          <strong>外部资料声称</strong>的窗口，两者来源不同）
        </span>
      </p>

      {/* ★★ v0.12 主交付：外部季节性**参考时间轴**（全部 25 条按 1–12 月铺开）
          ★ 与上方「历史季节性机会地图」来源不同、配色不同：本区一律「外部参考」。 */}
      <ExternalSeasonTimeline
        entries={filtered}
        allEntries={all}
        categories={categories}
        category={catFilter}
        onCategory={setCatFilter}
        onOpenMap={onOpenMap}
        onRequestDraft={onRequestDraft}
        macroRows={macroRows ?? []}
        today={today}
      />

      <h3 className="esr-sub">当前优先观察（{priority.length} 项）</h3>
      <ul className="esr-list">
        {priority.map((e) => <EntryCard key={e.id} e={e} today={today} onOpenMap={onOpenMap} />)}
      </ul>

      <div className="esr-rest-head">
        <h3 className="esr-sub">全部线索（{all.length} 项）</h3>
        <button
          type="button"
          className="esr-toggle"
          aria-expanded={showAll}
          onClick={() => setShowAll((v) => !v)}
        >
          {showAll ? `收起 ${rest.length} 项的详细卡片` : `展开其余 ${rest.length} 项的详细卡片`}
        </button>
      </div>

      {showAll && (
        <>
          <ul className="esr-list">
            {rest.map((e) => <EntryCard key={e.id} e={e} today={today} onOpenMap={onOpenMap} />)}
          </ul>
          {rest.length === 0 && (
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
