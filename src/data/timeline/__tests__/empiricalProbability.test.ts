/**
 * ★★ 经验基准概率（v0.9）—— 分母 / 排除 / Wilson / 机制区分 / 时间前推。
 *
 * 本文件全部用**仓库真实数据**（`power_historical_events_v0_3` / `flu_historical_events_v0_6`），
 * 不造假样例。唯一例外是 `wilsonInterval` 的数学性质（用合成输入验证公式本身）。
 */
import { describe, it, expect } from 'vitest';

import {
  EMPIRICAL_PROBABILITY_LABEL,
  JEFFREYS_ALPHA,
  JEFFREYS_BETA,
  MODEL_MIN_EX_ANTE_FEATURES,
  MODEL_MIN_OUT_OF_SAMPLE_STEPS,
  assessModelFeasibility,
  comparableCodeOf,
  computeEmpiricalEstimate,
  empiricalTargetOf,
  jeffreysFrequency,
  timeOrderedBaseline,
  wilsonInterval,
  type EmpiricalTarget,
} from '../empiricalProbability';
import {
  crossYearComparisonOf,
  eventMapByTheme,
  type CrossYearYear,
} from '../historicalEventMaps';

const power = eventMapByTheme('POWER_SUMMER')!;
const flu = eventMapByTheme('FLU')!;
const powerCmp = crossYearComparisonOf(power.doc)!;
const fluCmp = crossYearComparisonOf(flu.doc)!;
const powerTarget = empiricalTargetOf(power.doc, powerCmp)!;
const fluTarget = empiricalTargetOf(flu.doc, fluCmp)!;

/* ================================================================ 1. Wilson */

describe('Wilson 95% 区间', () => {
  it('★ 已知值：1/7 的 95% Wilson ≈ [0.0257, 0.5131]', () => {
    const w = wilsonInterval(1, 7)!;
    expect(w.low).toBeCloseTo(0.0257, 3);
    expect(w.high).toBeCloseTo(0.5131, 3);
    expect(w.z).toBe(1.96);
  });

  it('★ 已知值：1/9 的 95% Wilson ≈ [0.0199, 0.4350]', () => {
    const w = wilsonInterval(1, 9)!;
    expect(w.low).toBeCloseTo(0.0199, 3);
    expect(w.high).toBeCloseTo(0.4350, 3);
  });

  it('★★ 小样本的区间**必须**宽（不得用点估计冒充精度）', () => {
    const small = wilsonInterval(1, 7)!;
    const large = wilsonInterval(100, 700)!;
    expect(small.high - small.low).toBeGreaterThan(0.4);
    expect(large.high - large.low).toBeLessThan(0.08);
    // 同一点估计 1/7，样本越小越宽
    expect(small.high - small.low).toBeGreaterThan(large.high - large.low);
  });

  it('★ 边界：k=0 与 k=n 时区间仍在 [0,1] 内且不退化为一个点', () => {
    for (const [k, n] of [[0, 7], [7, 7], [0, 1], [1, 1]] as const) {
      const w = wilsonInterval(k, n)!;
      expect(w.low).toBeGreaterThanOrEqual(0);
      expect(w.high).toBeLessThanOrEqual(1);
      expect(w.high - w.low).toBeGreaterThan(0);
    }
  });

  it('★★ n = 0 → **null**（不得返回 [0,1] 或 [0,0] 冒充结论）', () => {
    expect(wilsonInterval(0, 0)).toBeNull();
    expect(wilsonInterval(1, 0)).toBeNull();
    expect(wilsonInterval(1, Number.NaN)).toBeNull();
  });

  it('★ 成功数被夹到 [0,n]（越界输入不产生荒谬区间）', () => {
    const a = wilsonInterval(-3, 7)!;
    const b = wilsonInterval(99, 7)!;
    expect(a.low).toBeGreaterThanOrEqual(0);
    expect(b.high).toBeLessThanOrEqual(1);
    expect(a).toEqual(wilsonInterval(0, 7));
    expect(b).toEqual(wilsonInterval(7, 7));
  });
});

describe('Jeffreys 平滑频率（评估基准）', () => {
  it('★ 公式：(k + 0.5) / (n + 1)，恒在 (0,1) 内', () => {
    expect(JEFFREYS_ALPHA).toBe(0.5);
    expect(JEFFREYS_BETA).toBe(0.5);
    expect(jeffreysFrequency(0, 0)).toBeCloseTo(0.5, 12);
    expect(jeffreysFrequency(0, 3)).toBeCloseTo(0.125, 12);
    expect(jeffreysFrequency(1, 5)).toBeCloseTo(0.25, 12);
    for (const [k, n] of [[0, 1], [0, 100], [100, 100], [1, 7]] as const) {
      const p = jeffreysFrequency(k, n);
      expect(p).toBeGreaterThan(0);
      expect(p).toBeLessThan(1);
    }
  });

  it('★★ 与原始频率的关系：0 与 1 被拉向 0.5，中间值几乎不变', () => {
    expect(jeffreysFrequency(0, 10)).toBeGreaterThan(0);        // 原始 0 → 不为 0
    expect(jeffreysFrequency(10, 10)).toBeLessThan(1);          // 原始 1 → 不为 1
    expect(Math.abs(jeffreysFrequency(5, 10) - 0.5)).toBeLessThan(0.02);
  });

  it('★ 原始经验比例 k/n 与 Wilson 区间**不受平滑影响**', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    expect(e.rate).toBeCloseTo(1 / 7, 12);          // 仍是 1/7，不是平滑值
    expect(e.wilson!.low).toBeCloseTo(0.0257, 3);   // 仍是未平滑的 Wilson
    expect(e.wilson!.high).toBeCloseTo(0.5131, 3);
  });
});

/* ================================================================ 2. 分母口径 */

describe('★★ 分母：只收 comparable === true', () => {
  it('★★ 电力：分母 = 7（不是 10 个年份，也不是 comparableYears）', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    expect(powerCmp.years).toHaveLength(10);
    expect(e.denominator).toBe(7);
    expect(e.sampleYears).toEqual([2017, 2018, 2020, 2021, 2022, 2023, 2025]);
    // ★ 分母 ≠ 年份总数
    expect(e.denominator).not.toBe(powerCmp.years.length);
  });

  it('★★ 电力：3 个 partial 年份被**逐条**排除，且带源数据原因', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    expect(e.excluded.map((x) => x.year)).toEqual([2016, 2019, 2024]);
    for (const x of e.excluded) {
      expect(x.comparable).toBe('partial');
      expect(x.reason, `${x.year} 必须有排除原因`).toBeTruthy();
      expect(x.reason!.length).toBeGreaterThan(5);
    }
    // ★ 排除的年份**不得**出现在分母里
    for (const x of e.excluded) expect(e.sampleYears).not.toContain(x.year);
  });

  it('★★ 流感：分母 = 9（2015 / 2016 两个 partial 排除）', () => {
    const e = computeEmpiricalEstimate(fluCmp.years, fluTarget);
    expect(fluCmp.years).toHaveLength(11);
    expect(e.denominator).toBe(9);
    expect(e.excluded.map((x) => x.year)).toEqual([2015, 2016]);
    expect(e.excluded.every((x) => x.comparable === 'partial')).toBe(true);
  });

  it('★★ 排除 ≠ 失败：排除年份**既不进分子也不进分母**', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    // 2016 的 outcome 是 DIVERGENT、2024 是 ALL_DOWN —— 若被算成失败，分母会变成 10
    expect(e.denominator + e.excluded.length).toBe(powerCmp.years.length);
    // 分布总和 = 分母（不是年份总数）
    const distTotal = e.distribution.reduce((s, b) => s + b.count, 0);
    expect(distTotal).toBe(e.denominator);
  });

  it('★ 可比性码：true / partial / false / 未记录 四态分明', () => {
    expect(comparableCodeOf({ year: 1, window_type: 'X', outcome: 'UP', comparable: true })).toBe('true');
    expect(comparableCodeOf({ year: 1, window_type: 'X', outcome: 'UP', comparable: 'partial' })).toBe('partial');
    expect(comparableCodeOf({ year: 1, window_type: 'X', outcome: 'UP', comparable: false })).toBe('false');
    // ★ 缺失 → `unrecorded`（不得猜成 false）
    expect(comparableCodeOf({ year: 1, window_type: 'X', outcome: 'UP' })).toBe('unrecorded');
  });

  it('★★ 无任何完整可比较年份 → rate / wilson 均为 null（不补 0）', () => {
    const years: CrossYearYear[] = [
      { year: 2019, window_type: 'X', outcome: 'UP', comparable: 'partial', comparable_reason: '部分可比' },
      { year: 2020, window_type: 'X', outcome: 'ALL_DOWN', comparable: false },
    ];
    const e = computeEmpiricalEstimate(years, powerTarget);
    expect(e.denominator).toBe(0);
    expect(e.successes).toBe(0);
    expect(e.rate).toBeNull();
    expect(e.wilson).toBeNull();
    expect(e.distribution).toEqual([]);
    expect(e.excluded).toHaveLength(2);
  });
});

/* ================================================================ 3. 结果定义 */

describe('★★ 结果定义来自原数据（UP 是严格规则）', () => {
  it('★★ 电力：1/7（唯一 UP = 2022），不是「任意上涨」', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    expect(e.successes).toBe(1);
    expect(e.denominator).toBe(7);
    expect(e.rate).toBeCloseTo(1 / 7, 10);
    expect(e.successYears.map((s) => s.year)).toEqual([2022]);
    // 分布：UP 只有 1 年，DIVERGENT 4 / UNDERPERFORM 2
    const byCode = Object.fromEntries(e.distribution.map((b) => [b.outcome, b.count]));
    expect(byCode.UP).toBe(1);
    expect(byCode.DIVERGENT).toBe(4);
    expect(byCode.UNDERPERFORM).toBe(2);
  });

  it('★★ 非 UP 类**不计入**成功（ALL_DOWN / UNDERPERFORM / DIVERGENT 都不是成功）', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    for (const code of ['ALL_DOWN', 'UNDERPERFORM', 'DIVERGENT']) {
      const bucket = e.distribution.find((b) => b.outcome === code);
      if (!bucket) continue;
      expect(powerTarget.successOutcomes).not.toContain(code);
      expect(e.successYears.some((s) => s.outcome === code)).toBe(false);
    }
  });

  it('★★ 目标定义必须带源数据的 `outcome_rule` 原文（缺规则 → 不构造目标）', () => {
    expect(powerTarget.outcomeRule).toContain('全部上涨');
    expect(powerTarget.outcomeRule).toContain('全部跑赢基准');
    expect(fluTarget.outcomeRule).toContain('全部上涨');
    // 缺 outcome_rule 的文档 → null（宁可不展示，也不自己编规则）
    expect(empiricalTargetOf({ artifact: 'x', artifact_version: '1', position: '', events: [] } as never,
      powerCmp)).toBeNull();
  });

  it('★ 比例是**算出来的**：换一个分母，比例随之改变（无硬编码）', () => {
    const subset = powerCmp.years.filter((y) => y.year >= 2020);
    const e = computeEmpiricalEstimate(subset, powerTarget);
    // 2020..2025 中 comparable=true：2020,2021,2022,2023,2025 = 5；UP 仅 2022
    expect(e.denominator).toBe(5);
    expect(e.successes).toBe(1);
    expect(e.rate).toBeCloseTo(0.2, 10);
    expect(e.rate).not.toBeCloseTo(1 / 7, 3);
  });
});

/* ================================================================ 4. 流感机制 */

describe('★★ 流感：价格结果 ≠ 事件机制', () => {
  it('★★ 唯一 UP 年是 2019/20，事件类型为 UNKNOWN_PUBLIC_HEALTH（非流感）', () => {
    const e = computeEmpiricalEstimate(fluCmp.years, fluTarget);
    expect(e.successYears.map((s) => s.year)).toEqual([2019]);
    const s = e.successYears[0];
    expect(s.eventType).toBe('UNKNOWN_PUBLIC_HEALTH');
    expect(s.seasonLabel).toBe('2019/20 季');
  });

  it('★★ SEASONAL_FLU 年份的 UP 计数 = 0（不得把非流感事件记作流感驱动成功）', () => {
    const e = computeEmpiricalEstimate(fluCmp.years, fluTarget);
    const fluRows = e.mechanismSplit.find((m) => m.eventType === 'SEASONAL_FLU');
    expect(fluRows, '流感季应作为独立机制桶存在').toBeTruthy();
    expect(fluRows!.count).toBeGreaterThan(0);
    expect(fluRows!.successCount).toBe(0);
    // 唯一的成功落在非流感机制桶里
    const nonFlu = e.mechanismSplit.find((m) => m.eventType === 'UNKNOWN_PUBLIC_HEALTH')!;
    expect(nonFlu.successCount).toBe(1);
    // 机制桶年数总和 = 分母（不重不漏）
    expect(e.mechanismSplit.reduce((s, m) => s + m.count, 0)).toBe(e.denominator);
  });

  it('★ 缺 `event_type` 的年份归到 UNRECORDED（不猜成某个机制）', () => {
    const e = computeEmpiricalEstimate(powerCmp.years, powerTarget);
    // 电力逐年没有 event_type 字段
    expect(e.mechanismSplit).toHaveLength(1);
    expect(e.mechanismSplit[0].eventType).toBe('UNRECORDED');
    expect(e.mechanismSplit[0].count).toBe(e.denominator);
  });
});

/* ================================================================ 5. 时间前推 */

describe('★★ 时间前推（expanding window）基线', () => {
  it('★★ 训练集**严格早于**被预测年（无未来信息泄漏）', () => {
    for (const [years, target] of [
      [powerCmp.years, powerTarget],
      [fluCmp.years, fluTarget],
    ] as const) {
      const ev = timeOrderedBaseline(years, target);
      expect(ev.n).toBeGreaterThan(0);
      for (const s of ev.steps) {
        expect(Math.max(...s.trainYears)).toBeLessThan(s.year);
        expect(s.trainYears).not.toContain(s.year);
      }
    }
  });

  it('★★ 预测值 = **Jeffreys 平滑**历史频率（原始 k/n 另行保留作参照）', () => {
    const ev = timeOrderedBaseline(powerCmp.years, powerTarget);
    for (const s of ev.steps) {
      // 评估基准 = (k + 0.5) / (n + 1)
      expect(s.predicted).toBeCloseTo((s.trainSuccesses + 0.5) / (s.trainN + 1), 12);
      // 原始频率仍如实保留（页面展示的 k/n 用它，不参与 Brier / LogLoss）
      expect(s.rawFrequency).toBeCloseTo(s.trainSuccesses / s.trainN, 12);
    }
    expect(ev.baseline.kind).toBe('JEFFREYS_SMOOTHED_FREQUENCY');
    expect(ev.baseline.alpha).toBe(0.5);
    expect(ev.baseline.beta).toBe(0.5);
    expect(ev.baseline.label).toContain('Jeffreys');
  });

  it('★★ 平滑的作用：一次意外成功不再主导整组 LogLoss', () => {
    // 电力 2022 是「训练集 0 成功 → 预测 0 → 实际 1」的那一步
    const ev = timeOrderedBaseline(powerCmp.years, powerTarget);
    const miss = ev.steps.find((s) => s.year === 2022)!;
    expect(miss.trainSuccesses).toBe(0);
    expect(miss.rawFrequency).toBe(0);          // 原始频率确实是 0
    // 该步训练集 = 2017/2018/2020/2021（4 年，0 成功）→ (0 + 0.5) / (4 + 1) = 0.1
    expect(miss.predicted).toBeCloseTo(0.1, 12);
    expect(miss.logLoss).toBeCloseTo(-Math.log(0.1), 9);   // ≈ 2.30，不是 20.7
    // 整组 LogLoss 不再被单步拉到 5+
    expect(ev.pooledLogLoss!).toBeLessThan(1.5);
  });

  it('★★ 步数 = 分母 − minTrain（默认 3）；电力 7−3=4，流感 9−3=6', () => {
    expect(timeOrderedBaseline(powerCmp.years, powerTarget).n).toBe(4);
    expect(timeOrderedBaseline(fluCmp.years, fluTarget).n).toBe(6);
  });

  it('★★ Brier / LogLoss 与逐步值自洽（可复算）', () => {
    const ev = timeOrderedBaseline(powerCmp.years, powerTarget);
    const brier = ev.steps.reduce((s, x) => s + (x.predicted - x.observed) ** 2, 0) / ev.n;
    const logloss = ev.steps.reduce((s, x) => {
      const p = Math.min(1 - 1e-9, Math.max(1e-9, x.predicted));
      return s + -(x.observed === 1 ? Math.log(p) : Math.log(1 - p));
    }, 0) / ev.n;
    expect(ev.pooledBrier!).toBeCloseTo(brier, 9);
    expect(ev.pooledLogLoss!).toBeCloseTo(logloss, 9);
  });

  it('★★ 样本不足时**不假装**能评估校准', () => {
    const ev = timeOrderedBaseline(powerCmp.years, powerTarget);
    expect(ev.n).toBeLessThan(10);
    expect(ev.calibrationNote).toContain('样本不足');
    // 分箱仍然给出（事实陈列），但每箱样本极小
    expect(ev.calibration.reduce((s, b) => s + b.n, 0)).toBe(ev.n);
  });

  it('★★ 可行性判定：4 / 6 步 << 门槛 30 → 明确「不训练模型」', () => {
    const ev = timeOrderedBaseline(powerCmp.years, powerTarget);
    const f = assessModelFeasibility(ev, { comparableYears: 7 });
    expect(MODEL_MIN_OUT_OF_SAMPLE_STEPS).toBe(30);
    expect(f.sufficient).toBe(false);
    expect(f.outOfSampleSteps).toBe(4);
    expect(f.verdict).toContain('不训练');
    // 必须列出缺什么（不是一句「样本不足」了事）
    expect(f.missing.length).toBeGreaterThanOrEqual(2);
    expect(f.missing.join('\n')).toContain('事前');
  });

  it('★★ 步数达标**不等于**具备训练条件（v0.10 修正）', () => {
    const ev = timeOrderedBaseline(fluCmp.years, fluTarget);
    // 步数门槛降到 3 → 6 步达标
    const f = assessModelFeasibility(ev, { required: 3, comparableYears: 9 });
    expect(f.stepsSufficient).toBe(true);
    // 但现有数据**没有任何事前特征** → 仍不具备训练条件
    expect(f.exAnteFeatureCount).toBe(0);
    expect(f.featuresSufficient).toBe(false);
    expect(f.sufficient).toBe(false);
    expect(f.verdict).toContain('不具备训练条件');
    expect(f.verdict).toContain('步数达标 ≠ 可以训练');
  });

  it('★ 两道门槛**同时**满足才叫「可以开始」（不是只看步数）', () => {
    const ev = timeOrderedBaseline(fluCmp.years, fluTarget);
    const f = assessModelFeasibility(ev, {
      required: 3, comparableYears: 9, exAnteFeatureCount: 4,
    });
    expect(f.stepsSufficient).toBe(true);
    expect(f.featuresSufficient).toBe(true);
    expect(f.sufficient).toBe(true);
    expect(f.verdict).toContain('可以开始');
  });

  it('★ 特征够但步数不够 → 仍不训练', () => {
    const ev = timeOrderedBaseline(fluCmp.years, fluTarget);
    const f = assessModelFeasibility(ev, { required: 30, exAnteFeatureCount: 5 });
    expect(f.featuresSufficient).toBe(true);
    expect(f.stepsSufficient).toBe(false);
    expect(f.sufficient).toBe(false);
    expect(f.verdict).toContain('不训练');
  });
});

/* ================================================================ 6. 文案 */

describe('★ 文案口径', () => {
  it('★★ 唯一命名是「探索性经验基准概率」，不得简称「未来概率」', () => {
    expect(EMPIRICAL_PROBABILITY_LABEL).toBe('探索性经验基准概率');
    expect(EMPIRICAL_PROBABILITY_LABEL).not.toContain('未来');
  });
});
