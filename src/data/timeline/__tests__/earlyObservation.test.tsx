import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import {
  earlyObservationOf,
  currentMarketOf,
  EARLY_OBSERVATION_L3_NOTE,
} from '../earlyObservation';
import { CampaignDetail } from '../../../components/CampaignDetail/CampaignDetail';
import { CurrentMarketStrip } from '../../../components/CurrentMarket/CurrentMarketStrip';
import type { TimelineCampaign } from '../timelineTypes';

/**
 * 「启动前观察」的不变量测试（v0_2 · 分层版）。
 *
 * ★ 锁住设计 `docs/DESIGN_EARLY_OBSERVATION_v0_2.md` 的三条硬约束：
 *
 *   1. **不做「像不像」** —— 只有事实，无相似度 / 匹配 / 概率 / 评分 / 排序。
 *   2. **全部 ex-ante** —— 每个检查点只用它当日及之前的数据。
 *   3. ★★ **当前市场状态不与任何具体 campaign 并列** ——
 *      把「某段历史的启动前」与「现在」摆在同一张卡片，等于替使用者摆好「像不像」的题面。
 *      **本文件用断言把这一条钉死**（见 §CampaignDetail 最后两条）。
 */

const source = researchTimelineSource();

function campaignById(id: string): TimelineCampaign | null {
  for (const y of source.years()) {
    const c = source.yearData(y).campaigns.find((x) => x.campaign_id === id);
    if (c) return c;
  }
  return null;
}

describe('earlyObservation · L1 市场层（基准，无选择偏差）', () => {
  it('★ 给出启动前多检查点 T-60/40/20/10/5/1，且全部**早于启动日**', () => {
    const e = earlyObservationOf('C-2023-AD')!;
    const ml = e.marketLayer!;
    expect(ml).not.toBeNull();
    expect(ml.seriesId).toBe('SH000300');
    const ts = ml.checkpoints.map((c) => c.tMinus);
    expect(ts).toContain(60);
    expect(ts).toContain(20);
    expect(ts).toContain(1);
    const c = campaignById('C-2023-AD')!;
    for (const p of ml.checkpoints) expect(p.date < c.start).toBe(true);
    expect(ml.atLastDay!.date).toBe('2023-06-09');
  });

  it('★ L1 **不输出**相对强度（相对自身恒为 0，无意义）', () => {
    const ml = earlyObservationOf('C-2023-AD')!.marketLayer!;
    for (const p of ml.checkpoints) expect(p.relStrength20).toBeNull();
  });

  it('观测量无量纲：分位在 0–1、波动率比为正', () => {
    const ml = earlyObservationOf('C-2023-AD')!.marketLayer!;
    for (const p of ml.checkpoints) {
      if (p.volPct60 !== null) {
        expect(p.volPct60).toBeGreaterThanOrEqual(0);
        expect(p.volPct60).toBeLessThanOrEqual(1);
      }
      if (p.volRatio !== null) expect(p.volRatio).toBeGreaterThan(0);
    }
  });
});

describe('earlyObservation · L2 标的层（事后选定 → 必须带偏差警告）', () => {
  it('给出逐标的的启动前状态，且**带相对强度**', () => {
    const sl = earlyObservationOf('C-2023-AD')!.securityLayer!;
    expect(sl.securities.length).toBeGreaterThanOrEqual(3);
    const de = sl.securities.find((s) => s.securityId === 'DESAYSV')!;
    expect(de.atLastDay).not.toBeNull();
    expect(de.atLastDay!.relStrength20).not.toBeNull();
  });

  it('★★ 偏差警告必须存在，且写明「不得与当前并列」', () => {
    const sl = earlyObservationOf('C-2023-AD')!.securityLayer!;
    expect(sl.biasNote.length).toBeGreaterThan(10);
    expect(sl.biasNote).toContain('事后选定');
    expect(sl.biasNote).toContain('不得与当前并列');
  });
});

describe('earlyObservation · 当前市场状态（只供全局位置）', () => {
  it('★ 取最新可得交易日（asOf 随数据刷新，断言与产物交叉一致）', () => {
    // ★ v0.25：旧断言写死 `2026-09-30 / 4357.62 / -5.5` —— 那是**旧行为快照**，
    //   每补一次行情就得改测试。改为「与产物逐字一致」的交叉断言（唯一写死的数字是
    //   本轮实测值，作为**回归基线**，下次刷新时连同 docs 一起更新）。
    const m = currentMarketOf()!;
    expect(m.seriesId).toBe('SH000300');
    expect(m.asOf).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(m.asOf).toBe('2026-10-20');            // 本轮实测：最后交易日（v0.26 刷新）
    expect(m.observables!.close).toBe(4152.11);    // 产物 current_market 逐字一致
    expect(m.observables!.ret20Pct).toBeCloseTo(-7.3, 1);
  });

  it('artifact 中没有的对象 → null（**不造默认值**）', () => {
    expect(earlyObservationOf('C-NOT-EXIST')).toBeNull();
    expect(earlyObservationOf('')).toBeNull();
  });

  it('★ L3 未建的原因必须写明（含「个股清单」这一实质理由）', () => {
    expect(EARLY_OBSERVATION_L3_NOTE.length).toBeGreaterThan(20);
    expect(EARLY_OBSERVATION_L3_NOTE).toContain('个股清单');
  });

  it('★ 语义边界：视图模型**不含**任何 score / 评分 / 概率 / 排名字段', () => {
    const e = earlyObservationOf('C-2023-AD')!;
    for (const obj of [e, e.marketLayer, e.securityLayer]) {
      const keys = Object.keys(obj ?? {}).map((x) => x.toLowerCase());
      for (const banned of ['score', 'rating', 'rank', 'probability', 'prediction']) {
        expect(keys.some((x) => x.includes(banned))).toBe(false);
      }
    }
  });
});

describe('CampaignDetail · 启动前观察区块（真实数据）', () => {
  const noop = () => {};

  it('渲染 L1 / L2 两层与纪律声明，且不残留 Markdown 标记', () => {
    const c = campaignById('C-2023-AD')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('启动前观察');
    expect(html).toContain('L1 · 市场层');
    expect(html).toContain('L2 · 标的层');
    expect(html).toContain('T-60');
    expect(html).toContain('德赛西威');
    expect(html).toContain('事后选定');
    // 纪律声明必须在（措辞沿用全库既定白名单，避免触发评分词护栏）
    expect(html).toContain('非预测');
    expect(html).toContain('不评分、不排名');
    // JSX 文本里不得残留会字面显示的 Markdown 强调符
    expect(html).not.toContain('**');
  });

  it('★★★ 约束 3：campaign 详情**不得**出现当前市场状态（否则等于摆好「像不像」的题面）', () => {
    const c = campaignById('C-2023-AD')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).not.toContain('当前市场状态');
    // ★ v0.25：不写死具体日期 —— 用**当轮真实的 asOf** 做不变量：
    //   下次补行情后页面日期变了，这条断言依然成立（写死日期等于每次都要改测试）。
    const asOf = currentMarketOf()!.asOf;
    expect(asOf).toBeTruthy();
    expect(html, '当前市场状态泄漏进了 campaign 详情').not.toContain(asOf);
  });
});

describe('earlyObservation · L2 缺失必须带原因（v0.25 新增）', () => {
  const noop = () => {};

  it('★★ NO_DATA 行不过滤、且逐条带 reason / why', () => {
    // ★ 曾把非 OK 行**静默过滤**掉 —— 用户看不到「哪几只没数据、为什么」。
    const sl = earlyObservationOf('C-2016-CONS-BAIJIU-UPGRADE')!.securityLayer;
    // 该 campaign 三只标的均为 2015–2016 负价段 → 全部 NO_DATA（2016 事件无 L2 层）
    const layer = earlyObservationOf('C-2020-HIEQ-AUTOMATION')!.securityLayer!;
    const missing = layer.securities.filter((s) => s.status === 'NO_DATA');
    expect(missing.length, '步科 / 绿的谐波在 2020-04-01 前未上市 → 必须留在列表里').toBeGreaterThan(0);
    for (const s of missing) {
      expect(['listed_after_campaign_start', 'no_series', 'insufficient_pre_history',
              'no_observable_points'], s.securityId).toContain(s.reason);
      expect(s.why, s.securityId).toBeTruthy();
      expect(s.rowsBeforeStart, s.securityId).not.toBeNull();
    }
  });

  it('★★ CampaignDetail 渲染 NO_DATA 的原因文字（不显示成「无数据」就完事）', () => {
    const c = campaignById('C-2020-HIEQ-AUTOMATION')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('启动前数据不足');
    expect(html, '必须写明缺口原因').toContain('上市');
    expect(html, '缺数据的标的必须仍然列出').toContain('步科');
  });
});

describe('CurrentMarketStrip · 全局位置（独立组件）', () => {
  it('渲染当前市场状态，并明写「不与任何历史行情并列」', () => {
    const html = renderToStaticMarkup(<CurrentMarketStrip />);
    expect(html).toContain('当前市场状态');
    // ★ v0.25：页面显示的日期必须与产物 current_market.asOf **逐字一致**
    //   （用户能分清「当前状态」与「历史数据」的日期，验收标准第 2 条）
    const m = currentMarketOf()!;
    expect(html, `页面未显示产物日期 ${m.asOf}`).toContain(m.asOf!);
    expect(html).toContain('SH000300');
    expect(html).toContain('不与任何历史行情并列');
    expect(html).toContain('不作任何匹配判定');
  });
});
