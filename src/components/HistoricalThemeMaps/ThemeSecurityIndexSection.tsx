/**
 * ★★ 历史参与标的索引（ThreeC 1.3 · v0.11）。
 *
 * 位置：`HistoricalThemeMaps` 的当前题材面板内、**逐事件列表之前**。
 * 数据：完全由当前题材的 `doc.events[].participants` 汇总（`themeSecurityIndexOf`），
 * **不复制**研究数据、不建第二套地图。
 *
 * ## 交互
 *
 * - 按公司名称 / 代码 / 别名搜索（纯前端，无网络）；
 * - 点「展开」看该标的**逐次**的历史事件记录：纳入理由 / 证据等级 / 同期报道涨幅 /
 *   该事件已有的实测行情（按各事件原口径，**不跨事件合并**）。
 *
 * ## 语义红线（UI 常驻）
 *
 * 历史参与 ≠ 业务相关 ≠ 行情上涨；`REPORT_NAMED` 与 `BUSINESS_VERIFIED` 逐次呈现；
 * 不给相关度打分、不按涨幅或出现次数排序、不跨事件汇总收益。
 */
import { Fragment, useMemo, useState } from 'react';

import {
  EVIDENCE_LEVEL_LABEL,
  PARTICIPANT_CATEGORY_LABEL,
  type HistoricalEventsDoc,
} from '../../data/timeline/historicalEventMaps';
import {
  SECURITY_INDEX_DISCLAIMER,
  evidenceSummaryOf,
  filterSecurityIndex,
  themeSecurityIndexOf,
  type SecurityOccurrence,
  type ThemeSecurityEntry,
} from '../../data/timeline/themeSecurityIndex';
import { RichText } from '../RichText';

function pct(v?: number | null): string {
  if (v == null || !Number.isFinite(v)) return '—';
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`;
}

function pp(v?: number | null): string {
  if (v == null || !Number.isFinite(v)) return '—';
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}pp`;
}

/** 一次出现的明细（逐事件原口径，不与其他事件合并） */
function OccurrenceRow({ o }: { o: SecurityOccurrence }) {
  return (
    <li className="tsi-occ" data-occ-event={o.eventId}>
      <div className="tsi-occ-head">
        <strong>{o.year} · {o.eventLabel}</strong>
        <span className="tsi-cat">{PARTICIPANT_CATEGORY_LABEL[o.category] ?? o.category}</span>
        <span className={`tsi-ev ev-${(o.evidenceLevel ?? 'unrecorded').toLowerCase()}`}>
          {o.evidenceLevel ? EVIDENCE_LEVEL_LABEL[o.evidenceLevel] : '（未标注证据等级）'}
        </span>
      </div>

      <p className="tsi-line"><strong>纳入理由</strong>：<RichText text={o.rationale} /></p>
      <p className="tsi-line tsi-src"><strong>来源</strong>：<RichText text={o.source} /></p>

      {(o.reportedMove || o.eventReportedMove) && (
        <p className="tsi-line">
          <strong>同期报道当日涨幅</strong>：
          {o.eventReportedMove ?? o.reportedMove}
          <span className="tsi-hint">（报道口径，非区间收益）</span>
        </p>
      )}

      {o.hasMarketPerformance ? (
        <p className="tsi-line">
          <strong>该事件实测行情</strong>
          {o.marketWindow ? `（窗口 ${o.marketWindow[0]} ~ ${o.marketWindow[1]}）` : ''}：
          区间 {pct(o.periodReturnPct)} · 至高点 {pct(o.toHighPct)}
          {o.highDate ? `（${o.highDate}）` : ''} · 区间超额 {pp(o.excessPeriodPp)}
          · 至高点超额 {pp(o.excessToHighPp)}
          <span className="tsi-hint">（该事件口径，未与其他事件合并）</span>
        </p>
      ) : (
        <p className="tsi-line tsi-missing">
          该事件未提供该标的的实测行情 —— <strong>原样保留缺失</strong>，不以 0 代替
          {o.marketData ? `（参与者条目仅记「${o.marketData}」）` : ''}。
        </p>
      )}

      {o.businessMechanism && (
        <p className="tsi-line">
          <strong>业务机制</strong>：<RichText text={o.businessMechanism} />
          {o.businessMechanismCaveat && (
            <span className="tsi-caveat"><RichText text={o.businessMechanismCaveat} /></span>
          )}
        </p>
      )}
      {o.note && <p className="tsi-line tsi-note"><RichText text={o.note} /></p>}
    </li>
  );
}

function SecurityRow({ x, open, onToggle }: {
  x: ThemeSecurityEntry; open: boolean; onToggle: () => void;
}) {
  return (
    <>
      <tr data-security-id={x.securityId} className={open ? 'is-open' : undefined}>
        <td>
          <strong>{x.name}</strong>
          <code className="tsi-ticker">{x.ticker}</code>
          {x.aliases.length > 0 && (
            <span className="tsi-alias">（历史别名：{x.aliases.join(' / ')}）</span>
          )}
        </td>
        <td className="tsi-num">{x.eventCount}</td>
        <td>{x.years.join(' · ')}</td>
        <td className="tsi-evsum">{evidenceSummaryOf(x)}</td>
        <td>
          <button type="button" className="tsi-toggle" aria-expanded={open}
                  onClick={onToggle}>
            {open ? '收起' : '展开'}该标的的事件记录
          </button>
        </td>
      </tr>
      {open && (
        <tr className="tsi-detail">
          <td colSpan={5}>
            <ol className="tsi-occs">
              {x.occurrences.map((o) => <OccurrenceRow key={`${o.eventId}-${o.category}`} o={o} />)}
            </ol>
          </td>
        </tr>
      )}
    </>
  );
}

export function ThemeSecurityIndexSection({ doc }: { doc: HistoricalEventsDoc }) {
  const index = useMemo(() => themeSecurityIndexOf(doc), [doc]);
  const [query, setQuery] = useState('');
  const [openId, setOpenId] = useState<string | null>(null);

  // ★ 无参与标的 → 不渲染空壳
  if (index.entries.length === 0) return null;

  const filtered = filterSecurityIndex(index, query);
  const searching = query.trim().length > 0;

  return (
    <section className="tsi" aria-label="历史参与标的索引">
      <div className="tsi-head">
        <h5 className="tsi-title">历史参与标的</h5>
        <span className="tsi-meta">
          <strong>{index.totals.securities}</strong> 只 · 跨 <strong>{index.totals.eventsWithParticipants}</strong> 个事件 ·
          共 <strong>{index.totals.occurrences}</strong> 次出现
        </span>
        <span className="tsi-sort">按公司名称排序（<strong>不是</strong>按涨幅或出现次数）</span>
      </div>

      <p className="tsi-disc"><RichText text={SECURITY_INDEX_DISCLAIMER} /></p>

      <div className="tsi-search">
        <input
          type="search"
          aria-label="按名称或代码搜索标的"
          placeholder="输入公司名称或代码（如 华兰生物 / 002007）"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {searching && (
          <button type="button" className="tsi-clear" onClick={() => setQuery('')}>清除</button>
        )}
        <span className="tsi-count" data-tsi-count={filtered.entries.length}>
          {filtered.entries.length} / {index.entries.length} 只
        </span>
      </div>

      {filtered.entries.length === 0 ? (
        <p className="tsi-empty">
          没有匹配「{query.trim()}」的标的 —— 本索引只含<strong>已记录</strong>的参与标的，
          <strong>未记录 ≠ 未参与</strong>。
        </p>
      ) : (
        <div className="fem-table-wrap">
          <table className="tsi-table">
            <thead>
              <tr>
                <th>公司 / 代码</th>
                <th title="该标的在本题材历史事件里出现的次数">涉及事件</th>
                <th>出现年份</th>
                <th title="逐次统计，不取最高级">证据类别（逐次）</th>
                <th><span className="tsi-sr">明细</span></th>
              </tr>
            </thead>
            <tbody>
              {filtered.entries.map((x) => (
                <Fragment key={x.securityId}>
                  <SecurityRow
                    x={x}
                    open={openId === x.securityId}
                    onToggle={() => setOpenId(openId === x.securityId ? null : x.securityId)}
                  />
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {index.unlinkedReports.length > 0 && (
        <div className="tsi-unlinked">
          <h6>同期报道点名、尚未关联标的记录（{index.unlinkedReports.length} 条）</h6>
          <p className="tsi-hint">
            ★ 这些代码在 <code>reported_same_day_moves</code> 里有涨幅记录，但该事件
            <strong>没有</strong>对应的参与者条目。代码未能与任何标的<strong>完全匹配</strong>
            → <strong>不猜测身份</strong>，原样保留为独立状态。
          </p>
          <ul>
            {index.unlinkedReports.map((r) => (
              <li key={`${r.eventId}-${r.code}`} data-unlinked-code={r.code}>
                <strong>{r.year} · {r.eventLabel}</strong> · <code>{r.code}</code> · {r.move}
                <span className="tsi-status">{r.statusLabel}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
