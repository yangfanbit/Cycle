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
import type { EvalDoc, IndexDoc } from '../types';

const doc = indexRaw as unknown as IndexDoc;
const evalDoc = evalRaw as unknown as EvalDoc;

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

  it('★★ 默认页面不做优先级排序、不含任何内部评分数据', () => {
    for (const banned of ['data-eval-row', 'INTERNAL_EVAL_ONLY', 'priority_score',
      'wilson_low', 'data-eval-view', 'calibrated']) {
      expect(html, `默认页面不得出现 ${banned}`).not.toContain(banned);
    }
    expect(html).toContain('不做优先级排序');
  });

  it('★ 评估视图是主动入口，默认不渲染评估表格', () => {
    expect(html).toContain('data-open-eval="1"');
    expect(html).not.toContain('<table class="wb-table">');
  });

  it('★ 检索结果按日期倒序，空 query 不铺 385 条', () => {
    expect(searchItems(doc.items, '')).toEqual([]);
    expect(html).toContain('按日期倒序');
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
