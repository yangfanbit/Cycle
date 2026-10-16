import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import App from '../../App';
import { researchTimelineSource } from '../../data/timeline/timelineAdapter';
import { parseCurrentCandidateDataset } from '../../data/timeline/currentCandidate';
import { selectCurrentCandidateDataset } from '../../data/timeline/appDatasets';
import { lookupDirection } from '../../data/timeline/directionLookup';
import { noneExplain } from '../DirectionLookup/DirectionLookupSection';
import canonicalJson from '@current/current_candidates.json';

/**
 * 分类体系（taxonomy）与「覆盖」语义 —— 真实数据回归（v0.7 · C 工作流）。
 *
 * ★★ 本文件守护的核心命题：
 *   **「根主题清单」是分类体系事实，不是覆盖承诺**；
 *   **「不在根清单里」不等于「未覆盖」** —— 具体结论由查询的实际命中给出。
 *
 * v0.6 的横幅曾写「不在此列表内的方向即为未覆盖」—— 实测为**假**
 * （44/46 个非根主题名都能命中历史对象）。本文件用真实数据把该语义钉死。
 */

const source = researchTimelineSource();
const dataset = selectCurrentCandidateDataset({ exampleFixture: false });

const roots = (source.taxonomy?.() ?? []).filter((n) => n.parent_theme_id === null);
const rootNames = roots.map((n) => n.name);

/** 某根主题下挂靠的历史对象数（用真实查询反推：查根名 → 历史命中数） */
const historicalHits = (q: string) => lookupDirection(q, source, dataset).historical.length;

describe('分类体系 · 根主题是分类事实（不是覆盖承诺）', () => {
  it('★ 根主题来自 taxonomy 数据（非人工硬编码），且含文化传媒', () => {
    expect(rootNames.length).toBeGreaterThanOrEqual(13);
    expect(rootNames).toContain('文化传媒');
    expect(rootNames).toContain('医药健康');
    expect(rootNames).toContain('电子');
  });

  it('★★ 根主题存在 ≠ 对象充足：至少有一个根下历史对象**极少**（≤2）', () => {
    // 实测：电力设备 / 电力（运营端）各仅 2 个 → 在清单内也可能几乎没有覆盖
    const counts = rootNames.map((n) => ({ n, c: historicalHits(n) }));
    const thin = counts.filter((x) => x.c <= 2);
    expect(thin.length, `极少的根：${JSON.stringify(thin)}`).toBeGreaterThanOrEqual(1);
    // ★ 但都**不是 0** —— 如实报告，不制造反例
    for (const { n, c } of counts) expect(c, n).toBeGreaterThan(0);
  });

  it('★★ 不在根清单里的**具体名称**仍可能命中（不得仅凭「不在列表内」判未覆盖）', () => {
    const r = lookupDirection('半导体', source, dataset);
    // 「半导体」是**子主题名**（属根「电子」），不在根清单里，但确实有历史命中
    expect(rootNames).not.toContain('半导体');
    expect(r.historical.length).toBeGreaterThan(0);
    expect(r.verdict).toBe('historical-only');
    // 名称解析如实说明它属哪个根
    expect(r.resolution?.matchedTheme?.name).toBe('半导体');
    expect(r.resolution?.root?.name).toBe('电子');
  });

  it('★★ 非库内名称也可能命中（「电力」不是库内主题名，却有命中）', () => {
    const r = lookupDirection('电力', source, dataset);
    // 库内根名是「电力设备」/「电力（运营端）」，精确名「电力」不在主题表里
    expect(rootNames).not.toContain('电力');
    expect(r.resolution?.matchedTheme).toBeNull();
    // 但子串匹配命中两侧 → 这正是「不在清单 ≠ 未覆盖」的最强反例
    expect(r.historical.length).toBeGreaterThan(0);
    expect(r.verdict).toBe('both');
  });

  it('★★ 四个事实互不相同：主题存在 / 直接挂靠 / 根下对象 / 当前侧对象', () => {
    // 「半导体材料」：库内主题存在、根下有 12 个对象，但**该主题直接挂靠 0 个** → none
    const r = lookupDirection('半导体材料', source, dataset);
    expect(r.verdict).toBe('none');
    expect(r.resolution?.matchedTheme?.name).toBe('半导体材料');
    expect(r.resolution?.directObjectCount).toBe(0);
    expect(r.resolution?.rootObjectCount).toBeGreaterThan(0);
    expect(r.resolution?.root?.name).toBe('电子');
  });

  it('★ 库内主题但无对象 ≠ 不在库内（两种「没有」必须分开说）', () => {
    const inLib = lookupDirection('半导体材料', source, dataset);
    const outLib = lookupDirection('动力煤', source, dataset);
    expect(inLib.verdict).toBe('none');
    expect(outLib.verdict).toBe('none');
    expect(inLib.resolution?.matchedTheme).not.toBeNull();
    expect(outLib.resolution?.matchedTheme).toBeNull();
    expect(inLib.resolution?.taxonomySize).toBe(outLib.resolution?.taxonomySize);
  });

  it('★ 孤儿对象不被隐藏（`RC-2023-HUAWEI` 不是任何主题名，但可被查询命中）', () => {
    const r = lookupDirection('华为汽车', source, dataset);
    expect(r.historical.length).toBeGreaterThan(0);
    expect(r.historical.some((h) => h.id.includes('HUAWEI'))).toBe(true);
    // ★ 它**不是**分类体系里的主题名（因此只能靠查询命中，不可能出现在根清单里）
    const allThemeNames = (source.taxonomy?.() ?? []).map((n) => n.name);
    expect(allThemeNames).not.toContain('华为汽车');
    // ★ 若产品只按「根清单」判断覆盖，这个对象会被完全漏掉 —— 这正是「不在清单 ≠ 未覆盖」
  });
});

describe('分类体系 · 横幅文案（App 层，真实渲染）', () => {
  const html = renderToStaticMarkup(<App />);

  it('★★ 横幅把根清单描述为**分类体系**，而不是「覆盖」承诺', () => {
    expect(html).toContain('分类体系');
    expect(html).toContain('根主题');
    // ★ 不得再出现 v0.6 的二元断言
    expect(html).not.toContain('不在此列表内的方向即为');
    expect(html).not.toContain('历史研究当前覆盖');
  });

  it('★★ 横幅明说「不在根清单里 ≠ 未覆盖」，并把裁决权交给方向查询', () => {
    expect(html).toContain('并不等于');
    expect(html).toContain('具体结论以方向查询的实际命中为准');
  });

  it('★★ 横幅列出四个**互不相同**的事实（不得合并成一个二元标签）', () => {
    expect(html).toContain('四件事互不相同');
    expect(html).toContain('分类体系里有没有对应根主题');
    expect(html).toContain('查询有没有命中对象');
    expect(html).toContain('有没有冻结 SA 给出的结构对应');
    expect(html).toContain('资料不足');
  });

  it('★ 横幅保留两条语义边界（名字 ≠ 结构对应；未覆盖 ≠ 结构上无对应）', () => {
    expect(html).toContain('名字没命中 ≠ 结构上无对应');
    expect(html).toContain('名字命中 ≠ 结构对应');
  });

  it('★ 横幅含真实根名（数据驱动，不是人工列表）', () => {
    for (const n of ['文化传媒', '医药健康', '电力设备']) {
      expect(html, n).toContain(n);
    }
  });

  it('★★ 横幅与方向查询**不矛盾**：横幅会判「未覆盖」的词，查询也不得命中', () => {
    // ★ 这是 v0.6 的同页矛盾（横幅说半导体未覆盖、示例却用半导体）的回归守卫。
    //   现在横幅只说分类事实 → 只需保证：真正未命中的词，两侧都没命中。
    for (const q of ['动力煤', '娱乐']) {
      const r = lookupDirection(q, source, dataset);
      expect(r.verdict, q).toBe('none');
      expect(r.historical.length + r.current.length, q).toBe(0);
    }
    // 而命中过的词，绝不能同时被文案判为「未覆盖」
    const semis = lookupDirection('半导体', source, dataset);
    expect(semis.verdict).not.toBe('none');
  });
});

describe('分类体系 · 主题计数不得硬编码', () => {
  it('★ 「未覆盖」说明的主题总数由**数据**注入（不再写死 44）', () => {
    const n = lookupDirection('动力煤', source, dataset).resolution?.taxonomySize ?? 0;
    expect(n).toBeGreaterThan(44); // 实测已增至 59
    // ★ 纯函数直测（该文案只在查询返回 none 后渲染，SSR 无法触达）
    const lines = noneExplain(n);
    expect(lines[0]).toContain(`库内 ${n} 个主题名`);
    expect(noneExplain(999)[0]).toContain('库内 999 个主题名'); // 完全由参数决定
    expect(lines.join('\n')).not.toContain('44');
  });

  it('★ canonical 当前候选仍为 6 个（示例 fixture 不参与默认路径）', () => {
    expect(parseCurrentCandidateDataset(canonicalJson).dataset.candidates).toHaveLength(6);
    expect(dataset.candidates).toHaveLength(6);
  });
});
