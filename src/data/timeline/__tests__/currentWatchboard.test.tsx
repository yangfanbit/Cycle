import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { buildWatchboard, WATCHBOARD_DISCLAIMER } from '../currentWatchboard';
import { CurrentWatchboardSection } from '../../../components/CurrentWatchboard/CurrentWatchboardSection';

/**
 * 「当前观察台」的不变量测试。
 *
 * ## ★★★ 本文件锁住的**最重要**一条：**阶段不得静默取一**
 *
 * `current_candidates.json` 元信息写明「阶段由**产品端** Phase Evidence Matrix 独立推导，**不由研究声明决定**」；
 * 引擎 `PhaseInference` 写明「推导阶段是**权威值**」，且「**不一致时 UI 必须并列显示，不得静默取一**」。
 *
 * 实测：6 个当前对象中 **2 个不一致** —— `CC-2026-BCI-MEDTECH` 与 `CC-2026-AUTO-SMARTDRIVE`
 * 的**推导值为 `UNKNOWN`**（R8：证据组合不满足任何阶段规则），而研究声明为 `THEME_FORMING`。
 *
 * 本模块 v0_1 曾直接读 `attention_state`，把两者都显示成「主题形成」—— **静默取了声明值**。
 * 这些断言防止它复发。
 */

describe('currentWatchboard · 阶段来源（真实数据）', () => {
  it('★★★ 推导值 ≠ 声明值时，**两者并列**保留，不静默取一', () => {
    const wb = buildWatchboard();
    const all = wb.groups.flatMap((g) => g.items);
    expect(wb.total).toBe(6);
    // 实测：2 个不一致
    expect(wb.disagreementCount).toBe(2);

    const bci = all.find((x) => x.candidateId === 'CC-2026-BCI-MEDTECH')!;
    expect(bci.phase).toBe('UNKNOWN'); // ★ 推导值（权威）
    expect(bci.declaredPhase).toBe('THEME_FORMING'); // ★ 声明值**并列保留**
    expect(bci.agreesWithDeclared).toBe(false);
    expect(bci.matchedRule).toBe('R8_UNCLASSIFIED');

    const auto = all.find((x) => x.candidateId === 'CC-2026-AUTO-SMARTDRIVE')!;
    expect(auto.phase).toBe('UNKNOWN');
    expect(auto.declaredPhase).toBe('THEME_FORMING');
    expect(auto.agreesWithDeclared).toBe(false);
  });

  it('★ 阶段来自规则引擎（命中规则 id 可审计），不是直接抄声明', () => {
    const all = buildWatchboard().groups.flatMap((g) => g.items);
    for (const it of all) {
      expect(it.matchedRule).toMatch(/^R\d+_/);
      expect(it.ruleLabel.length).toBeGreaterThan(0);
      expect(Array.isArray(it.reasons)).toBe(true);
    }
    // 四个一致的对象的推导值应与声明一致
    for (const id of ['CC-2026-OFFSHORE-WIND', 'CC-2026-COMPUTE-POWER', 'CC-2026-EMBODIED-AI', 'CC-2026-OPTICAL-LINK']) {
      const it = all.find((x) => x.candidateId === id)!;
      expect(it.agreesWithDeclared, id).toBe(true);
      expect(it.phase, id).toBe(it.declaredPhase);
    }
  });

  it('★★ 「还缺哪些维度」来自**引擎**（八维矩阵），不是本模块自算', () => {
    const all = buildWatchboard().groups.flatMap((g) => g.items);
    const optic = all.find((x) => x.candidateId === 'CC-2026-OPTICAL-LINK')!;
    expect(optic.coverage.known).toBe(8);
    expect(optic.missingDimensions).toEqual([]);

    const bci = all.find((x) => x.candidateId === 'CC-2026-BCI-MEDTECH')!;
    expect(bci.missingDimensions).toContain('资金响应');
    expect(bci.missingDimensions).toContain('扩散广度');
    expect(bci.coverage.known).toBe(7);
    expect(bci.coverage.total).toBe(8);
  });

  it('★ 组序 = 生命周期自然序；组内按**阶段起点时间序**', () => {
    const ORDER = ['EARLY_SIGNAL', 'THEME_FORMING', 'BROAD_CONFIRMATION', 'EXPANSION', 'PEAK', 'DECLINE', 'END', 'UNKNOWN'];
    const wb = buildWatchboard();
    const idx = wb.groups.map((g) => ORDER.indexOf(g.phase));
    for (let i = 1; i < idx.length; i += 1) expect(idx[i]).toBeGreaterThan(idx[i - 1]);
    for (const g of wb.groups) {
      const dated = g.items.filter((x) => x.phaseStart).map((x) => x.phaseStart as string);
      for (let i = 1; i < dated.length; i += 1) expect(dated[i] >= dated[i - 1]).toBe(true);
    }
  });

  it('★ 分组依据是**推导阶段**，不是声明阶段（否则 2 个 UNKNOWN 会被并进「主题形成」）', () => {
    const wb = buildWatchboard();
    const forming = wb.groups.find((g) => g.phase === 'THEME_FORMING');
    const ids = (forming?.items ?? []).map((x) => x.candidateId);
    expect(ids).toEqual(['CC-2026-OFFSHORE-WIND']); // 只有它推导为 THEME_FORMING
    expect(ids).not.toContain('CC-2026-BCI-MEDTECH');
    expect(ids).not.toContain('CC-2026-AUTO-SMARTDRIVE');
  });

  it('★ 语义边界：视图模型**不含**任何 score / 概率 / 排名字段', () => {
    const wb = buildWatchboard();
    const keys = [
      ...Object.keys(wb),
      ...Object.keys(wb.groups[0]),
      ...Object.keys(wb.groups[0].items[0]),
    ].map((x) => x.toLowerCase());
    for (const banned of ['score', 'rating', 'rank', 'probability', 'prediction', 'weight']) {
      expect(keys.some((x) => x.includes(banned))).toBe(false);
    }
  });

  it('★★ 声明必须写明「并列不取一」与既定的否定式措辞', () => {
    expect(WATCHBOARD_DISCLAIMER).toContain('并列');
    expect(WATCHBOARD_DISCLAIMER).toContain('不等于');
    expect(WATCHBOARD_DISCLAIMER).toContain('不评分、不排名');
    expect(WATCHBOARD_DISCLAIMER).toContain('非预测');
  });
});

describe('CurrentWatchboardSection · 渲染', () => {
  it('★ 不一致的对象在界面上**并列显示**推导值与研究声明', () => {
    const html = renderToStaticMarkup(<CurrentWatchboardSection />);
    expect(html).toContain('推导阶段（权威）');
    expect(html).toContain('研究声明为「主题形成」');
    expect(html).toContain('两者并列，不静默取一');
    expect(html).toContain('命中规则 R8_UNCLASSIFIED');
  });

  it('渲染分组、「还缺哪些维度」与语义声明', () => {
    const html = renderToStaticMarkup(<CurrentWatchboardSection />);
    expect(html).toContain('当前观察台');
    expect(html).toContain('还缺哪些维度');
    expect(html).toContain('脑机接口医疗器械');
    expect(html).toContain('不等于');
    expect(html).toContain('不评分、不排名');
    expect(html).toContain('非预测');
    expect(html).not.toContain('**'); // 不得残留会字面显示的 Markdown 标记
  });

  it('提供「看研究问题」入口（只做导航，不做判定）', () => {
    const html = renderToStaticMarkup(<CurrentWatchboardSection onOpenCandidate={() => {}} />);
    expect(html).toContain('看研究问题');
  });
});
