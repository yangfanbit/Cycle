import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import {
  klineConfirmationOf,
  klineConfirmationSummary,
  KLINE_TOLERANCE_DAYS,
} from '../klineConfirmation';
import { CampaignDetail } from '../../../components/CampaignDetail/CampaignDetail';
import type { TimelineCampaign } from '../timelineTypes';

/**
 * 「K 线证实状态」的不变量测试。
 *
 * ★ 用**真实数据**锁住 2026-10-08 的实测结论：
 *   49 个有峰值的 campaign 中 **32 个被 K 线证实、17 个未被证实**（±7 日 = 周粒度）。
 *
 * ★★ 本文件同时锁住**语义边界** —— 这是本模块存在的前提：
 *   「未证实」**不等于**「日期错误」。二者可以同时成立：
 *   记录峰值在 ±7 日内**有记录依据**（指数 / 商品价 / 行业价 / 政策事件），
 *   只是**没有任何已登记标的**在该周创出价格高点。
 *   若有人把这个字段读成「数据错误率」，这些断言会失败。
 */

const source = researchTimelineSource();

function campaignById(id: string): TimelineCampaign | null {
  for (const y of source.years()) {
    const c = source.yearData(y).campaigns.find((x) => x.campaign_id === id);
    if (c) return c;
  }
  return null;
}

describe('klineConfirmation · 状态判定（真实数据）', () => {
  it('★ 已证实：记录峰值落在某已登记标的的价格高点同一周内', () => {
    const k = klineConfirmationOf('C-2018-CONS-HOG-AFRICAN');
    expect(k).not.toBeNull();
    expect(k!.status).toBe('CONFIRMED');
    expect(k!.recordedPeak).toBe('2020-03-09');
    expect(k!.nearest!.securityId).toBe('MUYUAN');
    expect(k!.nearest!.deltaDays).toBe(0);
    // 标的**中文名**由 canonical export 解析（产品不碰 research/database）
    expect(k!.nearest!.securityName).toBe('牧原股份');
    // 已证实者不携带依据列表（避免噪音）
    expect(k!.anchors).toEqual([]);
  });

  it('★★ 未证实：记录峰值不对应任何已登记标的 —— 但**记录里有依据**', () => {
    const k = klineConfirmationOf('C-2023-CONS-VALUE-RETAIL');
    expect(k!.status).toBe('UNCONFIRMED');
    expect(k!.recordedPeak).toBe('2025-08-29');
    // 依据存在，且为**原文摘录**（本模块不做归类）
    expect(k!.anchors.length).toBeGreaterThanOrEqual(1);
    expect(k!.anchors.some((a) => a.excerpt.includes('万辰集团'))).toBe(true);
    // 依据的日期必须落在容差内
    for (const a of k!.anchors) {
      const delta = Math.abs(
        (Date.parse(k!.recordedPeak!) - Date.parse(a.date)) / 86400000,
      );
      expect(delta).toBeLessThanOrEqual(KLINE_TOLERANCE_DAYS);
    }
  });

  it('★ 未证实的依据可以是**非股价口径**（指数 / 商品价 / 政策事件）—— 只给原文，不归类', () => {
    // 面板**价格**峰值，非股价峰值
    const panel = klineConfirmationOf('C-2020-PANEL-CYCLE');
    expect(panel!.status).toBe('UNCONFIRMED');
    expect(panel!.anchors.some((a) => a.excerpt.includes('LCD 面板价格'))).toBe(true);

    // 政策**文件印发日**，非股价峰值
    const humanoid = klineConfirmationOf('C-2023-HIEQ-HUMANOID');
    expect(humanoid!.status).toBe('UNCONFIRMED');
    expect(humanoid!.anchors.some((a) => a.excerpt.includes('人形机器人创新发展指导意见'))).toBe(true);

    // 板块**指数**高点，非个股价格高点
    const memory = klineConfirmationOf('C-2024-SEMI-MEMORY');
    expect(memory!.status).toBe('UNCONFIRMED');
    expect(memory!.anchors.some((a) => a.excerpt.includes('申万半导体板块指数'))).toBe(true);
  });

  it('★ 未证实且**无任何依据** —— 只有少数几条，必须与「有依据」区分', () => {
    const k = klineConfirmationOf('C-2019-AD');
    expect(k!.status).toBe('UNCONFIRMED');
    expect(k!.anchors).toEqual([]);
    // 最近标的差得很远 —— 与「差几日」的口径问题不是一回事
    expect(k!.nearest!.deltaDays).toBeGreaterThan(30);
  });

  it('记录**未标注峰值**是合法空状态，不等于「未通过证实」', () => {
    const k = klineConfirmationOf('C-2024-RES-GOLD-CB');
    expect(k!.status).toBe('NO_PEAK_RECORDED');
    expect(k!.recordedPeak).toBeNull();
    expect(k!.nearest).toBeNull();
  });

  it('artifact 中没有的对象 → null（**不造默认值**）', () => {
    expect(klineConfirmationOf('C-NOT-EXIST')).toBeNull();
    expect(klineConfirmationOf('')).toBeNull();
  });

  it('★ 汇总为**计数事实**：32 证实 / 17 未证实 / 4 未标注峰值 / 0 无数据', () => {
    expect(klineConfirmationSummary.CONFIRMED).toBe(32);
    expect(klineConfirmationSummary.UNCONFIRMED).toBe(17);
    expect(klineConfirmationSummary.NO_PEAK_RECORDED).toBe(4);
    expect(klineConfirmationSummary.NO_DATA).toBe(0);
  });

  it('容差取自 artifact 原文（周粒度），不在产品侧硬编码', () => {
    expect(KLINE_TOLERANCE_DAYS).toBe(7);
  });

  it('★ 语义边界：视图模型**不含**任何 score / 评分 / 概率 / 排名字段', () => {
    const k = klineConfirmationOf('C-2023-CONS-VALUE-RETAIL')!;
    const keys = Object.keys(k).map((x) => x.toLowerCase());
    for (const banned of ['score', 'rating', 'rank', 'probability', 'confidence', 'prediction']) {
      expect(keys.some((x) => x.includes(banned))).toBe(false);
    }
  });
});

describe('CampaignDetail · K 线证实区块（真实数据）', () => {
  const noop = () => {};

  it('已证实的 campaign → 显示状态与最近的已登记标的', () => {
    const c = campaignById('C-2018-CONS-HOG-AFRICAN')!;
    expect(c).not.toBeNull();
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('K 线证实');
    expect(html).toContain('K 线已证实');
    expect(html).toContain('牧原股份');
    // 口径必须写出来（否则读者无法复核）
    expect(html).toContain('原始价盘中最高');
  });

  it('★ 未证实 → 明确写出「不等于日期错误」，并给出原文依据', () => {
    const c = campaignById('C-2023-HIEQ-HUMANOID')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('K 线未证实');
    expect(html).toContain('不等于');
    expect(html).toContain('没有任何已登记标的');
    // 依据原文透传（不归类）
    expect(html).toContain('人形机器人创新发展指导意见');
    // ★ 区块必须**显式声明纪律**：只报计数事实、不归类、不给评分
    expect(html).toContain('不作归类、不给评分');
    // 依据摘录不得带来源标注尾巴（可读性；规则见 artifact 的 excerpt_rule）
    expect(html).not.toContain('provenance: R01-01 Intake Package');
    expect(html).not.toContain('｜PIT:');
  });

  it('未标注峰值 → 说明是合法空状态，而非「未通过证实」', () => {
    const c = campaignById('C-2024-RES-GOLD-CB')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('记录未标注峰值');
    expect(html).toContain('合法空状态');
  });
});
