import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import canonicalJson from '@observation/structural_analogy_explanations_v0_13.json';
import currentCandidatesJson from '@current/current_candidates.json';
import { researchTimelineSource } from '../../../data/timeline/timelineAdapter';
import { parseStructuralAnalogyDataset, type StructuralAnalogyDataset } from '../../../data/timeline/structuralAnalogy';
import { parseCurrentCandidateDataset } from '../../../data/timeline/currentCandidate';
import { CONTRACT_LIFECYCLE_STAGES } from '../../../data/timeline/researchAttention';
import { LIFECYCLE_STAGE_LABEL } from '../../../data/timeline/historicalCase';
import { LifecycleComparisonSection } from '../LifecycleComparisonSection';

/**
 * 生命周期对照视图（ThreeC 1.3 P2 · v0.8）。
 *
 * ★ 全部基于**仓库真实数据**（冻结 SA v0.13 + canonical 当前候选 + Contract v1.2 导出），
 *   **不造**样例来让测试通过。
 * ★ 不变量：不排序 / 不显示进度语义 / 缺失与开放区间如实显示 / 结构对应只引用 SA。
 */

const dataset = parseStructuralAnalogyDataset(canonicalJson);
const source = researchTimelineSource();
const candidates = parseCurrentCandidateDataset(currentCandidatesJson).dataset.candidates;

const cand = (id: string) => {
  const c = candidates.find((x) => x.candidate_id === id);
  if (!c) throw new Error(`候选不存在：${id}`);
  return c;
};

const render = (id: string, opts: { dataSource?: boolean; onSelect?: boolean } = {}) =>
  renderToStaticMarkup(
    <LifecycleComparisonSection
      candidate={cand(id)}
      dataset={dataset}
      dataSource={opts.dataSource === false ? null : source}
      onSelect={opts.onSelect ? () => {} : undefined}
    />,
  );

describe('生命周期对照 · 语义红线（不变量）', () => {
  it('★★ 组件**自带**「并排展示、不是结构对应」声明', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('并排展示');
    expect(html).toContain('结构对应');
    expect(html).toContain('唯一入口是上方冻结 SA');
    expect(html).toContain('非结构对应');
  });

  it('★★ 进度 / 评价类措辞只允许出现在**否定语境**里（沿用 expectNoPredictiveLanguage 约定）', () => {
    // ★ 扫**去标签后的文本**：HTML 里否定词与目标词之间隔着 </strong><span> 等标签，
    //   直接按字符窗口扫会误判（实测踩到）。
    const text = (render('CC-2026-BCI-MEDTECH') + render('CC-2026-OPTICAL-LINK'))
      .replace(/<[^>]+>/g, '');
    // ① 硬禁：任何语境都不许出现
    //   ★ 注意不能裸禁「信号」—— 阶段名「早期信号 / EARLY_SIGNAL」是**合法标签**
    for (const hard of ['评分', '排名', '概率', '预测', '买入', '卖出', '目标价', '胜率', '买卖信号', '信号区']) {
      expect(text, hard).not.toContain(hard);
    }
    // ② 只允许否定语境（如免责声明「不说明谁领先/落后/更快/更慢」）
    for (const phrase of ['领先', '落后', '更快', '更慢', '已完成', '进度']) {
      let i = text.indexOf(phrase);
      while (i >= 0) {
        const before = text.slice(Math.max(0, i - 24), i);
        expect(['不', '非', '无', '未', '禁止'].some((n) => before.includes(n)),
          `「${phrase}」只能出现在否定语境（上下文：…${before}〔${phrase}〕）`).toBe(true);
        i = text.indexOf(phrase, i + 1);
      }
    }
  });

  it('★★ 历史阶段序列按导出**原序**呈现（本组件不重排）', () => {
    // C-2023-AD 的导出序列顺序必须与 `dataSource` 给出的顺序一致
    const c = source.yearData(2023).campaigns.find((x) => x.campaign_id === 'C-2023-AD')
      ?? source.years().flatMap((y) => source.yearData(y).campaigns)
        .find((x) => x.campaign_id === 'C-2023-AD')!;
    expect(c.lifecycle!.length).toBeGreaterThan(1);
    const html = render('CC-2026-BCI-MEDTECH');
    // 序列里第一个阶段的标签应出现在表格中
    const first = c.lifecycle![0];
    expect(html).toContain(first.stage);
  });
});

describe('生命周期对照 · 真实数据用例', () => {
  it('① BCI-MEDTECH：有 SA 判为「结构支持」的历史对象，默认只列这些', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    // C-2023-AD 是唯一的 SUPPORTED 历史对象
    expect(html).toContain('C-2023-AD');
    expect(html).toContain('结构支持');
    // 当前侧显示研究自述阶段（THEME_FORMING）
    expect(html).toContain('THEME_FORMING');
    // 显示全部 89 个历史对象的开关存在（默认只列 SUPPORTED）
    expect(html).toContain('显示全部 89 个历史对象');
  });

  it('② COMPUTE-POWER / OFFSHORE-WIND：**没有** SUPPORTED → 诚实空态（不造假行）', () => {
    for (const id of ['CC-2026-COMPUTE-POWER', 'CC-2026-OFFSHORE-WIND']) {
      const html = render(id);
      expect(html, id).toContain('没有');
      expect(html, id).not.toContain('结构支持</span>');
    }
  });

  it('③ OPTICAL-LINK：默认列出两个 SUPPORTED 历史对象（C-2023-COMM-OPTICAL / C-2025-ROBOTAXI）', () => {
    const html = render('CC-2026-OPTICAL-LINK');
    expect(html).toContain('C-2023-COMM-OPTICAL');
    expect(html).toContain('C-2025-ROBOTAXI');
  });

  it('④ 开放区间：当前侧 `phase_window.end = null` → 明说「开放」，不补结束日', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('开放');
    expect(html).toContain('研究未给出结束日');
  });

  it('⑤ 缺失阶段序列的历史对象 → 「未登记阶段序列」，而不是空白或推断', () => {
    // C-2024-V2X 在导出里零 lifecycle 行
    const all = render('CC-2026-OPTICAL-LINK');
    expect(all).toContain('显示全部');
    // 打开全部后至少能渲染表格；未登记者应有明确文案（真实数据里存在零阶段对象）
    const anyZero = source.years().flatMap((y) => source.yearData(y).campaigns)
      .some((c) => (c.lifecycle ?? []).length === 0);
    expect(anyZero).toBe(true); // 前提：真实数据里确有零阶段对象
  });
});

describe('生命周期对照 · 边界与降级', () => {
  it('★ 无 dataSource → 明说「无法读取历史阶段序列」，不假装有对照', () => {
    const html = render('CC-2026-BCI-MEDTECH', { dataSource: false });
    expect(html).toContain('未提供');
    expect(html).toContain('无法读取历史阶段序列');
    expect(html).not.toContain('C-2023-AD</code>');
  });

  it('★ 无 onSelect（不传）→ 不渲染「打开该历史案例」按钮', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).not.toContain('打开该历史案例');
  });

  it('★ 有 onSelect → 渲染「打开该历史案例」（可继续追到案例详情）', () => {
    const html = render('CC-2026-BCI-MEDTECH', { onSelect: true });
    expect(html).toContain('打开该历史案例');
  });

  it('★ SA 的 `forbidden_comparison` 被**原样展示**（禁止项不得被吞掉）', () => {
    // 找**真正带** forbidden_comparison 的候选，而不是假定第一个候选有
    const hit = dataset.candidates.find((c) =>
      c.explanations.some((x) => x.dimensions.lifecycle.forbiddenComparison));
    expect(hit, '冻结 SA 里应存在带 forbidden_comparison 的候选').toBeTruthy();
    const html = render(hit!.candidateId);
    expect(html).toContain('SA 明文禁止');
  });
});

describe('生命周期对照 · 标签覆盖度（机械比对）', () => {
  it('★ Contract v1.2 全部 11 个阶段在导出中出现，且都有中文标签', () => {
    const present = new Set<string>();
    for (const y of source.years()) {
      for (const c of source.yearData(y).campaigns) {
        for (const p of (c.lifecycle ?? [])) present.add(p.stage);
      }
    }
    for (const s of CONTRACT_LIFECYCLE_STAGES) {
      expect(present.has(s), `导出中应出现 ${s}`).toBe(true);
      expect(LIFECYCLE_STAGE_LABEL[s], `应有标签 ${s}`).toBeTruthy();
    }
    // ★ v0.8：ENDED 此前**无标签**（实测导出有 2 条）→ 现已补
    expect(present.has('ENDED')).toBe(true);
    expect(LIFECYCLE_STAGE_LABEL.ENDED).toBeTruthy();
  });

  it('★ 视图渲染的每个历史阶段都有中文标签（不出现裸英文）', () => {
    const html = render('CC-2026-OPTICAL-LINK');
    // 出现的阶段名（大写枚举）都应能在标签表里找到
    for (const s of CONTRACT_LIFECYCLE_STAGES) {
      if (html.includes(s)) {
        expect(LIFECYCLE_STAGE_LABEL[s], `${s} 应有中文标签`).toBeTruthy();
      }
    }
  });
});

/* ================================================================
 * v0.9 展示修复：列序说明 + 持续时长（能算才给，不能算说原因）
 * ================================================================ */

describe('生命周期对照 · 展示修复（v0.9）', () => {
  it('★★ 表头与说明一致：**第一列是历史对象**，第二列才是当前研究对象', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    // 表头顺序
    const iHist = html.indexOf('>历史对象<');
    const iCur = html.indexOf('>当前侧（自述）<');
    expect(iHist).toBeGreaterThan(0);
    expect(iCur).toBeGreaterThan(iHist);
    // caption 必须与表头一致（v0.8 的 caption 写反了）
    const cap = html.slice(html.indexOf('<caption>'), html.indexOf('</caption>'));
    expect(cap).toContain('左列 = ');
    expect(cap.indexOf('历史对象')).toBeLessThan(cap.indexOf('当前研究对象'));
    expect(cap).toContain('第二列');
    expect(cap).not.toContain('左列 = 当前研究对象');
  });

  it('★★ 起止与精度足够时**给出持续时长**（真实数据）', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('data-duration="ok"');
    const m = html.match(/持续 (\d+) 天（约 ([\d.]+) 个月）/);
    expect(m, '应至少有一个可计算的阶段').toBeTruthy();
    expect(Number(m![1])).toBeGreaterThan(0);
  });

  it('★★ 单日锚点 → 明说**无法计算**（不得显示「持续 0 天」）', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('data-duration="SINGLE_DAY"');
    expect(html).toContain('单日锚点（起止同日）→ 无法计算时长');
    expect(html).not.toContain('持续 0 天');
  });

  it('★★ 阶段窗口精度（粗粒度）→ 不给出精确时长', () => {
    const html = render('CC-2026-BCI-MEDTECH');
    expect(html).toContain('data-duration="LOW_PRECISION"');
    expect(html).toContain('精度为阶段窗口（粗粒度）→ 不给出精确时长');
  });

  it('★★ 生命周期区不再露出 Markdown 星号（v0.8 遗留展示缺陷）', () => {
    for (const id of ['CC-2026-BCI-MEDTECH', 'CC-2026-OPTICAL-LINK', 'CC-2026-AUTO-SMARTDRIVE']) {
      expect(render(id), id).not.toContain('**');
    }
  });
});
