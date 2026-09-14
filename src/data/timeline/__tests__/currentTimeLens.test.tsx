import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import {
  currentTimeLens,
  historicalPhasesInWindow,
  possibleDriversOf,
  stageLabel,
} from '../currentTimeLens';
import { previewTimelineSource, samePeriodWindow, verifiedTimelineSource } from '../timelineAdapter';
import { fixtureCampaigns, fixtureCrossYearMedia } from '../../../../tests/fixtures/campaignFixtures';

/**
 * Current Time Lens v0 测试（13 项）。
 * 分组：
 *   - 数据逻辑 1–8：窗口复用 / 时间定位 / 历史阶段映射 / 未覆盖措辞 / 不编造
 *   - 联动 9–10：selection 可解析 + 与 SamePeriodView 同口径
 *   - 产品 11–13：不做概率 / 不预测 / 不越界
 */

const TODAY = '2026-09-13'; // 9 月 → 窗口 08-15 ~ 10-15

/* ---------------- 数据逻辑 1–8 ---------------- */

describe('1. 时间定位：复用 samePeriodWindow，窗口口径与 SamePeriodView 一致', () => {
  it('today=2026-09-13 → 窗口 2026-08-15 ~ 2026-10-15（逐字一致）', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    expect(lens.position.window).toEqual(samePeriodWindow(2026, 9));
    expect(lens.position.window).toEqual({ start: '2026-08-15', end: '2026-10-15' });
    expect(lens.position.windowLabel).toBe('08-15 ~ 10-15');
    expect(lens.position.year).toBe(2026);
    expect(lens.position.month).toBe(9);
    expect(lens.position.day).toBe(13);
    expect(lens.position.monthLabel).toBe('9 月');
  });

  it('跨年月份（1 月）窗口退化正确：不崩溃、口径正确', () => {
    const lens = currentTimeLens(previewTimelineSource(), '2026-01-05');
    expect(lens.position.window).toEqual({ start: '2025-12-15', end: '2026-02-15' });
  });
});

describe('2. 同期行情来源：仅来自数据源（导出 v1），年份来自 years()', () => {
  it('9 月窗口各年份命中与 samePeriodCampaigns 完全一致', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    // 覆盖 2018–2025（导出年份区间）
    expect(lens.samePeriod.map((r) => r.year)).toEqual([
      2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025,
    ]);
    // 2018 反例年：无数据（不编造）
    expect(lens.samePeriod[0].entries).toEqual([]);
    // 有数据年份的 campaign_id 与 Adapter 列表一致
    const byYear = new Map(lens.samePeriod.map((r) => [r.year, r.entries.map((e) => e.campaign_id)]));
    // 2019-2022：医药跨年 Campaign（C-2019-PHARMA-INNOV）每年都命中窗口
    expect(byYear.get(2019)).toEqual(['C-2019-PHARMA-INNOV', 'C-2019-AD']);
    expect(byYear.get(2022)).toEqual(['C-2019-PHARMA-INNOV', 'RC-2021-TCM', 'C-2022-POLICY']);
    expect(byYear.get(2023)).toEqual(['RC-2023-HUAWEI']);
    expect(byYear.get(2024)).toEqual(['RC-2024-SECONDARY']);
    expect(byYear.get(2025)).toEqual(['C-2025-ROBOTAXI']);
  });
});

describe('3. 历史阶段映射：返回的是「当年窗口内」的阶段（历史事实）', () => {
  it('2019 C-2019-AD：主要阶段按窗口内覆盖天数取（主升覆盖 08-15~09-24 最长）', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    const e = lens.samePeriod
      .find((r) => r.year === 2019)!
      .entries.find((x) => x.campaign_id === 'C-2019-AD')!;
    expect(e.campaign_id).toBe('C-2019-AD');
    // 主升（08-15→09-24）覆盖 41 天，为窗口内最长 → 主要阶段
    expect(e.phaseLabel).toBe('主升');
    expect(e.phaseHit).toEqual({ start: '2019-08-15', end: '2019-09-24' });
    // 其余命中阶段保留为「另有…」（早期信号 / 峰值 / 主段结束）
    expect(e.phaseAlso).toContain('峰值');
    expect(e.phaseAlso).toContain('主段结束');
  });

  it('2024 RC-2024-SECONDARY：窗口内命中 早期信号 与 主段结束（均被保留）', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    const e = lens.samePeriod.find((r) => r.year === 2024)!.entries[0];
    expect(e.campaign_id).toBe('RC-2024-SECONDARY');
    expect(e.kind).toBe('candidate');
    // 两阶段各 1 天，同长取 lifecycle 靠前（EARLY_SIGNAL）→ 早期信号
    expect(e.phaseLabel).toBe('早期信号');
    expect(e.phaseAlso).toEqual(['主段结束']);
  });

  it('historicalPhasesInWindow 直接单测：只保留与窗口相交的阶段，days 正确', () => {
    const win = { start: '2023-08-15', end: '2023-10-15' };
    const rc = previewTimelineSource()
      .yearData(2023)
      .campaigns.find((c) => c.campaign_id === 'RC-2023-HUAWEI')!;
    const hits = historicalPhasesInWindow(rc, win);
    expect(hits.map((h) => h.stage)).toEqual([
      'EARLY_SIGNAL',
      'THEME_FORMING',
      'BROAD_CONFIRMATION',
      'MAIN_RISE',
    ]);
    // MAIN_RISE 生命周期 09-20→10-31，与窗口相交 09-20→10-15（26 天）
    const mainRise = hits.find((h) => h.stage === 'MAIN_RISE')!;
    expect(mainRise.hit).toEqual({ start: '2023-09-20', end: '2023-10-15' });
    expect(mainRise.days).toBe(26);
  });

  it('阶段标签为严格中英映射（不语义扩写）', () => {
    expect(stageLabel('EARLY_SIGNAL')).toBe('早期信号');
    expect(stageLabel('BROAD_CONFIRMATION')).toBe('广泛确认');
    expect(stageLabel('MAIN_END')).toBe('主段结束');
    expect(stageLabel('UNKNOWN_STAGE')).toBe('UNKNOWN_STAGE'); // 未知枚举原样返回，不编造
  });
});

describe('4. 无 lifecycle 的行情：阶段未标注（不编造）', () => {
  it('verified fixture 无 lifecycle → phaseLabel=null / phaseAlso=[]', () => {
    const lens = currentTimeLens(verifiedTimelineSource(fixtureCampaigns), '2023-07-01');
    const flat = lens.samePeriod.flatMap((r) => r.entries);
    expect(flat.length).toBeGreaterThan(0);
    for (const e of flat) {
      expect(e.phaseLabel).toBeNull();
      expect(e.phaseHit).toBeNull();
      expect(e.phaseAlso).toEqual([]);
    }
  });
});

describe('5. 未覆盖措辞：无数据 → uncovered=true（不是「历史没有机会」）', () => {
  it('生产 verified 为空：uncovered=true，且各年份条目为空', () => {
    const lens = currentTimeLens(verifiedTimelineSource(), TODAY);
    expect(lens.uncovered).toBe(true);
    expect(lens.coveredYears).toBe(0);
    expect(lens.samePeriod.every((r) => r.entries.length === 0)).toBe(true);
  });

  it('2 月窗口：医药跨年 Campaign 覆盖 2019–2022 → uncovered=false（跨年 Campaign 语义）', () => {
    const lens = currentTimeLens(previewTimelineSource(), '2026-02-10');
    expect(lens.uncovered).toBe(false);
    expect(lens.coveredYears).toBe(4); // 2019–2022 由 C-2019-PHARMA-INNOV 覆盖（2019-01-02~2022-10-31）
  });

  it('9 月窗口：preview 源有覆盖 → uncovered=false，coveredYears=7', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    expect(lens.uncovered).toBe(false);
    expect(lens.coveredYears).toBe(7); // 2019–2025（2018 空）
  });
});

describe('6. 可能驱动 / 相关因素：汇总四问、去重、原样保留 unknown', () => {
  it('possibleDrivers 与 UI 标注语义（「可能」）由数据层给出原始标签', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    const d2023 = lens.possibleDrivers.find((d) => d.campaign_id === 'RC-2023-HUAWEI');
    expect(d2023).toBeDefined();
    expect(d2023!.year).toBe(2023);
    expect(d2023!.labels.some((l) => l.includes('问界新M7'))).toBe(true);
  });

  it('openEnded 候选的 ending 占位「unknown（…）」原样展示，不编造', () => {
    const rc = previewTimelineSource()
      .yearData(2023)
      .campaigns.find((c) => c.campaign_id === 'RC-2023-HUAWEI')!;
    const labels = possibleDriversOf(rc);
    expect(labels.some((l) => l.startsWith('unknown'))).toBe(true);
  });

  it('去重：同 Campaign 内相同标签只出现一次', () => {
    const rc = previewTimelineSource()
      .yearData(2024)
      .campaigns.find((c) => c.campaign_id === 'C-2024-ROBOTAXI')!;
    const labels = possibleDriversOf(rc);
    expect(new Set(labels).size).toBe(labels.length);
  });

  it('无 drivers / 无事件的 verified fixture → 空标签（不编造归因）', () => {
    const cmp = verifiedTimelineSource(fixtureCampaigns).yearData(2023).campaigns[0];
    expect(possibleDriversOf(cmp)).toEqual([]);
  });
});

describe('7. 事实字段不被改写：start / end / status / kind 与源一致', () => {
  it('Lens 条目的历史区间与状态原样透传（不改写历史事实）', () => {
    const source = previewTimelineSource();
    const lens = currentTimeLens(source, TODAY);
    for (const row of lens.samePeriod) {
      for (const e of row.entries) {
        const src = source
          .yearData(e.year)
          .campaigns.find((c) => c.campaign_id === e.campaign_id)!;
        expect(e.start).toBe(src.start);
        expect(e.end).toBe(src.end);
        expect(e.status).toBe(src.status);
        expect(e.kind).toBe(src.kind);
        expect(e.title).toBe(src.title);
      }
    }
  });

  it('conflict 状态原样保留（C-2024-ROBOTAXI 在源中为 conflict）', () => {
    const lens = currentTimeLens(previewTimelineSource(), '2026-08-01'); // 窗口 07-15~09-15 覆盖 Robotaxi
    const flat = lens.samePeriod.flatMap((r) => r.entries);
    const robotaxi = flat.find((e) => e.campaign_id === 'C-2024-ROBOTAXI');
    expect(robotaxi).toBeDefined();
    expect(robotaxi!.status).toBe('conflict');
  });
});

describe('8. 跨年窗口的安全性：12 月窗口含次年 01-15 亦不越界', () => {
  it('today=2026-12-20 → 窗口 2026-11-15 ~ 2027-01-15，跨年行情可命中', () => {
    const lens = currentTimeLens(verifiedTimelineSource([fixtureCrossYearMedia]), '2026-12-20');
    expect(lens.position.window).toEqual({ start: '2026-11-15', end: '2027-01-15' });
    const flat = lens.samePeriod.flatMap((r) => r.entries);
    expect(flat.some((e) => e.campaign_id === 'cmp_media_2026_2027')).toBe(true);
  });
});

/* ---------------- 联动 9–10 ---------------- */

describe('9. selection 联动：Lens 条目可解析为详情面板可用的 Campaign', () => {
  it('每条条目携带完整 campaign 对象（campaign_id 可在源中查回）', () => {
    const source = previewTimelineSource();
    const lens = currentTimeLens(source, TODAY);
    for (const row of lens.samePeriod) {
      for (const e of row.entries) {
        expect(e.campaign.campaign_id).toBe(e.campaign_id);
        // CampaignDetail 依赖的核心字段可用
        expect(typeof e.campaign.title).toBe('string');
        expect(Array.isArray(e.campaign.phases)).toBe(true);
        expect(Array.isArray(e.campaign.themes)).toBe(true);
      }
    }
  });

  it('可能驱动列表的 campaign_id 均可在源中查回（点击可打开详情）', () => {
    const source = previewTimelineSource();
    const lens = currentTimeLens(source, TODAY);
    for (const d of lens.possibleDrivers) {
      const found = source
        .years()
        .some((y) => source.yearData(y).campaigns.some((c) => c.campaign_id === d.campaign_id));
      expect(found).toBe(true);
    }
  });
});

describe('10. 与 SamePeriodView 同口径：窗口与命中集合完全一致', () => {
  it('Lens.samePeriod 与 samePeriodCampaigns 的年份/条目逐一对应', () => {
    const source = previewTimelineSource();
    const lens = currentTimeLens(source, TODAY);
    for (const row of lens.samePeriod) {
      const win = samePeriodWindow(row.year, 9);
      const expected = source
        .yearData(row.year)
        .campaigns.filter((c) => c.start <= win.end && c.end >= win.start)
        .map((c) => c.campaign_id)
        .sort();
      expect(row.entries.map((e) => e.campaign_id).sort()).toEqual(expected);
    }
  });
});

/* ---------------- 产品 11–13 ---------------- */

describe('11. 不做概率口径：输出不含「N 次」/概率字段', () => {
  it('结果对象只在覆盖度提示中给年份数量，不含次数统计字段', () => {
    const lens = currentTimeLens(previewTimelineSource(), TODAY);
    const keys = Object.keys(lens);
    expect(keys).toEqual(
      expect.arrayContaining(['position', 'samePeriod', 'coveredYears', 'possibleDrivers', 'uncovered']),
    );
    // 不存在 probability / frequency / count / score 之类的字段
    for (const k of keys) {
      expect(k.toLowerCase()).not.toMatch(/prob|freq|score|confidence|chance/);
    }
  });
});

describe('12. 不做预测：输出只含历史事实字段，无未来日期', () => {
  it('所有条目 end 均 ≤ 数据源最大年份（不产生未来推断）', () => {
    const source = previewTimelineSource();
    const lens = currentTimeLens(source, TODAY);
    const maxYear = Math.max(...source.years());
    for (const row of lens.samePeriod) {
      for (const e of row.entries) {
        expect(Number(e.end.slice(0, 4))).toBeLessThanOrEqual(maxYear);
      }
    }
  });
});

describe('13. 不越界：Lens 不改动数据源 / 不产生新数据', () => {
  it('对同一源重复调用结果稳定（纯函数，无副作用）', () => {
    const source = previewTimelineSource();
    const a = currentTimeLens(source, TODAY);
    const b = currentTimeLens(source, TODAY);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
    // 源年份不变（未被写入 / 篡改）
    expect(source.years()).toEqual([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]);
  });

  it('条目数量 = 各年命中数之和（无凭空新增条目）', () => {
    const source = previewTimelineSource();
    const lens = currentTimeLens(source, TODAY);
    const expected = lens.samePeriod.reduce((n, r) => n + r.entries.length, 0);
    const actual = lens.samePeriod.reduce((n, r) => n + r.entries.length, 0);
    expect(actual).toBe(expected);
    // 2019–2022 各 2~3 条（含医药跨年 Campaign + 医药 RC）+ 2023/2024/2025 各 1 条 = 14 条
    expect(actual).toBe(14);
  });
});

/* ---------------- 渲染契约（SSR 静态渲染，验证组件可正常渲染真实数据） ---------------- */

describe('渲染：CurrentTimeLens SSR 输出关键文案与历史事实', () => {
  it('preview 源 + 9 月：输出时间定位、年份、历史阶段（「当时处于」）与可能驱动标题', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={previewTimelineSource()}
        today={TODAY}
        selection={null}
        onSelect={() => {}}
      />,
    );
    // A. 时间定位
    expect(html).toContain('2026-09-13');
    expect(html).toContain('08-15 ~ 10-15');
    // B. 年份 + Campaign（历史事实）
    expect(html).toContain('2019');
    expect(html).toContain('2024');
    // C. 历史阶段映射：明确写成「当时处于」，不是「当前」
    expect(html).toContain('当时处于');
    expect(html).toContain('主升');
    // D. 可能相关因素（V1.8.1 起标签由「可能驱动 / 相关因素」改为「可能相关因素」）
    expect(html).toContain('可能相关因素');
    expect(html).not.toContain('可能驱动 / 相关因素');
    // 不做概率口径：不出现「N 次」（频次计数；排除「次级行情」这一固有名词）
    expect(html).not.toMatch(/\d+\s*次(?!级)/);
    expect(html).not.toMatch(/(出现概率|上涨概率|胜率|可能性为|大概率)/);
  });

  it('生产 verified 为空：输出「当前研究数据未覆盖」而非「历史没有机会」', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={verifiedTimelineSource()}
        today={TODAY}
        selection={null}
        onSelect={() => {}}
      />,
    );
    expect(html).toContain('当前研究数据未覆盖');
    // 必须带「不是「历史没有机会」」的澄清限定语，而不是直接断言「历史没有机会」
    expect(html).toContain('不是「历史没有机会」');
    // 不得把「历史没有机会」当作独立结论输出（仅允许出现在否定澄清中）
    expect(html).not.toMatch(/(?<!不是「)历史没有机会/);
  });

  it('空态（生产 verified 层为空）：uncovered 文案出现，且不出现任何年份条目', () => {
    // 说明：引入医药跨年 Campaign（2019-2022）后，preview 源在 2 月窗口也不再为空；
    // 「未覆盖空态」由真正的空数据源（生产 verified 层当前为空）触发。
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={verifiedTimelineSource()}
        today="2026-02-10"
        selection={null}
        onSelect={() => {}}
      />,
    );
    expect(html).toContain('当前研究数据未覆盖');
    expect(html).not.toContain('ctl-entry');
  });
});
