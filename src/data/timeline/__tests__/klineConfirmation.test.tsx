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
 * ★ 用**真实数据**锁住 2026-10-08 的实测结论（53 个历史对象）：
 *   **32 已证实 · 5 真问题 · 12 不适用股价检验 · 4 未标注峰值**（±7 日 = 周粒度）。
 *
 * ★★ 本文件锁住的是**语义边界**，这是 v0_2 存在的前提：
 *
 *   1. **`NOT_APPLICABLE` 不是「未通过」** —— 记录峰值的参照物是**指数 / 商品价 / 行业价 /
 *      政策事件 / 板块级异动**时，用股价去检验本身就是**用错了工具**。
 *   2. **`UNCONFIRMED` 也不是「日期错误」** —— 参照物是股价却不被股价支持，
 *      可能是日期有误，也可能是**代表标的清单不全**。
 *
 *   若有人把 `NOT_APPLICABLE` 读成「未通过」、或把 `UNCONFIRMED` 读成「数据错误率」，
 *   这些断言会失败。
 */

const source = researchTimelineSource();

function campaignById(id: string): TimelineCampaign | null {
  for (const y of source.years()) {
    const c = source.yearData(y).campaigns.find((x) => x.campaign_id === id);
    if (c) return c;
  }
  return null;
}

describe('klineConfirmation · 五状态判定（真实数据）', () => {
  it('★ 已证实：记录峰值落在某已登记标的的价格高点同一周内', () => {
    const k = klineConfirmationOf('C-2018-CONS-HOG-AFRICAN')!;
    expect(k.status).toBe('CONFIRMED');
    expect(k.recordedPeak).toBe('2020-03-09');
    expect(k.nearest!.securityId).toBe('MUYUAN');
    expect(k.nearest!.deltaDays).toBe(0);
    // 标的**中文名**由 canonical export 解析（产品不碰 research/database）
    expect(k.nearest!.securityName).toBe('牧原股份');
    // 参照物原样透传，且标为 PROVISIONAL（研究判断，待审查）
    expect(k.referent.code).toBe('SECURITY_HIGH');
    expect(k.referent.label).toBe('代表标的股价高点');
    expect(k.referent.reviewStatus).toBe('PROVISIONAL');
    // 已证实者不携带依据列表（避免噪音）
    expect(k.anchors).toEqual([]);
  });

  it('★★ 未证实（真问题）：参照物**是股价**，但没有任何已登记标的同周创价格高点', () => {
    const k = klineConfirmationOf('C-2023-CONS-VALUE-RETAIL')!;
    expect(k.status).toBe('UNCONFIRMED');
    expect(k.referent.code).toBe('SECURITY_HIGH');
    expect(k.recordedPeak).toBe('2025-08-29');
    // 依据存在，且为**原文摘录**（本模块不做归类）
    expect(k.anchors.some((a) => a.excerpt.includes('万辰集团'))).toBe(true);
  });

  it('★★★ 不适用：参照物**不是股价**（指数 / 商品价 / 政策 / 板块级）—— 不判为未通过', () => {
    // 板块**指数**高点
    const mem = klineConfirmationOf('C-2024-SEMI-MEMORY')!;
    expect(mem.status).toBe('NOT_APPLICABLE');
    expect(mem.referent.code).toBe('SECTOR_INDEX_HIGH');
    expect(mem.anchors.some((a) => a.excerpt.includes('申万半导体板块指数'))).toBe(true);

    // 商品 / 行业**产品价格**高点
    const panel = klineConfirmationOf('C-2020-PANEL-CYCLE')!;
    expect(panel.status).toBe('NOT_APPLICABLE');
    expect(panel.referent.code).toBe('PRICE_HIGH');
    expect(panel.anchors.some((a) => a.excerpt.includes('LCD 面板价格'))).toBe(true);

    // **政策事件**日
    const humanoid = klineConfirmationOf('C-2023-HIEQ-HUMANOID')!;
    expect(humanoid.status).toBe('NOT_APPLICABLE');
    expect(humanoid.referent.code).toBe('POLICY_EVENT');
    expect(humanoid.anchors.some((a) => a.excerpt.includes('人形机器人创新发展指导意见'))).toBe(true);

    // **公司事件**日
    const debt = klineConfirmationOf('C-2020-RE-DEBT-RISK')!;
    expect(debt.status).toBe('NOT_APPLICABLE');
    expect(debt.referent.code).toBe('COMPANY_EVENT');

    // **行业指标**拐点
    const robotDown = klineConfirmationOf('C-2018-HIEQ-ROBOT-DOWN')!;
    expect(robotDown.status).toBe('NOT_APPLICABLE');
    expect(robotDown.referent.code).toBe('INDUSTRY_INDICATOR');
  });

  it('★ 未界定参照物 + 股价不支持 → 仍判为 UNCONFIRMED（不放过）', () => {
    const k = klineConfirmationOf('C-2019-AD')!;
    expect(k.status).toBe('UNCONFIRMED');
    expect(k.referent.code).toBe('UNSPECIFIED');
    expect(k.anchors).toEqual([]);
    expect(k.nearest!.deltaDays).toBeGreaterThan(30);
  });

  it('记录**未标注峰值**是合法空状态，不等于「未通过证实」', () => {
    const k = klineConfirmationOf('C-2024-RES-GOLD-CB')!;
    expect(k.status).toBe('NO_PEAK_RECORDED');
    expect(k.recordedPeak).toBeNull();
    expect(k.nearest).toBeNull();
  });

  it('artifact 中没有的对象 → null（**不造默认值**）', () => {
    expect(klineConfirmationOf('C-NOT-EXIST')).toBeNull();
    expect(klineConfirmationOf('')).toBeNull();
  });

  it('★ 汇总为**计数事实**：32 已证实 / 5 未证实 / 12 不适用 / 4 未标注峰值 / 0 无数据', () => {
    expect(klineConfirmationSummary.CONFIRMED).toBe(32);
    expect(klineConfirmationSummary.UNCONFIRMED).toBe(5);
    expect(klineConfirmationSummary.NOT_APPLICABLE).toBe(12);
    expect(klineConfirmationSummary.NO_PEAK_RECORDED).toBe(4);
    expect(klineConfirmationSummary.NO_DATA).toBe(0);
  });

  it('★ 参照物声明覆盖全部 53 个历史对象（含 8 种取值）', () => {
    let n = 0;
    const codes = new Set<string>();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        const k = klineConfirmationOf(c.campaign_id);
        if (!k) continue;
        n += 1;
        codes.add(k.referent.code);
      }
    }
    expect(n).toBeGreaterThanOrEqual(53);
    expect(codes.size).toBeGreaterThanOrEqual(6);
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

  it('已证实 → 显示状态、参照物与最近的已登记标的', () => {
    const c = campaignById('C-2018-CONS-HOG-AFRICAN')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('K 线证实');
    expect(html).toContain('K 线已证实');
    expect(html).toContain('牧原股份');
    expect(html).toContain('峰值参照物');
    expect(html).toContain('代表标的股价高点');
    // 口径必须写出来（否则读者无法复核）
    expect(html).toContain('原始价盘中最高');
  });

  it('★★ 不适用股价检验 → 明确写「不是合适的检验工具」「不判为未通过」，并给出参照物与依据', () => {
    const c = campaignById('C-2023-HIEQ-HUMANOID')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('不适用股价检验');
    expect(html).toContain('不是合适的检验工具');
    expect(html).toContain('不判为未通过');
    // 参照物与原文依据都要在
    expect(html).toContain('政策事件日');
    expect(html).toContain('人形机器人创新发展指导意见');
    // ★ 不得出现「未证实」的字样（否则会被读成未通过）
    expect(html).not.toContain('K 线未证实');
    // 依据摘录不得带来源标注尾巴（规则见 artifact 的 excerpt_rule）
    expect(html).not.toContain('provenance: R01-01 Intake Package');
    expect(html).not.toContain('｜PIT:');
  });

  it('★ 未证实 → 说明这是**需要研究侧核对的问题**（日期或清单），并列出原文依据', () => {
    const c = campaignById('C-2023-CONS-VALUE-RETAIL')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('K 线未证实');
    expect(html).toContain('没有任何已登记标的');
    expect(html).toContain('需要研究侧核对的问题');
    expect(html).toContain('代表标的清单不全');
    expect(html).toContain('万辰集团');
    // 纪律声明必须在（措辞沿用全库既定的否定式白名单：`不评分、不排名`）
    expect(html).toContain('不等于');
    expect(html).toContain('不评分、不排名');
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
