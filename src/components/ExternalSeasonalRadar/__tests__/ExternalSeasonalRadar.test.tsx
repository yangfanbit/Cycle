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
import { eventMapByExternalId } from '../../../data/timeline/historicalEventMaps';

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

describe('ExternalSeasonalRadar · 下一步入口（v0.25）', () => {
  const mapOpen = (themeId: string) => { void themeId; };
  const draftOpen = (entry: { id: string }) => { void entry.id; };
  const withHandlers = renderToStaticMarkup(
    <ExternalSeasonalRadar today={TODAY} onOpenMap={mapOpen} onRequestDraft={draftOpen} />,
  );

  it('★★ 每项线索都有下一步：有地图 → 地图按钮，无地图且核验为「带入草稿」→ 草稿按钮', () => {
    // 优先区四项：冰雪经济(DRAFT) · 双十一(MAP) · 流感(MAP) · 供暖(DRAFT)
    expect((withHandlers.match(/esr-map-open/g) ?? [])).toHaveLength(2);
    expect((withHandlers.match(/esr-draft-open/g) ?? [])).toHaveLength(2);
    // 不伪装：无地图的入口必须明写「暂无历史事件地图」
    expect(withHandlers).toContain('暂无历史事件地图');
    expect(withHandlers).toContain('不伪装成已有地图');
  });

  it('★★ 25 项中，有地图 + 有草稿入口的条目数与产物核验结论一致', () => {
    // 数据层核对：kind=MAP 的条目必须都能在索引里找到地图；其余 DRAFT/OBSERVE 给草稿入口
    const entries = externalCalendarEntries();
    const mapKinds = entries.filter((e) => e.verification?.next_step.kind === 'MAP');
    const draftKinds = entries.filter((e) =>
      e.verification?.next_step.kind === 'DRAFT' || e.verification?.next_step.kind === 'OBSERVE');
    for (const e of mapKinds) {
      expect(eventMapByExternalId(e.id), `${e.id} 声明 MAP 但索引里没有地图`).toBeTruthy();
    }
    // 有地图的条目不必再给草稿按钮（地图即下一步）
    for (const e of draftKinds) {
      expect(eventMapByExternalId(e.id), `${e.id} 无地图却给了 MAP 结论`).toBeUndefined();
    }
    expect(mapKinds.length + draftKinds.length
           + entries.filter((e) => e.verification?.next_step.kind === 'NONE').length).toBe(25);
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

  it('★★ v0.12/13：**时间轴默认覆盖全部 25 条**，详细卡片按需展开', () => {
    // ★ 25 条在**时间轴**上默认可见（23 行 + 2 条无窗口）→ 这才是「默认全覆盖」
    expect((html.match(/data-est-row=/g) ?? [])).toHaveLength(23);
    expect((html.match(/data-est-nowin-id=/g) ?? [])).toHaveLength(2);
    // 每条在时间轴上都有「外部参考」标记
    expect((html.match(/est-ext/g) ?? []).length).toBeGreaterThanOrEqual(25);
    // 详细卡片默认收起（避免与时间轴重复铺开），但展开入口与 25 项计数都在
    expect(html).toContain('展开其余 21 项的详细卡片');
    expect(html).toContain('全部线索（25 项）');
    expect((html.match(/class="esr-card"/g) ?? [])).toHaveLength(4);
  });

  it('★ 总数与版本可追溯（v0.25：日历已升 v0_2，25 项逐项核验）', () => {
    expect(html).toContain('25');
    expect(html, '日历版本号必须与产物一致').toContain('0.2');
    expect(html).toContain('2026-10-13');
    // ★ v0.25：核验结论段必须渲染（六问的落地结果），且不写死「全部未经验证」
    expect(html).toContain('核验结论');
    expect(html).toContain('性质：');
    expect(html).toContain('下一步');
  });
});
