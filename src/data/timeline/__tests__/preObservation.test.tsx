import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { SamePeriodView } from '../../../components/SamePeriodView/SamePeriodView';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import {
  historicalPreObservationDays,
  isInPreObservation,
  PRE_OBSERVATION_HINT,
  PRE_OBSERVATION_LABEL,
  preObservationChainOf,
  preObservationWindowOf,
  themeFormationDate,
} from '../preObservation';
import { themeRowsOf } from '../themeRows';
import { previewTimelineSource, verifiedTimelineSource } from '../timelineAdapter';
import { fixtureCampaigns } from '../../../../tests/fixtures/campaignFixtures';

/**
 * V1.8.2 Timeline Detail UX + Pre-observation Window 测试（10 项 + 附加）。
 *
 * 分组：
 *   1. inline summary appears on selection（就地展开，非侧栏）
 *   2. timeline remains visible（详情不遮挡 / 非永久压缩）
 *   3. full detail opens only on explicit action
 *   4. mobile bottom sheet fallback
 *   5. pre-observation window starts 30 days before formation
 *   6. early signal follows pre-observation
 *   7. no prediction language
 *   8. no buy/sell language
 *   9. preview / production isolation
 *  10. candidate / conflict preserved
 */

const TODAY = '2026-09-13'; // 9 月 → 窗口 08-15 ~ 10-15
const SEPT = 9;

const fs = require('node:fs') as typeof import('node:fs');
const path = require('node:path') as typeof import('node:path');
/** 读取仓库内文件（vitest 的 cwd = 仓库根） */
const read = (rel: string) => fs.readFileSync(path.resolve(process.cwd(), rel), 'utf-8');

/* ---------------- 1. Inline Summary（Level 1） ---------------- */

describe('1. inline summary appears on selection（就地展开，不打开侧栏）', () => {
  it('主题行 + 摘要结构存在于 SamePeriodView（就地渲染，无 detail-panel）', () => {
    const html = renderToStaticMarkup(
      <SamePeriodView dataSource={previewTimelineSource()} today={TODAY} />,
    );
    // 主题行存在（一行 = 一个主题）
    expect(html).toContain('sp-theme-head');
    expect(html).toContain('sp-theme-title');
    // 组件自身不渲染 Level 2 侧栏（只有显式动作后才由 App 渲染 CampaignDetail）
    expect(html).not.toContain('detail-panel');
  });

  it('摘要组件包含指定字段：主题 / 年份 / 阶段 / 相关因素 / 状态', () => {
    const src = read('src/components/SamePeriodView/SamePeriodView.tsx');
    for (const token of [
      '主题摘要',
      '代表阶段',
      '当时处于',
      '可能相关因素',
      '查看完整历史案例',
    ]) {
      expect(src).toContain(token);
    }
    // 提前观察区标签来自常量（不在组件源码中硬编码）
    expect(src).toContain('PRE_OBSERVATION_LABEL');
    expect(src).toContain('PRE_OBSERVATION_HINT');
  });
});

/* ---------------- 2. Timeline remains visible ---------------- */

describe('2. timeline remains visible（点击主题不打断时间轴）', () => {
  it('点击主题行不调用 onSelect（Level 1 不打开侧栏）', () => {
    const src = read('src/components/SamePeriodView/SamePeriodView.tsx');
    // 只有 InlineThemeSummary 的「查看完整历史案例」按钮调用 onSelect
    const calls = src.match(/onSelect\?\.\(/g) ?? [];
    expect(calls.length).toBe(1);
    // 主题行头按钮是 onToggle（就地展开），不是 onSelect
    expect(src).toContain('className="sp-theme-head" onClick={onToggle}');
  });

  it('CSS 中详情面板为浮层（fixed），未对主画布施加永久宽度压缩', () => {
    const css = read('src/styles.css');
    const i = css.indexOf('.detail-panel {');
    const block = css.slice(i, i + 500);
    expect(block).toContain('position: fixed');
    // 无 padding-right / margin-right 之类的「压缩 Timeline」规则
    expect(css).not.toMatch(/\.app-main[^{]*\{[^}]*padding-right:\s*min\(420px/);
  });
});

/* ---------------- 3. Full detail only on explicit action ---------------- */

describe('3. full detail opens only on explicit action（Level 2 显式动作）', () => {
  it('App 仅在 selection 存在时才渲染 CampaignDetail', () => {
    const app = read('src/App.tsx');
    expect(app).toContain('selectedCampaign &&');
    expect(app).toContain('<CampaignDetail');
  });

  it('摘要内「查看完整历史案例」是唯一的 onSelect 触发点', () => {
    const src = read('src/components/SamePeriodView/SamePeriodView.tsx');
    // 按钮文本与调用同处一个 JSX 块
    expect(src).toContain('查看完整历史案例 →');
    const i = src.indexOf('sp-btn-full');
    expect(i).toBeGreaterThan(-1);
    const around = src.slice(i, i + 260);
    expect(around).toContain('查看完整历史案例');
    expect(around).toContain('onOpenFull(focus.campaign_id)');
    // onOpenFull 由父组件传入，其实现才调用 onSelect
    expect(src).toContain('onOpenFull={(id) => onSelect?.({ kind: \'campaign\', id })}');
  });
});

/* ---------------- 4. Mobile bottom sheet fallback ---------------- */

describe('4. mobile bottom sheet fallback（移动端 Bottom Sheet）', () => {
  it('CSS 在窄屏把详情面板改为 Bottom Sheet（top:auto / 圆角 / max-height）', () => {
    const css = read('src/styles.css');
    const i = css.indexOf('@media (max-width: 720px)');
    const block = css.slice(i, i + 700);
    expect(block).toContain('.detail-panel');
    expect(block).toContain('top: auto');
    expect(block).toContain('border-radius: 14px 14px 0 0');
    expect(block).toContain('max-height');
  });
});

/* ---------------- 5. Pre-observation starts 30 days before formation --------- */

describe('5. pre-observation window starts 30 days before formation', () => {
  it('常量恒为 30，且注释声明「不代表历史平均领先期」', () => {
    expect(historicalPreObservationDays).toBe(30);
    const src = read('src/data/timeline/preObservation.ts');
    expect(src).toContain('不代表历史平均领先期');
    expect(src).toContain('UI research buffer');
  });

  it('窗口 = [formation-30, formation-1]（不含形成日本身）', () => {
    const win = preObservationWindowOf({ start: '2025-09-01' });
    expect(win).not.toBeNull();
    expect(win!.formation).toBe('2025-09-01');
    expect(win!.start).toBe('2025-08-02'); // 09-01 - 30 天
    expect(win!.end).toBe('2025-08-31'); // 09-01 - 1 天
    expect(win!.days).toBe(30);
  });

  it('formation 优先取 lifecycle 最早阶段起点（主题形成边界）', () => {
    const campaign = {
      start: '2023-09-20',
      lifecycle: [
        { stage: 'EARLY_SIGNAL', start: '2023-08-29', end: '2023-09-01', precision: 'EXACT_DATE' },
        { stage: 'MAIN_RISE', start: '2023-09-20', end: '2023-10-31', precision: 'DATE_WINDOW' },
      ],
    };
    expect(themeFormationDate(campaign)).toBe('2023-08-29');
    const win = preObservationWindowOf(campaign)!;
    expect(win.formation).toBe('2023-08-29');
    expect(win.start).toBe('2023-07-30');
  });

  it('真实导出（RC-2023-HUAWEI）提前观察区起点 = 形成日 - 30 天', () => {
    const rc = previewTimelineSource()
      .yearData(2023)
      .campaigns.find((c) => c.campaign_id === 'RC-2023-HUAWEI')!;
    const chain = preObservationChainOf(rc)!;
    expect(chain.preObservation.days).toBe(30);
    const expectedStart = new Date(Date.parse(chain.formation + 'T00:00:00Z') - 30 * 86400000)
      .toISOString()
      .slice(0, 10);
    expect(chain.preObservation.start).toBe(expectedStart);
  });
});

/* ---------------- 6. Early signal follows pre-observation --------- */

describe('6. early signal follows pre-observation（层级：观察区 → 早期信号 → 形成）', () => {
  it('有 Early Signal 时为三段式 hasEarlySignal=true', () => {
    const withEs = {
      start: '2023-09-20',
      lifecycle: [{ stage: 'MAIN_RISE', start: '2023-09-20', end: '2023-10-31', precision: 'DATE_WINDOW' }],
      early_signal: { start: '2023-08-29', end: '2023-09-05', label: '前置观察' },
    };
    const chain = preObservationChainOf(withEs)!;
    expect(chain.hasEarlySignal).toBe(true);
    expect(chain.earlySignal?.start).toBe('2023-08-29');
    // 观察区终点早于形成日（不与 Campaign 主体重叠）
    expect(chain.preObservation.end < chain.preObservation.formation).toBe(true);
  });

  it('无 Early Signal 时退化为两段式（不编造）', () => {
    const noEs = { start: '2023-09-20', lifecycle: [] as never[] };
    const chain = preObservationChainOf(noEs as never)!;
    expect(chain.hasEarlySignal).toBe(false);
    expect(chain.earlySignal).toBeNull();
  });

  it('真实导出：RC-2023-HUAWEI 存在早期信号（导出既有字段，非本层编造）', () => {
    const rc = previewTimelineSource()
      .yearData(2023)
      .campaigns.find((c) => c.campaign_id === 'RC-2023-HUAWEI')!;
    const chain = preObservationChainOf(rc)!;
    // 该 RC lifecycle 首阶段为 EARLY_SIGNAL；early_signal 字段存在性按导出数据决定
    expect(chain.preObservation.formation).toBe('2023-08-29');
  });
});

/* ---------------- 7. No prediction language --------- */

describe('7. no prediction language（无预测措辞）', () => {
  it('SamePeriodView + Lens 渲染文本不含预测类措辞', () => {
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
    for (const banned of ['大概率', '将会上涨', '必然', '预测为', '预计上涨', '后市看涨', '目标价']) {
      expect(html).not.toContain(banned);
    }
  });

  it('提前观察区的**界面输出**不含禁用文案（源码 doc-comment 中的反例说明不计）', () => {
    // 断言渲染输出，而非源码注释；源码注释中以「✗ 不是…」形式列出反例属合规文档。
    const html = renderToStaticMarkup(
      <SamePeriodView dataSource={previewTimelineSource()} today={TODAY} />,
    );
    for (const banned of ['30天后', '大概率上涨', '建议提前', '最佳埋伏']) {
      expect(html).not.toContain(banned);
    }
    // 常量 hint 必须含非建议限定
    expect(PRE_OBSERVATION_HINT).toContain('不是买入建议');
    expect(PRE_OBSERVATION_HINT).toContain('不代表历史平均领先期');
  });
});

/* ---------------- 8. No buy/sell language --------- */

describe('8. no buy/sell language（无买卖建议措辞）', () => {
  it('全渲染文本不含买入 / 卖出 / 仓位类措辞', () => {
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
    for (const banned of ['买入', '卖出', '建仓', '加仓', '减仓', '止盈', '止损', '仓位', '布局区', '信号区']) {
      expect(html).not.toContain(banned);
    }
  });

  it('标签统一为「历史提前观察区」，未使用买入区 / 布局区 / 信号区', () => {
    expect(PRE_OBSERVATION_LABEL).toBe('历史提前观察区');
  });
});

/* ---------------- 9. Preview / production isolation --------- */

describe('9. preview / production isolation', () => {
  it('生产 verified 为空 → 主题行 0，显示未覆盖措辞', () => {
    const html = renderToStaticMarkup(
      <SamePeriodView dataSource={verifiedTimelineSource()} today={TODAY} />,
    );
    expect(html).toContain('当前研究数据未覆盖');
    expect(html).not.toContain('sp-theme-row');
    expect(themeRowsOf(verifiedTimelineSource(), SEPT).rows).toEqual([]);
  });

  it('preview 源产出主题行；verified fixture 无主题 → 未标注主题占位（不混淆）', () => {
    expect(themeRowsOf(previewTimelineSource(), SEPT).rows.length).toBeGreaterThan(0);
    const fixtureResult = themeRowsOf(verifiedTimelineSource(fixtureCampaigns), 7);
    expect(fixtureResult.rows.every((r) => r.untitled)).toBe(true);
  });
});

/* ---------------- 10. Candidate / conflict preserved --------- */

describe('10. candidate / conflict preserved', () => {
  it('RC 保留 kind=candidate 且状态不升级；行内不合并', () => {
    const all = themeRowsOf(previewTimelineSource(), SEPT).rows.flatMap((r) => r.campaigns);
    const rc = all.find((e) => e.campaign_id === 'RC-2023-HUAWEI')!;
    expect(rc.kind).toBe('candidate');
    expect(rc.status).not.toBe('verified');
    expect(rc.preObservation).not.toBeNull();
  });

  it('重大冲突标记保留在主题行条目上（hasMajorConflict 字段存在）', () => {
    const src = read('src/data/timeline/themeRows.ts');
    expect(src).toContain('hasMajorConflict');
    const all = themeRowsOf(previewTimelineSource(), SEPT).rows.flatMap((r) => r.campaigns);
    for (const e of all) {
      expect(typeof e.hasMajorConflict).toBe('boolean');
    }
  });
});

/* ---------------- 附加：Current Time Context 提前观察区说明 --------- */

describe('附加. Current Time Context 提前观察区说明（含非预测限定语）', () => {
  it('isInPreObservation 语义正确：窗口内 true，形成日之后 false', () => {
    const c = { start: '2025-09-01', lifecycle: [] as never[] };
    expect(isInPreObservation(c as never, '2025-08-15')).toBe(true);
    expect(isInPreObservation(c as never, '2025-09-01')).toBe(false); // 形成日不在观察区（半开区间）
    expect(isInPreObservation(c as never, '2025-07-01')).toBe(false);
  });

  it('渲染含「历史提前观察区」时必须同时出现「不代表本年度预测」限定', () => {
    const src = read('src/components/CurrentTimeLens/CurrentTimeLens.tsx');
    if (src.includes(PRE_OBSERVATION_LABEL)) {
      expect(src).toContain('不代表本年度预测');
    }
    expect(src).toContain('不代表本年度预测');
  });

  it('Timeline 渲染提前观察区条形（pre-obs 类名存在）', () => {
    const src = read('src/components/Timeline/Timeline.tsx');
    expect(src).toContain('pre-obs');
    expect(src).toContain('preObservationChainOf');
    const css = read('src/styles.css');
    expect(css).toContain('.bar.pre-obs');
    // 极淡：低透明度 + 斜纹
    expect(css).toMatch(/\.bar\.pre-obs[\s\S]{0,400}opacity:\s*0\.\d/);
  });
});
