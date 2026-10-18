/**
 * ★★ 历史题材地图 —— **主入口**（ThreeC 1.3 · v0.10）。
 *
 * ## 为什么需要它
 *
 * v0.9 之前，5 个题材（索引驱动）的历史事件地图**只能**从「外部季节性观察雷达」的线索卡里间接进入：
 * 用户必须先展开「全部线索」、找到某条外部线索、再在卡内看到地图。
 * 但地图本身是**ThreeC 自己的历史事后重建**，与「外部资料声称的窗口」是两种东西 ——
 * 把它藏在外部线索里，等于让用户以为它也是外部参考。
 *
 * ## 本组件的职责（单一）
 *
 * 由 `historical_event_maps_index.json` 驱动，**列出全部已建地图的题材**，
 * 通过题材切换渲染**同一个** `HistoricalEventMap`（**不复制事件卡实现**）。
 *
 * ## 硬约束
 *
 * - **不硬编码题材**：题材清单、标签、显示配置全部来自索引（`allResolvedEventMaps()`）。
 *   索引新增题材后此处自动出现；未登记 doc 的题材**不显示空壳**。
 * - **不硬编码事件数**：计数由 `doc.events.length` 现算。
 * - **不新增数据管线**：跨年份比较与经验基准概率仍由 `HistoricalEventMap` 内部渲染。
 * - **不与外部雷达互相替代**：雷达只展示外部线索；本区只展示历史事后重建。
 */
import { useEffect, useMemo, useState } from 'react';

import {
  allResolvedEventMaps,
  eventMapsNotIncluded,
  type ResolvedEventMap,
} from '../../data/timeline/historicalEventMaps';
import {
  loadSaCrossReference,
  type SaCrossReferenceIndex,
} from '../../data/marketSnapshot/saCrossReference';
import { HistoricalEventMap } from '../ExternalSeasonalRadar/HistoricalEventMap';
import { ThemeSecurityIndexSection } from './ThemeSecurityIndexSection';

/** 组件 id（供外部雷达「查看地图」跳转定位） */
export const HISTORICAL_THEME_MAPS_ID = 'historical-theme-maps';

export interface ThemeMapSummary {
  themeId: string;
  label: string;
  eventCount: number;
  /** 该题材事件覆盖的年份（升序，去重）—— 只做事实陈列 */
  years: number[];
}

/**
 * ★ 题材摘要（**纯函数**，供 UI 与测试共用）。
 * 计数与年份全部从 doc 现算，**不读索引里的 `event_count`**（索引字段可能与 doc 漂移）。
 */
export function themeMapSummaries(maps: readonly ResolvedEventMap[]): ThemeMapSummary[] {
  return maps.map((m) => {
    const years = [...new Set(m.doc.events.map((e) => e.year))].sort((a, b) => a - b);
    return {
      themeId: m.theme_id,
      label: m.label,
      eventCount: m.doc.events.length,
      years,
    };
  });
}

export function HistoricalThemeMaps({
  activeThemeId,
  onSelectTheme,
  onOpenObject,
  canOpenObject,
}: {
  /** 受控的当前题材（由 App 持有，便于外部雷达跳转时联动） */
  activeThemeId?: string;
  onSelectTheme?: (themeId: string) => void;
  /** ★ v0.15：事件 → 历史对象详情（复用 App selection / CampaignDetail 流程） */
  onOpenObject?: (objectId: string) => void;
  /** ★ v0.15：对象能否通过现有详情流程解析（不可解析 → 不给按钮） */
  canOpenObject?: (objectId: string) => boolean;
}) {
  const maps = useMemo(() => allResolvedEventMaps(), []);
  const summaries = useMemo(() => themeMapSummaries(maps), [maps]);
  const [innerActive, setInnerActive] = useState<string>('');
  const [openNote, setOpenNote] = useState(false);
  /** ★★ v0.21：当前唯一 CANONICAL 快照的 SA 交叉引用（一次性载入；失败 → `loaded=false`，不崩） */
  const [saRef, setSaRef] = useState<SaCrossReferenceIndex | null>(null);
  useEffect(() => {
    let alive = true;
    loadSaCrossReference()
      .then((x) => { if (alive) setSaRef(x); })
      .catch(() => { /* 载入失败已在索引内标记，不额外抛错 */ });
    return () => { alive = false; };
  }, []);

  if (maps.length === 0) return null;          // ★ 无数据 → 不渲染空壳

  const active = activeThemeId || innerActive || maps[0].theme_id;
  const current = maps.find((m) => m.theme_id === active) ?? maps[0];
  const totalEvents = summaries.reduce((s, x) => s + x.eventCount, 0);
  const notIncluded = eventMapsNotIncluded();

  const select = (id: string) => {
    if (!activeThemeId) setInnerActive(id);
    onSelectTheme?.(id);
  };

  return (
    <section className="htm" id={HISTORICAL_THEME_MAPS_ID} aria-label="历史题材地图">
      <div className="htm-head">
        <h2 className="htm-title">历史题材地图</h2>
        <span className="htm-count">
          共 <strong>{maps.length}</strong> 个题材 · <strong>{totalEvents}</strong> 个历史事件
        </span>
      </div>

      <p className="htm-note">
        这里是 ThreeC 对<strong>历史题材</strong>的<strong>事后重建</strong>（来源：同期报道 + 库内 Campaign +
        实测行情），按题材切换查看。★ 与下方「外部季节性观察雷达」<strong>来源不同</strong>：
        本区是<strong>从历史数据得到</strong>的题材事件，雷达是<strong>外部资料声称</strong>的季节性窗口。
        事件可展开查看催化时间线 / 相关标的 / 纳入理由 / 业务机制证据 / 报道当日涨幅 / 区间行情 /
        相对基准表现 / 缺失事项；跨年份比较与该题材的经验基准概率也在其中。
      </p>

      {/* 题材切换：标签由索引驱动，计数由 doc 现算 */}
      <div className="htm-tabs" role="tablist" aria-label="按题材切换历史地图">
        {summaries.map((s) => (
          <button
            key={s.themeId}
            type="button"
            role="tab"
            id={`htm-tab-${s.themeId}`}
            aria-selected={s.themeId === current.theme_id}
            aria-controls={`htm-panel-${s.themeId}`}
            className={`htm-tab${s.themeId === current.theme_id ? ' is-on' : ''}`}
            data-theme-id={s.themeId}
            onClick={() => select(s.themeId)}
          >
            <span className="htm-tab-label">{s.label}</span>
            <span className="htm-tab-meta">
              {s.eventCount} 个事件
              {s.years.length > 0 ? ` · ${s.years[0]}–${s.years[s.years.length - 1]}` : ''}
            </span>
          </button>
        ))}
      </div>

      <div
        className="htm-panel"
        role="tabpanel"
        id={`htm-panel-${current.theme_id}`}
        aria-labelledby={`htm-tab-${current.theme_id}`}
      >
        {/* ★★ v0.11：先给「这个题材历史上有哪些标的」，再给逐事件列表。
            ★ 数据完全来自当前题材的 `doc.events[].participants`（`themeSecurityIndexOf`），
              不复制研究数据、不建第二套地图。
            ★ key 用 theme_id：切题材时搜索/展开态自然重置（不串题材）。 */}
        <ThemeSecurityIndexSection key={current.theme_id} doc={current.doc} />

        {/* ★ 复用既有地图组件：事件卡 / 跨年份比较 / 经验基准概率全部原样 */}
        <HistoricalEventMap
          doc={current.doc}
          display={current.display}
          onOpenObject={onOpenObject}
          canOpenObject={canOpenObject}
          saRef={saRef}
        />
      </div>

      {notIncluded.length > 0 && (
        <div className="htm-missing">
          <button type="button" className="htm-missing-toggle" aria-expanded={openNote}
                  onClick={() => setOpenNote((v) => !v)}>
            {openNote ? '收起' : '查看'}未建立地图的题材（{notIncluded.length} 个）
          </button>
          {openNote && (
            <ul className="htm-missing-list">
              {notIncluded.map((n) => (
                <li key={n.theme_id}>
                  <strong>{n.label}</strong>：{n.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
