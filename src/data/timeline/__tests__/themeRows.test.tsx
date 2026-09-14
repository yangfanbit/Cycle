import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { SamePeriodView } from '../../../components/SamePeriodView/SamePeriodView';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import {
  UNTITLED_THEME_KEY,
  UNTITLED_THEME_TITLE,
  primaryThemeName,
  themeRowsOf,
} from '../themeRows';
import {
  previewTimelineSource,
  samePeriodCampaigns,
  verifiedTimelineSource,
} from '../timelineAdapter';
import { fixtureCampaigns } from '../../../../tests/fixtures/campaignFixtures';

/**
 * V1.8.1 主题级历史机会视图测试（11 项场景 + IA / 产品约束）。
 *
 * 分组：
 *   - 主题分组 1–8：一行一主题 / 主主题选取 / 同主题多条不合并 / RC badge /
 *                    阶段映射 / 相关概念 / 未标注主题 / 与 samePeriodCampaigns 口径一致
 *   - IA 9：Timeline 在前、Lens 在后（页面顺序）
 *   - 产品 10：无交易建议措辞
 *   - 产品 11：不由 Event 自动生成相关因素
 */

const SEPT = 9; // 9 月 → 窗口 08-15 ~ 10-15
const TODAY = '2026-09-13';

/** 渲染顺序提取：同时含两个视图的页面片段中，Timeline 必须先于 Lens 出现 */
function indexOfFirst(hay: string, needle: string): number {
  return hay.indexOf(needle);
}

/* ---------------- 主题分组 1–8 ---------------- */

describe('1. 一行 = 一个主主题（不是一行一个 Campaign）', () => {
  it('9 月窗口：主题行数量 < 同期 Campaign 总数（已聚类）', () => {
    const src = previewTimelineSource();
    const result = themeRowsOf(src, SEPT);
    const totalCampaigns = samePeriodCampaigns(src, SEPT)
      .flatMap((r) => r.campaigns).length;
    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows.length).toBeLessThan(totalCampaigns);
  });

  it('每行的 themeKey = 该组主主题名，且行内每条行情都归属于同一主主题', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    for (const row of result.rows) {
      for (const e of row.campaigns) {
        if (row.untitled) {
          expect(e.mainTheme).toBeNull();
        } else {
          expect(e.mainTheme).toBe(row.themeKey);
        }
      }
    }
  });
});

describe('2. 主主题选取：role=main 优先，否则第一个主题', () => {
  it('primaryThemeName：main 优先于 related', () => {
    expect(
      primaryThemeName({
        themes: [
          { name: '汽车', role: 'related' },
          { name: '新能源汽车/电池', role: 'main' },
        ],
      }),
    ).toBe('新能源汽车/电池');
  });

  it('primaryThemeName：无 main 时取第一个；无主题时 null（不编造）', () => {
    expect(primaryThemeName({ themes: [{ name: 'A', role: 'secondary' }] })).toBe('A');
    expect(primaryThemeName({ themes: [] })).toBeNull();
  });
});

describe('3. 同主题多条独立行情：聚类但不合并（明细仍逐条）', () => {
  it('新能源汽车/电池 主题在 2020/2021/2022 各有一条独立行情，全部保留', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const row = result.rows.find((r) => r.themeKey === '新能源汽车/电池');
    // 2020 与 2021 该主题为 main；2022 为 related（归入 汽车消费/购置税刺激 主主题）
    expect(row).toBeDefined();
    const years = row!.campaigns.map((e) => e.year);
    expect(years).toContain(2020);
    expect(years).toContain(2021);
    // 独立行情不合并：每条有各自 campaign_id
    const ids = new Set(row!.campaigns.map((e) => e.campaign_id));
    expect(ids.size).toBe(row!.campaigns.length);
  });

  it('行内明细按年份升序，且每条携带原始 campaign 对象（供 selection 使用）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    for (const row of result.rows) {
      const ys = row.campaigns.map((e) => e.year);
      expect([...ys].sort((a, b) => a - b)).toEqual(ys);
      for (const e of row.campaigns) {
        expect(e.campaign.campaign_id).toBe(e.campaign_id);
      }
    }
  });
});

describe('4. RC 保留独立行情身份（badge，不升级状态、不合并进正式 Campaign）', () => {
  it('2023 RC-2023-HUAWEI 与 2024 RC-2024-SECONDARY 均为 kind=candidate', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const all = result.rows.flatMap((r) => r.campaigns);
    const rc2023 = all.find((e) => e.campaign_id === 'RC-2023-HUAWEI');
    const rc2024 = all.find((e) => e.campaign_id === 'RC-2024-SECONDARY');
    expect(rc2023?.kind).toBe('candidate');
    expect(rc2024?.kind).toBe('candidate');
    // RC 不映射为 verified
    expect(rc2023?.status).not.toBe('verified');
    expect(rc2024?.status).not.toBe('verified');
  });
});

describe('5. 阶段映射：当年窗口内主要阶段（历史事实）+ 其余保留为 phaseAlso', () => {
  it('2019 智能驾驶/无人驾驶：窗口内主要阶段与 currentTimeLens 口径一致（主升）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const row = result.rows.find((r) => r.themeKey === '智能驾驶/无人驾驶');
    expect(row).toBeDefined();
    const e2019 = row!.campaigns.find((e) => e.year === 2019)!;
    expect(e2019.phaseLabel).toBe('主升');
    expect(e2019.phaseAlso.length).toBeGreaterThan(0);
  });

  it('主题行 primaryPhase 与 phaseSummary 一致（代表阶段必来自组内命中的阶段标签）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    for (const row of result.rows) {
      if (row.primaryPhase === null) {
        expect(row.phaseSummary).toBe('阶段未标注');
      } else {
        expect(row.phaseSummary).toContain('个年份');
        expect(row.campaigns.map((e) => e.phaseLabel)).toContain(row.primaryPhase);
      }
    }
  });

  /**
   * 已知限制（Audit Finding F-MED-1）：
   * 跨年（多年度）Campaign 的行级代表阶段为 null —— `themeRows.ts` 构造入口时
   * `year: c.year` 取的是 campaign 自身年份，而非**所属行的年份**，导致行级聚合
   * 用错 `samePeriodWindow`（本轮医药 Campaign 为 2019-01-02~2022-10-31，暴露该缺陷）。
   * 汽车案例 campaign_year == 展示年，故一直未暴露。
   * 本用例固定当前行为；F-MED-1 修复后应同步改为「primaryPhase 非空」。
   */
  it('已知限制 F-MED-1：跨年 Campaign 行的 primaryPhase 为 null（待修复）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const row = result.rows.find((r) => r.themeKey === '创新药')!;
    expect(row).toBeDefined();
    expect(row.campaigns.map((e) => e.phaseLabel)).toEqual([null, '主升', '退潮', '退潮']);
    expect(row.primaryPhase).toBeNull();
    expect(row.phaseSummary).toBe('阶段未标注');
  });
});

describe('6. 相关概念：组内其余主题名去重（不含主主题本身）', () => {
  it('新能源汽车/电池 行的相关概念包含「汽车」（related 主题）', () => {
    const result = themeRowsOf(previewTimelineSource(), SEPT);
    const row = result.rows.find((r) => r.themeKey === '新能源汽车/电池')!;
    expect(row.relatedConcepts).toContain('汽车');
    expect(row.relatedConcepts).not.toContain('新能源汽车/电池');
    // 去重
    expect(new Set(row.relatedConcepts).size).toBe(row.relatedConcepts.length);
  });
});

describe('7. 未标注主题：无 theme 信息时归入占位组（不编造主题名）', () => {
  it('verified fixture（无 themes）→ 单行 untitled，标题为「未标注主题」', () => {
    const result = themeRowsOf(verifiedTimelineSource(fixtureCampaigns), 7);
    const untitled = result.rows.filter((r) => r.untitled);
    expect(untitled.length).toBe(1);
    expect(untitled[0].themeKey).toBe(UNTITLED_THEME_KEY);
    expect(untitled[0].title).toBe(UNTITLED_THEME_TITLE);
    expect(untitled[0].relatedConcepts).toEqual([]);
  });
});

describe('8. 与 samePeriodCampaigns 完全同口径（不发明新日期逻辑）', () => {
  it('主题行内 campaign_id 集合 = samePeriodCampaigns 输出的并集', () => {
    const src = previewTimelineSource();
    const expected = new Set(
      samePeriodCampaigns(src, SEPT).flatMap((r) => r.campaigns.map((c) => c.campaign_id)),
    );
    const actual = new Set(
      themeRowsOf(src, SEPT).rows.flatMap((r) => r.campaigns.map((e) => e.campaign_id)),
    );
    expect(actual).toEqual(expected);
  });

  it('生产 verified 为空 → 无主题行，uncovered = true', () => {
    const result = themeRowsOf(verifiedTimelineSource(), SEPT);
    expect(result.rows).toEqual([]);
    expect(result.uncovered).toBe(true);
  });
});

/* ---------------- IA 9 / 产品 10–11 ---------------- */

describe('9. IA：Timeline 是第一视觉，Current Time Lens 降级其后', () => {
  it('Isource 顺序证明：Timeline 在 Lens 之前（App 中顺序由 App.tsx 保证，此处校验组件语义）', () => {
    // 直接检验 App.tsx 源码顺序，避免依赖 jsdom 渲染
    // （在测试中读取源码文件，断言 Timeline 的 JSX 出现在 CurrentTimeLens 之前）
    const fs = require('node:fs') as typeof import('node:fs');
    const path = require('node:path') as typeof import('node:path');
    const appSrc = fs.readFileSync(
      path.resolve(__dirname, '../../../App.tsx'),
      'utf-8',
    );
    expect(indexOfFirst(appSrc, '<Timeline')).toBeLessThan(indexOfFirst(appSrc, '<CurrentTimeLens'));
    // SamePeriodView 主题行视图也在 Lens 之前
    expect(indexOfFirst(appSrc, '<SamePeriodView')).toBeLessThan(
      indexOfFirst(appSrc, '<CurrentTimeLens'),
    );
  });

  it('SamePeriodView 渲染主题行（一行 = 主题），且标题为「历史同周期主题」', () => {
    const html = renderToStaticMarkup(
      <SamePeriodView dataSource={previewTimelineSource()} today={TODAY} />,
    );
    expect(html).toContain('历史同周期主题');
    expect(html).toContain('sp-theme-row');
    // 不应再是每年一行的旧结构
    expect(html).toContain('sp-theme-title');
  });

  it('CurrentTimeLens 标题为「当前时间上下文」（降级，不再自称顶部入口）', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={previewTimelineSource()}
        today={TODAY}
        selection={null}
        onSelect={() => {}}
      />,
    );
    expect(html).toContain('当前时间上下文');
    expect(html).not.toContain('Current Time Lens');
  });
});

describe('10. 产品：界面不含交易建议 / 预测措辞', () => {
  it('SamePeriodView + Lens 渲染文本不含买入 / 建议 / 会涨 等措辞', () => {
    const html =
      renderToStaticMarkup(<SamePeriodView dataSource={previewTimelineSource()} today={TODAY} />) +
      renderToStaticMarkup(
        <CurrentTimeLens
          dataSource={previewTimelineSource()}
          today={TODAY}
          selection={null}
          onSelect={() => {}}
        />,
      );
    for (const banned of ['买入', '卖出', '建议买', '会涨', '目标价', '止盈', '止损', '仓位']) {
      expect(html).not.toContain(banned);
    }
  });
});

describe('11. 产品：可能相关因素不由 Event 自动生成（沿用 Research 归因口径）', () => {
  it('Lens 的「可能相关因素」标签来自 campaignDrivers（drivers/事件归组），非本视图新造', () => {
    const src = previewTimelineSource();
    const row2025 = src.yearData(2025).campaigns.find((c) => c.campaign_id === 'C-2025-ROBOTAXI');
    expect(row2025?.drivers).toBeDefined(); // 导出携带研究层归因
    const html = renderToStaticMarkup(
      <CurrentTimeLens dataSource={src} today={TODAY} selection={null} onSelect={() => {}} />,
    );
    expect(html).toContain('可能相关因素');
    expect(html).not.toContain('可能驱动 / 相关因素');
  });
});
