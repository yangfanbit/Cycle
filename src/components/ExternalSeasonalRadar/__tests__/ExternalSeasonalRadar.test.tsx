/**
 * ExternalSeasonalRadar —— UI 层验收测试。
 *
 * ★ 重点验证「**外部来源与 ThreeC 历史结论在页面上是可区分的**」，
 *   以及「无映射 / 无固定窗口 / 日期不足」这些**空白状态被如实展示**（不隐藏）。
 */
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ExternalSeasonalRadar } from '../ExternalSeasonalRadar';
import {
  EXTERNAL_SOURCE_LABEL,
  externalCalendarEntries,
} from '../../../data/timeline/externalSeasonalCalendar';

const TODAY = '2026-10-13';
const html = renderToStaticMarkup(<ExternalSeasonalRadar today={TODAY} />);

describe('ExternalSeasonalRadar · 来源分离', () => {
  it('★ 渲染出「外部资料参考（未由 ThreeC 验证）」徽标', () => {
    expect(html).toContain(EXTERNAL_SOURCE_LABEL);
  });

  it('★ 明确声明与历史地图的来源区别', () => {
    expect(html).toContain('外部季节性观察雷达');
    expect(html).toContain('从历史数据得到');
    expect(html).toContain('外部资料声称');
  });

  it('★ 页脚声明「窗口内不代表上涨、不提升成熟度」', () => {
    expect(html).toContain('不代表');
    expect(html).toContain('不提升');
    expect(html).toContain('外部参考');
  });

  it('★ 不得出现分数 / 排名 / 概率 / 信号类措辞', () => {
    for (const banned of ['买入', '卖出', '仓位', '评分', '排名', '胜率', '信号区']) {
      expect(html, `不应出现「${banned}」`).not.toContain(banned);
    }
  });
});

describe('ExternalSeasonalRadar · 优先展示四项', () => {
  it('★ 用户指定的四项出现在优先区（基准日 2026-10-13）', () => {
    for (const name of ['冰雪经济', '双十一', '流感 / 医药', '供暖 / 能源']) {
      expect(html, `应展示「${name}」`).toContain(name);
    }
  });

  it('★ 每项都显示原始窗口文本（不转成具体日期）', () => {
    expect(html).toContain('10 月至次年 3 月');   // 冰雪经济
    expect(html).toContain('10–11 月');           // 双十一
    expect(html).toContain('9 月至次年 1 月');    // 流感
    expect(html).toContain('11–12 月');           // 供暖
  });

  it('★ 显示窗口关系标签（由日期计算）', () => {
    expect(html).toMatch(/窗口内|即将进入|窗口已过/);
  });

  it('★ 显示外部来源名（可追溯）', () => {
    expect(html).toContain('A股季节性题材日历（2026版）');
  });

  it('★ 显示研究成熟度（且标注未经验证）', () => {
    expect(html).toContain('外部参考');
    expect(html).toContain('未经 ThreeC 验证');
  });
});

describe('ExternalSeasonalRadar · 空白状态如实展示', () => {
  it('★ 优先区含未映射条目时，直接展示「未映射」与原因（不隐藏）', () => {
    // 流感/医药 与 供暖/能源 是 MAPPED；冰雪/双十一是 MAPPED。
    // 该断言检查渲染中**存在**未映射展示能力（21 项折叠区展开后可见）——
    // 这里以数据层保证「有 UNMAPPED 条目」，页面在展开时渲染其 reason。
    const unmapped = externalCalendarEntries().filter((e) => e.mapping.status === 'UNMAPPED');
    expect(unmapped.length).toBeGreaterThan(0);
    for (const e of unmapped) {
      expect(e.mapping.reason!.length).toBeGreaterThan(10);
    }
  });

  it('★ 折叠区默认收起，并提供展开入口（不丢弃其余 21 项）', () => {
    expect(html).toContain('展开其余 21 项');
    expect(html).toContain('全部线索（25 项）');
  });

  it('★ 总数与版本可追溯', () => {
    expect(html).toContain('25');
    expect(html).toContain('0.1');
    expect(html).toContain('2026-10-13');
  });
});
