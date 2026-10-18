/**
 * ★★ v0.21：历史事件 × **冻结 SA** 的精确交叉引用 —— 真实数据核对。
 *
 * ★ 数量全部由真实文件（`research/current/market_snapshots/snapshots/MS-2026-10-13-01.json`
 *   + `research/current/*_historical_events_*.json`）计算得出，**不预填预期数字**。
 */
import { describe, it, expect } from 'vitest';

import {
  emptySaCrossReference,
  loadSaCrossReference,
  saReferenceFor,
  summarizeSaCrossReference,
  SA_NOT_FOUND_LABEL,
} from '../saCrossReference';
import { eventMapByTheme } from '../../timeline/historicalEventMaps';

const THEMES = ['FLU', 'POWER_SUMMER', 'MEDIA', 'ROBOTICS', 'AUTO_INTELLIGENCE', 'SEMICONDUCTOR_AI'];

function eventCount(): number {
  return THEMES.reduce((n, t) => n + eventMapByTheme(t)!.doc.events.length, 0);
}

describe('A. ★★ 冻结 SA 交叉引用索引（真实 CANONICAL 快照）', () => {
  it('★★ 载入唯一 CANONICAL 快照 MS-2026-10-13-01（89 历史对象 × 6 当前对象 = 534）', async () => {
    const idx = await loadSaCrossReference();
    expect(idx.loaded, idx.loadError ?? '').toBe(true);
    expect(idx.snapshotId).toBe('MS-2026-10-13-01');
    expect(idx.snapshotStatus).toBe('CANONICAL');
    expect(idx.byHistoricalObject.size).toBe(89);
    expect(summarizeSaCrossReference(idx).rows).toBe(534);
  });

  it('★★ 事件侧精确核对：有对象引用 18 · 命中 18 · 未命中 0 · 匹配记录 108 条', async () => {
    const idx = await loadSaCrossReference();
    let withRef = 0;
    let found = 0;
    let notFound = 0;
    let rows = 0;
    const byStatus: Record<string, number> = {};

    for (const t of THEMES) {
      for (const e of eventMapByTheme(t)!.doc.events) {
        const cf = e.campaign_facts;
        const oid = cf ? (cf.object_id ?? cf.campaign_id) : undefined;
        if (!oid) continue;
        withRef += 1;
        const r = saReferenceFor(idx, oid);
        if (!r.matched) { notFound += 1; continue; }
        found += 1;
        rows += r.rows.length;
        for (const x of r.rows) byStatus[x.structuralStatus] = (byStatus[x.structuralStatus] ?? 0) + 1;
      }
    }

    expect(withRef).toBe(18);
    expect(found).toBe(18);
    expect(notFound).toBe(0);
    expect(rows).toBe(108);
    // ★ 匹配后按**已有** `structural_status` 汇总（原样，不重算）
    expect(byStatus).toEqual({
      STRUCTURAL_SUPPORTED: 4,
      STRUCTURAL_PARTIAL: 9,
      NO_VALID_CORRESPONDENCE: 56,
      INSUFFICIENT_EVIDENCE: 36,
      THEME_ONLY: 3,
    });
  });

  it('★ 事件总数 26 —— 其中 8 个**未记录对象**（对象级交叉引用不适用）', () => {
    let withoutRef = 0;
    for (const t of THEMES) {
      for (const e of eventMapByTheme(t)!.doc.events) {
        const cf = e.campaign_facts;
        if (!cf || !(cf.object_id ?? cf.campaign_id)) withoutRef += 1;
      }
    }
    expect(eventCount()).toBe(26);
    expect(withoutRef).toBe(8);
    expect(18 + withoutRef).toBe(eventCount());
  });
});

describe('B. ★ 对象类型 / 旧字段兼容 / 未匹配（只做精确 ID）', () => {
  it('★★ Research Candidate 按 `historical_research_candidate_id` 命中（RC-2024-SEMI-FUND3）', async () => {
    const idx = await loadSaCrossReference();
    const r = saReferenceFor(idx, 'RC-2024-SEMI-FUND3');
    expect(r.matched).toBe(true);
    expect(r.rows.length).toBe(6);                       // 6 个当前对象各一条
    expect(r.rows.every((x) => x.currentObjectId.startsWith('CC-'))).toBe(true);
    // 序号/名称齐全
    expect(r.rows[0].currentObjectName.length).toBeGreaterThan(0);
    expect(r.rows[0].statusLabel.length).toBeGreaterThan(0);
  });

  it('★ 旧字段兼容：`POWER-2023-SUMMER` 只带 `campaign_id` 仍命中 Campaign 对象', async () => {
    const idx = await loadSaCrossReference();
    const e = eventMapByTheme('POWER_SUMMER')!.doc.events
      .find((x) => x.event_id === 'POWER-2023-SUMMER')!;
    // 前置：该事件确实**没有** `object_id`，只有旧字段
    expect(e.campaign_facts?.object_id ?? null).toBeNull();
    expect(e.campaign_facts?.campaign_id).toBe('C-2023-POWEROP-THERMAL');
    const r = saReferenceFor(idx, e.campaign_facts!.campaign_id!);
    expect(r.matched).toBe(true);
    expect(r.rows.length).toBe(6);
  });

  it('★★ 未匹配：不存在的对象 id → matched=false，展示「未找到」文案（≠ 已否决）', async () => {
    const idx = await loadSaCrossReference();
    const r = saReferenceFor(idx, 'NOT-A-REAL-OBJECT');
    expect(r.matched).toBe(false);
    expect(r.rows).toEqual([]);
    expect(SA_NOT_FOUND_LABEL).toContain('未找到');
    expect(SA_NOT_FOUND_LABEL).toContain('SA');
  });

  it('★ 无对象 id / 空索引：matched=false；且 `loaded=false` **不等于**「未找到」', async () => {
    const idx = await loadSaCrossReference();
    expect(saReferenceFor(idx, null).matched).toBe(false);
    expect(saReferenceFor(idx, undefined).matched).toBe(false);

    const empty = emptySaCrossReference('测试：无 CANONICAL');
    expect(empty.loaded).toBe(false);
    expect(empty.byHistoricalObject.size).toBe(0);
    expect(saReferenceFor(empty, 'C-2023-POWEROP-THERMAL').matched).toBe(false);
  });

  it('★ 快照里的 structural_status 原样透传（不新增、不推断状态）', async () => {
    const idx = await loadSaCrossReference();
    const allowed = new Set([
      'STRUCTURAL_SUPPORTED', 'STRUCTURAL_PARTIAL', 'NO_VALID_CORRESPONDENCE',
      'INSUFFICIENT_EVIDENCE', 'THEME_ONLY',
    ]);
    for (const arr of idx.byHistoricalObject.values()) {
      for (const r of arr) expect(allowed.has(r.structuralStatus), r.structuralStatus).toBe(true);
    }
  });
});
