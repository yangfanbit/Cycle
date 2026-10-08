import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import { earlyObservationOf, EARLY_OBSERVATION_SCOPE_NOTE } from '../earlyObservation';
import { CampaignDetail } from '../../../components/CampaignDetail/CampaignDetail';
import type { TimelineCampaign } from '../timelineTypes';

/**
 * 「启动前观察」的不变量测试。
 *
 * ★ 锁住 2026-10-08 实测：核心链路声明的「提前观察」一段**此前从未实现**
 *   （export 里 `early_signal` 0 个 campaign 有值）。本产物实现其**历史侧**。
 *
 * ★★ 锁住**红线**：只描述事实，**不含**概率 / 评分 / 排序 / 预测。
 *
 * ★★ 锁住**已知限制**：6 个当前研究对象**没有标的字段** → 「当前像不像」**无法计算**，
 *   该限制必须**出现在界面上**，不得被掩盖成「功能已完成」。
 */

const source = researchTimelineSource();

function campaignById(id: string): TimelineCampaign | null {
  for (const y of source.years()) {
    const c = source.yearData(y).campaigns.find((x) => x.campaign_id === id);
    if (c) return c;
  }
  return null;
}

describe('earlyObservation · 启动前窗口（真实数据）', () => {
  it('★ 给出启动前 20 个交易日、逐标的的 ex-ante 观测量', () => {
    const e = earlyObservationOf('C-2023-AD')!;
    expect(e).not.toBeNull();
    expect(e.status).toBe('OK');
    expect(e.lookbackTradingDays).toBe(20);
    expect(e.benchmark).toBe('SH000300');
    expect(e.securities.length).toBeGreaterThanOrEqual(3);
    // 窗口必须**止于启动日之前**（ex-ante，不得引入启动后的数据）
    const c = campaignById('C-2023-AD')!;
    for (const s of e.securities) {
      expect(s.atLastDay).not.toBeNull();
      expect(s.atLastDay!.date < c.start).toBe(true);
      for (const p of s.series) expect(p.date < c.start).toBe(true);
    }
    // 相对强度必须能与基准对上：|rel − (ret − bench)| 无法在此断言，只断言数值存在
    const de = e.securities.find((s) => s.securityId === 'DESAYSV')!;
    expect(de.atLastDay!.volPct60).not.toBeNull();
    expect(de.atLastDay!.volRatio).not.toBeNull();
  });

  it('观测量定义与口径随 artifact 透传（分位在 0–1、波动率比为正）', () => {
    const e = earlyObservationOf('C-2023-AD')!;
    for (const s of e.securities) {
      const p = s.atLastDay!;
      if (p.volPct60 !== null) {
        expect(p.volPct60).toBeGreaterThanOrEqual(0);
        expect(p.volPct60).toBeLessThanOrEqual(1);
      }
      if (p.volRatio !== null) expect(p.volRatio).toBeGreaterThan(0);
    }
  });

  it('artifact 中没有的对象 → null（**不造默认值**）', () => {
    expect(earlyObservationOf('C-NOT-EXIST')).toBeNull();
    expect(earlyObservationOf('')).toBeNull();
  });

  it('★ 当前侧限制**必须存在且写明原因**（不得静默省略）', () => {
    expect(EARLY_OBSERVATION_SCOPE_NOTE.length).toBeGreaterThan(20);
    expect(EARLY_OBSERVATION_SCOPE_NOTE).toContain('当前');
    expect(EARLY_OBSERVATION_SCOPE_NOTE).toContain('标的');
  });

  it('★ 语义边界：视图模型**不含**任何 score / 评分 / 概率 / 排名字段', () => {
    const e = earlyObservationOf('C-2023-AD')!;
    const keys = Object.keys(e).map((x) => x.toLowerCase());
    for (const banned of ['score', 'rating', 'rank', 'probability', 'prediction']) {
      expect(keys.some((x) => x.includes(banned))).toBe(false);
    }
  });
});

describe('CampaignDetail · 启动前观察区块（真实数据）', () => {
  const noop = () => {};

  it('渲染「启动前观察」，含逐标的数值与纪律声明', () => {
    const c = campaignById('C-2023-AD')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('启动前观察');
    expect(html).toContain('启动前 20 个交易日');
    expect(html).toContain('德赛西威');
    expect(html).toContain('量分位');
    expect(html).toContain('MA20');
    // 纪律声明必须在（措辞沿用全库既定白名单，避免触发评分词护栏）
    expect(html).toContain('非预测');
    expect(html).toContain('不评分、不排名');
  });

  it('★★ 当前侧不可对照的限制**必须出现在界面上**（不掩盖未完成的部分）', () => {
    const c = campaignById('C-2023-AD')!;
    const html = renderToStaticMarkup(
      <CampaignDetail campaign={c} onOpenRule={noop} onClose={noop} />,
    );
    expect(html).toContain('当前侧');
    expect(html).toContain('没有任何标的字段');
  });
});
