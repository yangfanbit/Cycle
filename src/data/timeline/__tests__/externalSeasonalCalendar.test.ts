/**
 * 外部季节性题材日历 —— 验收测试。
 *
 * 覆盖用户 2026-10-13 指定的 8 项验收要求：
 *  ① 清单包含全部 25 项
 *  ② 跨年月份窗口正确解析
 *  ③ 月份精度不会变成伪造的日级精度
 *  ④ 外部线索与 ThreeC 历史结论保持独立
 *  ⑤ 无映射线索可以正常展示
 *  ⑥ 窗口活跃不自动提升研究成熟度
 *  ⑦ 来源和版本信息可追溯
 *  ⑧ JSON 格式错误 / 缺少必填字段 / 非法状态可被检查发现
 */
import { describe, expect, it } from 'vitest';
import {
  EXTERNAL_CALENDAR_NOTE,
  EXTERNAL_SOURCE_LABEL,
  MATURITY_LABEL,
  RELATION_LABEL,
  entriesByMonth,
  externalCalendarDoc,
  externalCalendarEntries,
  externalSourceById,
  validateCalendar,
  windowRelationOf,
  windowRelationOfWindow,
  windowTextOf,
  type ExternalCalendarDoc,
  type ExternalCalendarEntry,
} from '../externalSeasonalCalendar';

const TODAY = '2026-10-13'; // 本轮基准日（用户指定）
const entries = externalCalendarEntries();

/* ------------------------------------------------------------ ① 25 项 */

describe('① 清单完整性', () => {
  it('包含全部 25 项外部线索', () => {
    expect(entries).toHaveLength(25);
  });

  it('ID 唯一且稳定（EXT-01 … EXT-25）', () => {
    const ids = entries.map((e) => e.id);
    expect(new Set(ids).size).toBe(25);
    expect(ids).toContain('EXT-01');
    expect(ids).toContain('EXT-25');
  });

  it('每项都有名称与类别', () => {
    for (const e of entries) {
      expect(e.name.length, e.id).toBeGreaterThan(0);
      expect(e.category.length, e.id).toBeGreaterThan(0);
    }
  });
});

/* ------------------------------------------------------ ② 跨年窗口 */

describe('② 跨年月份窗口解析', () => {
  const crossYear = entries.filter((e) => (e.windows ?? []).some((w) => w.cross_year));
  it('存在跨年窗口条目（12→2 / 10→3 / 9→1 / 11→1）', () => {
    expect(crossYear.length).toBeGreaterThanOrEqual(4);
  });

  it('★ 12 月至次年 2 月：12 月 / 1 月 / 2 月都在窗口内', () => {
    const w = { start_month: 12, end_month: 2, cross_year: true, raw_text: '12 月至次年 2 月' };
    expect(windowRelationOfWindow(w, '2026-12-05')).toBe('IN_WINDOW');
    expect(windowRelationOfWindow(w, '2027-01-20')).toBe('IN_WINDOW');
    expect(windowRelationOfWindow(w, '2027-02-28')).toBe('IN_WINDOW');
    // 边界外
    expect(windowRelationOfWindow(w, '2026-11-30')).toBe('UPCOMING');
    expect(windowRelationOfWindow(w, '2027-03-01')).toBe('PASSED');
  });

  it('★ 10 月至次年 3 月（冰雪经济）：跨年两侧都在窗口内', () => {
    const w = { start_month: 10, end_month: 3, cross_year: true, raw_text: '10 月至次年 3 月' };
    expect(windowRelationOfWindow(w, '2026-10-13')).toBe('IN_WINDOW');
    expect(windowRelationOfWindow(w, '2027-01-15')).toBe('IN_WINDOW');
    expect(windowRelationOfWindow(w, '2027-03-31')).toBe('IN_WINDOW');
    expect(windowRelationOfWindow(w, '2026-09-01')).toBe('UPCOMING');
    expect(windowRelationOfWindow(w, '2027-04-01')).toBe('PASSED');
  });

  it('★ 非跨年窗口不误判', () => {
    const w = { start_month: 5, end_month: 7, cross_year: false, raw_text: '5–7 月' };
    expect(windowRelationOfWindow(w, '2026-06-01')).toBe('IN_WINDOW');
    expect(windowRelationOfWindow(w, '2026-04-01')).toBe('UPCOMING');
    expect(windowRelationOfWindow(w, '2026-08-01')).toBe('PASSED');
  });

  it('★ 多段窗口取最"近"的关系（EXT-21 环保：3 月；11 月至次年 1 月）', () => {
    const env = entries.find((e) => e.id === 'EXT-21')!;
    expect(env.windows).toHaveLength(2);
    // 10 月 → 第二段（11 月起）即将进入；第一段（3 月）已过 → 取 UPCOMING
    expect(windowRelationOf(env, '2026-10-13')).toBe('UPCOMING');
    // 12 月 → 落在第二段内
    expect(windowRelationOf(env, '2026-12-01')).toBe('IN_WINDOW');
    // 3 月 → 落在第一段内
    expect(windowRelationOf(env, '2027-03-10')).toBe('IN_WINDOW');
  });
});

/* ------------------------------------------------ ③ 月份精度不伪造 */

describe('③ 精度：月份级不得变成日级', () => {
  it('有窗口的条目精度一律为 MONTH，且窗口只有月份字段', () => {
    for (const e of entries) {
      if ((e.windows ?? []).length === 0) {
        expect(e.precision, e.id).toBe('NONE');
        continue;
      }
      expect(e.precision, e.id).toBe('MONTH');
      for (const w of e.windows) {
        expect(Object.keys(w).sort(), e.id).toEqual(
          ['cross_year', 'end_month', 'raw_text', 'start_month'].sort(),
        );
        // ★ 不得出现 day / date 之类字段
        expect(JSON.stringify(w)).not.toMatch(/"day"|"date"|"start_date"|"end_date"/);
      }
    }
  });

  it('★ 原始窗口文本保留（不被规范化成具体日期）', () => {
    for (const e of entries) {
      for (const w of e.windows ?? []) {
        expect(w.raw_text.length, e.id).toBeGreaterThan(0);
        expect(w.raw_text, `${e.id} 的 raw_text 不应含具体日`).not.toMatch(/\d{4}-\d{2}-\d{2}/);
      }
    }
  });

  it('窗口文本展示保留原始口径', () => {
    const ice = entries.find((e) => e.id === 'EXT-11')!;
    expect(windowTextOf(ice)).toBe('10 月至次年 3 月');
    const noWin = entries.find((e) => e.id === 'EXT-23')!;
    expect(windowTextOf(noWin)).toContain('无固定窗口');
  });
});

/* -------------------------------------------- ④ 外部与历史保持独立 */

describe('④ 外部线索与 ThreeC 历史结论的独立性', () => {
  it('★ 本模块显式声明来源属性（防止与历史结论混淆）', () => {
    expect(EXTERNAL_SOURCE_LABEL).toContain('外部');
    expect(EXTERNAL_SOURCE_LABEL).toContain('未由 ThreeC 验证');
    expect(EXTERNAL_CALENDAR_NOTE).toContain('不是');
    expect(EXTERNAL_CALENDAR_NOTE).toContain('外部资料');
  });

  it('★★ v0_2：25 项逐项核验，**没有**一项达到 THREEC_VALIDATED', () => {
    // ★ 旧断言是「全部 EXTERNAL_REFERENCE」——那是**旧行为快照**（v0_1 只导入未核验）。
    //   v0_2 的不变量是：每项都有核验结论，且**没有**任何一项被标成「ThreeC 已验证」。
    for (const e of entries) {
      expect(e.verification, `${e.id} 缺少逐项核验结论`).toBeTruthy();
      expect(e.verification!.disposition, e.id).toBe(e.maturity);
      expect(e.maturity, `${e.id} 不得未经正式研究就标 THREEC_VALIDATED`)
        .not.toBe('THREEC_VALIDATED');
      expect(e.verification!.reason.length, e.id).toBeGreaterThan(20);
      expect(e.verification!.next_step.text.length, e.id).toBeGreaterThan(10);
      expect(e.verification!.source_check.report_available, `${e.id} 不得声称读过原报告`).toBe(false);
    }
  });

  it('★ 本模块不引入分数 / 排名 / 概率 / 置信度字段', () => {
    const raw = JSON.stringify(externalCalendarDoc());
    for (const banned of ['"score"', '"rank"', '"probability"', '"confidence"', '"signal"']) {
      expect(raw, `不应出现 ${banned}`).not.toContain(banned);
    }
  });

  it('★ 映射只指向现有 Macro Theme 名，且不新增 canonical 对象', () => {
    // 允许的 13 个根主题（与 DB themes 的 parent_theme_id IS NULL 一致）
    const ROOTS = new Set([
      '消费', '资源', '电子', '汽车', '高端装备', '金融', '医药健康',
      '信息通信', '国防军工', '房地产', '文化传媒', '电力设备', '电力（运营端）',
    ]);
    for (const e of entries) {
      if (e.mapping.status === 'MAPPED') {
        expect(ROOTS.has(e.mapping.macro_theme!), `${e.id} 映射到未知根主题`).toBe(true);
      }
    }
    // ★ v0_2：`verification.threec_evidence.mechanism_matched` 会**引用**库内既有 campaign id
    //   —— 那是**引用证据**，不是新建对象。不变量改为：不出现 canonical 表结构 / 新建对象定义。
    const doc = externalCalendarDoc();
    expect(Object.keys(doc)).not.toContain('campaigns');
    expect(Object.keys(doc)).not.toContain('themes');
    const raw = JSON.stringify(doc);
    expect(raw).not.toMatch(/"TH-[A-Z]/);           // 不写 theme_id
    // 引用到的 campaign 必须是**库内既有**（以 C- 开头且带年份），且只出现在证据字段里
    const refs = entries.flatMap((e) => e.verification?.threec_evidence.mechanism_matched_campaigns ?? []);
    for (const cid of refs) expect(cid).toMatch(/^C-\d{4}-/);   // 只引用库内既有 Campaign
  });

  it('★ 未创建虚假 canonical：UNMAPPED 条目不指向任何主题', () => {
    for (const e of entries.filter((x) => x.mapping.status === 'UNMAPPED')) {
      expect(e.mapping.macro_theme, e.id).toBeNull();
      expect(e.mapping.reason, e.id).toBeTruthy();
    }
  });
});

/* -------------------------------------------------- ⑤ 无映射可展示 */

describe('⑤ 无映射线索可正常展示', () => {
  const unmapped = entries.filter((e) => e.mapping.status === 'UNMAPPED');

  it('存在 UNMAPPED 条目，且都能取到名称 / 窗口 / 来源', () => {
    expect(unmapped.length).toBeGreaterThan(0);
    for (const e of unmapped) {
      expect(e.name.length, e.id).toBeGreaterThan(0);
      expect(windowTextOf(e).length, e.id).toBeGreaterThan(0);
      expect(e.source_ids.length, e.id).toBeGreaterThan(0);
      expect(e.mapping.reason, e.id).toBeTruthy();
    }
  });

  it('★ 无映射不隐藏、不自动补结论（reason 必须写明）', () => {
    for (const e of unmapped) {
      expect(e.mapping.reason!.length, e.id).toBeGreaterThan(10);
    }
  });

  it('★ 无固定窗口 / 日期不足的条目有明确状态（不伪造窗口）', () => {
    const noFixed = entries.filter((e) => e.window_relation_override === 'NO_FIXED_WINDOW');
    const insufficient = entries.filter((e) => e.window_relation_override === 'INSUFFICIENT_DATE');
    expect(noFixed.length).toBeGreaterThan(0);
    expect(insufficient.length).toBeGreaterThan(0);
    for (const e of [...noFixed, ...insufficient]) {
      expect(e.windows, e.id).toHaveLength(0);
      expect(windowRelationOf(e, TODAY), e.id).toBe(e.window_relation_override);
    }
  });
});

/* ---------------------------------------- ⑥ 窗口活跃 ≠ 成熟度提升 */

describe('⑥ 窗口活跃不自动提升研究成熟度', () => {
  it('★★ 窗口活跃**不**改变成熟度：窗口内条目的 maturity === 核验结论', () => {
    const inWindow = entries.filter((e) => windowRelationOf(e, TODAY) === 'IN_WINDOW');
    expect(inWindow.length).toBeGreaterThan(0);
    for (const e of inWindow) {
      // 成熟度只由**核验结论**决定，与「今天是否在窗口内」无关
      expect(e.maturity, `${e.id} 窗口内但成熟度与核验结论不符`)
        .toBe(e.verification!.disposition);
    }
  });

  it('★ 成熟度与窗口关系是**两个独立字段**（不合并）', () => {
    // 同一条目可同时「窗口内」且**未验证**（OBSERVING）—— 证明两者解耦
    const e = entries.find((x) => x.id === 'EXT-08')!; // 双十一 10–11 月
    expect(windowRelationOf(e, TODAY)).toBe('IN_WINDOW');
    expect(e.maturity).toBe('OBSERVING');
    expect(MATURITY_LABEL[e.maturity]).toBe('观察中');
    expect(RELATION_LABEL.IN_WINDOW).toBe('窗口内');
  });

  it('★ 用户指定的四项优先展示，在基准日的关系可计算', () => {
    const want = ['EXT-11', 'EXT-08', 'EXT-12', 'EXT-09']; // 冰雪/双十一/流感/供暖
    for (const id of want) {
      const e = entries.find((x) => x.id === id)!;
      const rel = windowRelationOf(e, TODAY);
      expect(['IN_WINDOW', 'UPCOMING'], `${id} 应为窗口内或即将进入`).toContain(rel);
    }
  });
});

/* -------------------------------------------- ⑦ 来源与版本可追溯 */

describe('⑦ 来源与版本可追溯', () => {
  it('文档带 artifact 名与版本', () => {
    const doc = externalCalendarDoc();
    expect(doc.artifact).toBe('external_seasonal_calendar');
    expect(doc.artifact_version).toBe('0.2');
    expect(doc.generated_at).toBeTruthy();
  });

  it('★ 每条都引用**存在**的来源（可追溯）', () => {
    for (const e of entries) {
      expect(e.source_ids.length, e.id).toBeGreaterThan(0);
      for (const sid of e.source_ids) {
        expect(externalSourceById(sid), `${e.id} 引用了不存在的来源 ${sid}`).toBeDefined();
      }
    }
  });

  it('★ 每条都有变更记录（追加式）', () => {
    for (const e of entries) {
      expect(e.revision.length, e.id).toBeGreaterThan(0);
      expect(e.revision[0].date, e.id).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it('★ 原始资料未找到一事被显式记录（不假装有原文）', () => {
    const doc = externalCalendarDoc();
    for (const s of doc.source_reports) {
      expect(s.note, s.source_id).toContain('未');
    }
  });
});

/* ---------------------------------------------------- ⑧ 校验可发现 */

describe('⑧ 非法数据可被检查发现', () => {
  const good = externalCalendarDoc();

  it('当前文件通过校验（基线）', () => {
    expect(validateCalendar(good)).toEqual([]);
  });

  const clone = (): ExternalCalendarDoc => JSON.parse(JSON.stringify(good));

  it('缺少 id / name / category 被发现', () => {
    const d = clone();
    delete (d.entries[0] as Partial<ExternalCalendarEntry>).id;
    delete (d.entries[0] as Partial<ExternalCalendarEntry>).name;
    const issues = validateCalendar(d);
    expect(issues.some((i) => i.field === 'id')).toBe(true);
    expect(issues.some((i) => i.field === 'name')).toBe(true);
  });

  it('id 重复被发现', () => {
    const d = clone();
    d.entries[1].id = d.entries[0].id;
    expect(validateCalendar(d).some((i) => /id 重复/.test(i.message))).toBe(true);
  });

  it('月份越界被发现', () => {
    const d = clone();
    d.entries[0].windows = [{ start_month: 0, end_month: 13, cross_year: false, raw_text: 'x' }];
    const issues = validateCalendar(d);
    expect(issues.some((i) => i.field === 'windows.start_month')).toBe(true);
    expect(issues.some((i) => i.field === 'windows.end_month')).toBe(true);
  });

  it('★ 跨年标注与月份关系不一致被发现', () => {
    const d = clone();
    d.entries[0].windows = [{ start_month: 12, end_month: 2, cross_year: false, raw_text: 'x' }];
    expect(validateCalendar(d).some((i) => i.field === 'windows.cross_year')).toBe(true);
  });

  it('非法成熟度被发现', () => {
    const d = clone();
    (d.entries[0] as { maturity: string }).maturity = 'SOMETHING_ELSE';
    expect(validateCalendar(d).some((i) => i.field === 'maturity')).toBe(true);
  });

  it('★ MAPPED 无依据 / UNMAPPED 无原因 被发现', () => {
    const d = clone();
    const mapped = d.entries.find((e) => e.mapping.status === 'MAPPED')!;
    mapped.mapping.basis = null;
    const unmapped = d.entries.find((e) => e.mapping.status === 'UNMAPPED')!;
    unmapped.mapping.reason = null;
    const issues = validateCalendar(d);
    expect(issues.some((i) => i.field === 'mapping.basis')).toBe(true);
    expect(issues.some((i) => i.field === 'mapping.reason')).toBe(true);
  });

  it('缺来源被发现', () => {
    const d = clone();
    d.entries[0].source_ids = [];
    expect(validateCalendar(d).some((i) => i.field === 'source_ids')).toBe(true);
  });

  it('缺变更记录被发现', () => {
    const d = clone();
    d.entries[0].revision = [];
    expect(validateCalendar(d).some((i) => i.field === 'revision')).toBe(true);
  });

  it('entries 为空被发现', () => {
    const d = clone();
    d.entries = [];
    expect(validateCalendar(d).some((i) => i.field === 'entries')).toBe(true);
  });
});

/* --------------------------------------------------------- 附加：索引 */

describe('附加：月份索引', () => {
  it('12 个月都有索引项，且跨年条目不漏月', () => {
    const map = entriesByMonth(entries);
    expect(map.size).toBe(12);
    // 冰雪经济（10→3）应出现在 10/11/12/1/2/3 六个月
    const ice = entries.find((e) => e.id === 'EXT-11')!;
    for (const m of [10, 11, 12, 1, 2, 3]) {
      expect(map.get(m)!, `第 ${m} 月应含冰雪经济`).toContain(ice);
    }
    for (const m of [4, 5, 6, 7, 8, 9]) {
      expect(map.get(m)!, `第 ${m} 月不应含冰雪经济`).not.toContain(ice);
    }
  });
});
