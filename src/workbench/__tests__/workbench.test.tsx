/**
 * 研究工作台（v0.74）回归 —— 只测本轮真正引入的四类不变量，不扩建测试体系。
 *
 *  A. **口径切换**：有效性 = 研究增量；行情超额只作附注；默认页面无优先级排序。
 *  B. **内部排序隔离**：评分/概率字段只在评估视图出现，索引产物与默认渲染里都没有。
 *  C. **T 时刻冻结**：正文与事后核对物理分离，事后核对不改正文。
 *  D. **可核性**：索引 counts / URL 策略 / 评估 priority=Wilson 下界。
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { Workbench } from '../Workbench';
import { EvalView } from '../EvalView';
import {
  exportBundle, freezeRecord, loadEvals, loadRecords, nextRecordId,
  saveEval, saveRecord, searchItems,
} from '../records';
import indexRaw from '@current/workbench_index_v0_1.json';
import evalRaw from '@current/workbench_eval_basis_v0_1.json';
import frontierRaw from '@current/frontier_board_v0_1.json';
import calendarRaw from '@current/event_calendar_v0_1.json';
import type { EvalDoc, IndexDoc } from '../types';
import type { FrontierDoc, EventCalendar } from '../FrontierView';

const doc = indexRaw as unknown as IndexDoc;
const evalDoc = evalRaw as unknown as EvalDoc;
const frontier = frontierRaw as unknown as FrontierDoc;
const calendar = calendarRaw as unknown as EventCalendar;

beforeEach(() => {
  const mem = new Map<string, string>();
  (globalThis as unknown as { localStorage: Storage }).localStorage = {
    getItem: (k: string) => mem.get(k) ?? null,
    setItem: (k: string, v: string) => { mem.set(k, v); },
    removeItem: (k: string) => { mem.delete(k); },
    clear: () => mem.clear(),
    key: () => null,
    length: 0,
  } as Storage;
});

describe('A · 口径切换与默认页面隔离', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★ 默认页面写明「有效性 = 研究增量」，并声明行情超额只是附注', () => {
    expect(html).toContain('有效性 = 研究增量');
    expect(html).toContain('行情附注');
    expect(html).toContain('不参与验收');
  });

  it('★★ v0.77：默认页按 G1→G4 研究浏览顺序，但仍不含任何启发式内部打分', () => {
    // 排序分两种：产物已有的分组顺序可以上默认页；Wilson 打分只在评估视图。
    for (const banned of ['data-eval-row', 'INTERNAL_EVAL_ONLY', 'priority_score',
      'wilson_low', 'data-eval-view', 'calibrated']) {
      expect(html, `默认页面不得出现 ${banned}`).not.toContain(banned);
    }
    expect(html).toContain('G1→G4 研究浏览顺序');
    expect(html).toContain('无分数、不是收益排序');
    expect(html).toContain('值得关注');
    expect(html).toContain('不是买卖点');
  });

  it('★ 评估视图是主动入口，默认不渲染评估表格', () => {
    expect(html).toContain('data-open-eval="1"');
    expect(html).not.toContain('<table class="wb-table">');
  });

  it('★ 历史检索仍按日期倒序、空 query 不铺全量（数据不变量）', () => {
    expect(searchItems(doc.items, '')).toEqual([]);
    expect(html).toContain('data-open-history="1"');
    const dated = doc.items.map((x) => x.date).filter(Boolean) as string[];
    expect([...dated]).toEqual([...dated].sort().reverse());
    expect(doc.counts.total).toBe(doc.items.length);
  });
});

describe('B · 内部评估视图（唯一允许排序的地方）', () => {
  const html = renderToStaticMarkup(<EvalView doc={evalDoc} />);

  it('★ 表格与评分只在评估视图出现，且带完整边界声明', () => {
    expect(html).toContain('data-eval-view="1"');
    expect(html).toMatch(/data-eval-row="/);
    expect(html).toContain('INTERNAL_EVAL_ONLY');
    expect(html).toContain('不是未来概率');
    expect(html).toContain('不参与有效性验收');
    expect(html).toContain('Wilson 95% 区间下界');
  });

  it('★★ priority_score 恒等于 Wilson 下界，且每行都标未校准/非概率', () => {
    expect(evalDoc.rows.length).toBeGreaterThan(0);
    for (const r of evalDoc.rows) {
      expect(r.priority_score).toBe(r.wilson_low);
      expect(r.usage).toBe('INTERNAL_EVAL_ONLY');
      expect(r.calibrated).toBe(false);
      expect(r.is_probability).toBe(false);
    }
  });

  it('★ 索引产物零评分字段（构建器 --check 也守这条）', () => {
    const blob = JSON.stringify(doc);
    for (const banned of ['priority_score', 'wilson_low', 'hit_rate', 'calibrated']) {
      expect(blob).not.toContain(banned);
    }
  });
});

describe('C · T 时刻冻结与事后核对分离', () => {
  const now = new Date('2026-11-04T21:00:00+08:00');

  it('★ 3 字段正文不含 posthoc，自动字段可核', () => {
    const r = freezeRecord({
      question: '冬季流感的历史对应是否值得继续查？',
      verdict_at_T: '此前没想到 2018 年同期对照，准备核对原始公告',
      type: 'LEAD', cluster_id: 'FLU-2026-WINTER', item_ref: 'X',
    }, doc, now, []);
    expect(r.record_id).toBe('RU-20261104-01');
    expect(r.data_as_of).toBe(doc.as_of);
    expect(r.artifact_ref).toContain('workbench_index_v0_1@');
    expect(Object.keys(r)).not.toContain('posthoc_check');
    expect(Object.keys(r)).not.toContain('posthoc');
  });

  it('★ 同一天序号递增，只增不改', () => {
    const first = freezeRecord({ question: 'q1', verdict_at_T: 'v1', type: 'LEAD', cluster_id: '' }, doc, now, []);
    const rows = saveRecord(first);
    expect(nextRecordId(rows, now)).toBe('RU-20261104-02');
    const second = freezeRecord({ question: 'q2', verdict_at_T: 'v2', type: 'NO_LEAD', cluster_id: '' }, doc, now, rows);
    const all = saveRecord(second);
    expect(all).toHaveLength(2);
    expect(all[0].verdict_at_T).toBe('v1');
  });

  it('★★ 事后核对独立存储，写它不会改动正文', () => {
    const r = freezeRecord({ question: 'q', verdict_at_T: 'v', type: 'LEAD', cluster_id: 'C1' }, doc, now, []);
    saveRecord(r);
    const before = JSON.stringify(loadRecords());
    saveEval({ record_id: r.record_id, checked_at: now.toISOString(),
      is_new_correspondence: 'YES', note: '查到 2018 年原始公告，机制不同' });
    expect(JSON.stringify(loadRecords())).toBe(before);
    expect(loadEvals()).toHaveLength(1);
  });

  it('★ 导出把 records 与 evals 分成两个独立数组', () => {
    const r = freezeRecord({ question: 'q', verdict_at_T: 'v', type: 'LEAD', cluster_id: '' }, doc, now, []);
    saveRecord(r);
    saveEval({ record_id: r.record_id, checked_at: now.toISOString(),
      is_new_correspondence: 'NO', note: '本来就知道' });
    const bundle = JSON.parse(exportBundle());
    expect(bundle.protocol).toBe('REAL_USE_LITE_v0_1');
    expect(Array.isArray(bundle.records)).toBe(true);
    expect(Array.isArray(bundle.evals)).toBe(true);
    expect(bundle.records[0].record_id).toBe(bundle.evals[0].record_id);
  });
});

describe('D · 检索与可核性', () => {
  it('★ 多词 AND、大小写不敏感', () => {
    const hits = searchItems(doc.items, '风电');
    expect(hits.length).toBeGreaterThan(0);
    expect(hits.every((x) => x.title || x.why)).toBe(true);
    expect(searchItems(doc.items, '风电 光伏').length).toBeLessThanOrEqual(hits.length);
    expect(searchItems(doc.items, 'ZZZ_不存在的词_ZZZ')).toEqual([]);
  });

  it('★ 索引里每条都有可核来源说明；外部 URL 必须是 http(s)', () => {
    expect(doc.counts.with_external_url).toBeGreaterThan(0);
    for (const it of doc.items) {
      expect(it.why.length).toBeGreaterThan(0);
      expect(it.uncertainty_reason.length).toBeGreaterThan(0);
      expect(['LOW', 'MEDIUM', 'HIGH']).toContain(it.uncertainty);
      if (it.url) expect(it.url).toMatch(/^https?:\/\//);
    }
  });

  it('★ 三类来源都进入索引，且无编造 URL', () => {
    for (const k of ['HISTORICAL_OBJECT', 'POLICY_EVENT', 'THEME_MAP_EVENT']) {
      expect(doc.counts.by_kind[k]).toBeGreaterThan(0);
    }
    expect(doc.items.filter((x) => x.source.source_kind.startsWith('INTERNAL') && x.url).length).toBe(0);
  });
});

/** ★★ v0.77：默认主入口改成「前瞻排程」（push / 事前），不再是提问式检索。 */
describe('E · 前瞻排程（系统主动推出，双轨并列）', () => {
  const html = renderToStaticMarkup(<Workbench />);

  it('★★ 默认页是前瞻排程；历史检索 / 记录降级为二级入口', () => {
    expect(html).toContain('data-frontier-view="1"');
    expect(html).toContain('data-open-frontier="1"');
    expect(html).toContain('data-open-history="1"');
    // 提问框不应出现在默认首屏
    expect(html).not.toContain('data-search=""');
  });

  it('★★ 双轨各自 as_of 与更新节奏独立标注，不做因果拼接', () => {
    expect(html).toContain('统计轨 · 季度更新');
    expect(html).toContain('机制轨 · 每周更新');
    expect(html).toContain(frontier.tracks.statistical.as_of);
    expect(html).toContain(frontier.tracks.mechanism.as_of);
    expect(html).toContain('不做因果拼接');
    expect(frontier.tracks.statistical.cadence).toBe('QUARTERLY');
    expect(frontier.tracks.mechanism.cadence).toBe('WEEKLY');
  });

  it('★★ 默认按 G1→G4 研究浏览顺序，且每条带关注标签与双轨理由', () => {
    const groups = [...html.matchAll(/data-group="(G\d)"/g)].map((m) => m[1]);
    expect(groups.length).toBeGreaterThan(0);
    const rank: Record<string, number> = { G1: 1, G2: 2, G3: 3, G4: 4 };
    expect(groups).toEqual([...groups].sort((a, b) => rank[a] - rank[b]));
    expect(html).toContain('data-reason="STATISTICAL"');
    expect(html).toContain('data-reason="MECHANISM"');
    expect(html).toContain('值得关注');
    expect(html).toContain('可斟酌的决策点');
    expect(html).toMatch(/data-record-from="/);
  });

  it('★★ 机制轨作为独立信息流，不给统计卡硬贴理由', () => {
    expect(html).toContain(`data-mechanism-feed="${frontier.mechanism_feed.length}"`);
    // 关键词同时筛选机制轨（否则政策事件里独有的词查不到）
    expect(html).toContain(`data-mechanism-shown="${frontier.mechanism_feed.length}"`);
    expect(html).toContain('上方关键词同时筛选这里');
    expect(frontier.counts.with_mechanism_link).toBeLessThan(frontier.items.length / 10);
    expect(html).toContain('本期机制轨');
    expect(html).toContain('无可核关联');
    for (const e of frontier.mechanism_feed) {
      expect(e.url).toMatch(/^https?:\/\//);
      expect(e.fact_vs_assumption).toBe('FACT_PUBLISHED_DOCUMENT');
    }
  });

  it('★★ 机制理由只在精确序列匹配时出现，URL 可核', () => {
    const linked = frontier.items.filter((x) => x.mechanism_reason);
    expect(linked.length).toBe(frontier.counts.with_mechanism_link);
    for (const x of linked) {
      expect(x.mechanism_reason!.relation).toBe('EXACT_SERIES_MATCH');
      expect(x.mechanism_reason!.url).toMatch(/^https?:\/\//);
    }
  });

  it('★★ 生肖试点：谐音层标 UNVERIFIED、不进统计；PIT 名称缺口如实披露', () => {
    expect(html).toContain('data-calendar-hypothesis="ZODIAC_NAME"');
    expect(html).toContain('data-layer="HOMOPHONE"');
    expect(html).toContain('data-layer-status="UNVERIFIED_ASSUMPTION"');
    expect(html).toContain('九阳股份');
    expect(html).toContain('不进统计、不参与排序、不构成篮子');
    expect(html).toContain('data-gap="PIT_NAME_SNAPSHOT_MISSING"');
    expect(html).toContain('行为假说，不是题材');
    for (const l of calendar.hypotheses[0].mapping_layers) {
      if (l.layer !== 'LITERAL') expect(l.status).toBe('UNVERIFIED_ASSUMPTION');
    }
  });

  it('★★ 日历只含可核事实；产物与默认页均无内部评分字段', () => {
    expect(html).toContain(`data-calendar-entries="${calendar.entries.length}"`);
    for (const e of calendar.entries) expect(e.fact_vs_assumption.length).toBeGreaterThan(0);
    const blob = JSON.stringify(frontier);
    for (const banned of ['priority_score', 'wilson_low', 'INTERNAL_EVAL_ONLY']) {
      expect(blob).not.toContain(banned);
      expect(html).not.toContain(banned);
    }
  });

  it('★★ 措辞放宽但仍无买卖执行类用语', () => {
    for (const banned of ['买入', '卖出', '目标价', '仓位', '胜率', '推荐买入']) {
      expect(html, `不应出现「${banned}」`).not.toContain(banned);
    }
    expect(html).toContain('具体的买卖决策由你自行做出');
    expect(html).toContain('不是买卖点');
  });
});
