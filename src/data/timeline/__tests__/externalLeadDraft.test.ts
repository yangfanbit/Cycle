/**
 * ★★ 外部线索 → 研究请求草稿种子（v0.13）—— 内容与红线。
 */
import { describe, it, expect } from 'vitest';

import { externalCalendarDoc, externalCalendarEntries } from '../externalSeasonalCalendar';
import {
  EXTERNAL_LEAD_DRAFT_NOTE,
  draftFromExternalLead,
  draftReplaceConfirmText,
  makeDraftSeed,
} from '../externalLeadDraft';
import { isDraftBlank } from '../researchRequestDraft';

const doc = externalCalendarDoc();
const all = externalCalendarEntries();
const entryOf = (id: string) => all.find((e) => e.id === id)!;

describe('外部线索草稿种子 · 内容', () => {
  it('★★ 场景 3（EXT-17 未映射）：方向、窗口月份、类别、来源全部带入', () => {
    const seed = draftFromExternalLead(entryOf('EXT-17'), doc.source_reports);
    expect(seed.entryId).toBe('EXT-17');
    expect(seed.entryName).toBe('防汛 / 水利');
    expect(seed.draft.direction).toBe('防汛 / 水利');

    const known = seed.draft.knownLeads;
    expect(known).toContain('EXT-17');
    expect(known).toContain('6–7 月');                    // 原始窗口文本（月份精度）
    expect(known).toContain('行业季节性');                 // 类别
    expect(known).toContain('A股季节性题材日历（2026版）'); // 来源名
    expect(known).toContain('外部参考');
    expect(known).toContain('未经 ThreeC 验证');

    // 研究问题建议：可核实、可编辑
    expect(seed.draft.researchQuestions).toContain('核查');
    expect(seed.draft.researchQuestions).toContain('机制与时间证据');
  });

  it('★★ 月份保持原始精度：**不补日级日期**，无窗口线索不补月份', () => {
    const withWindow = draftFromExternalLead(entryOf('EXT-17'), doc.source_reports);
    expect(withWindow.draft.knownLeads).not.toMatch(/\d{4}-\d{2}-\d{2}/);
    expect(withWindow.draft.timeRange).toBe('');          // 不猜时间范围

    const noWindow = draftFromExternalLead(entryOf('EXT-24'), doc.source_reports);
    expect(noWindow.draft.knownLeads).toContain('无固定月份窗口');
    expect(noWindow.draft.knownLeads).not.toMatch(/\d{4}-\d{2}-\d{2}/);
    // 研究问题也不得出现虚构月份
    expect(noWindow.draft.researchQuestions).toContain('无固定月份窗口');
  });

  it('★★ 不伪造覆盖查询关联（种子不是一次查询）', () => {
    const seed = draftFromExternalLead(entryOf('EXT-17'), doc.source_reports);
    expect(seed.draft.linkedQuery).toBe('');
    expect(seed.draft.linkedAt).toBe('');
    expect(seed.draft.linkedCoverage).toBeNull();
    // 但草稿**不是空白**（有方向与已知线索 → 会触发「替换确认」判定）
    expect(isDraftBlank(seed.draft)).toBe(false);
  });

  it('★ 不编造「为什么关注」（用户自己填）', () => {
    const seed = draftFromExternalLead(entryOf('EXT-17'), doc.source_reports);
    expect(seed.draft.whyCare).toBe('');
  });

  it('★ 确认文案点名线索，且说明原草稿会被覆盖', () => {
    const t = draftReplaceConfirmText('防汛 / 水利');
    expect(t).toContain('防汛 / 水利');
    expect(t).toContain('非空草稿');
    expect(t).toContain('覆盖');
    expect(t).toContain('保留现有草稿');
    expect(EXTERNAL_LEAD_DRAFT_NOTE).toContain('可');
    expect(EXTERNAL_LEAD_DRAFT_NOTE).toContain('编辑');
    expect(EXTERNAL_LEAD_DRAFT_NOTE).toContain('不会');
  });
});

describe('外部线索草稿种子 · token', () => {
  it('★ makeDraftSeed 透传 token（同一线索再次点击可重新触发）', () => {
    const a = makeDraftSeed(entryOf('EXT-17'), doc.source_reports, 1);
    const b = makeDraftSeed(entryOf('EXT-17'), doc.source_reports, 2);
    expect(a.token).toBe(1);
    expect(b.token).toBe(2);
    expect(a.draft).toEqual(b.draft);
  });
});
