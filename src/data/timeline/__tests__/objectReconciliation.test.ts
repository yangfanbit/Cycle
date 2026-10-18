/**
 * ★★ v0.17：题材地图 × Research 对象 —— **标的对账**。
 *
 * 三分类必须可区分（直接匹配 / 地图补充 / 无法核对），且**精确匹配、不猜身份**。
 */
import { describe, it, expect } from 'vitest';

import { eventMapByTheme, type HistoricalEvent, type HistoricalEventsDoc } from '../historicalEventMaps';
import {
  RECON_LINK_LABEL,
  eventReconciliation,
  isExportObject,
  isRegisteredSecurity,
  objectSecurityIds,
  reconciliationOf,
  themeReconciliation,
} from '../objectReconciliation';

const semi = eventMapByTheme('SEMICONDUCTOR_AI')!.doc;
const flu = eventMapByTheme('FLU')!.doc;

function ev(doc: HistoricalEventsDoc, id: string): HistoricalEvent {
  const e = doc.events.find((x) => x.event_id === id);
  if (!e) throw new Error('未找到事件 ' + id);
  return e;
}

describe('A. ★ 对象 / 证券索引来自 canonical export（只读派生）', () => {
  it('★ isExportObject / objectSecurityIds / isRegisteredSecurity', () => {
    expect(isExportObject('C-2023-AI-COMPUTE-SEMI')).toBe(true);
    expect(isExportObject('RC-2024-SEMI-FUND3')).toBe(true);
    expect(isExportObject('NOT-A-REAL-OBJECT')).toBe(false);
    expect(objectSecurityIds('C-2023-AI-COMPUTE-SEMI')!.has('CAMBRICON')).toBe(true);
    expect(objectSecurityIds('NOT-A-REAL-OBJECT')).toBeNull();
    expect(isRegisteredSecurity('CAMBRICON')).toBe(true);
    expect(isRegisteredSecurity('NOT-A-REAL-SECURITY')).toBe(false);
  });

  it('★ Research Candidate 身份可辨识（RC-2024-SEMI-FUND3 为候选，非 Campaign）', () => {
    expect(objectSecurityIds('RC-2024-SEMI-FUND3')!.has('AMEC')).toBe(true);
  });
});

describe('B. ★★ 三分类必须可区分', () => {
  it('★★ 直接匹配：半导体 2023 AI 算力事件的登记标的全部 OBJECT_REGISTERED', () => {
    const e = ev(semi, 'SEMI-2023-AI-COMPUTE');
    const r = eventReconciliation(e);
    expect(r.objectId).toBe('C-2023-AI-COMPUTE-SEMI');
    expect(r.objectKind).toBe('campaign');
    expect(r.objectFound).toBe(true);
    expect(r.counts.OBJECT_REGISTERED).toBe(e.participants.length);
    expect(r.counts.MAP_SUPPLEMENT).toBe(0);
    expect(r.counts.UNRESOLVED).toBe(0);
  });

  it('★★ 地图补充：证券在全局注册表、但不在该对象 security_ids 中 → MAP_SUPPLEMENT', () => {
    const e = ev(semi, 'SEMI-2023-AI-COMPUTE');
    const r = reconciliationOf(e, 'HUALANVAX');   // 注册表在册，非半导体的关联对象所有
    expect(isRegisteredSecurity('HUALANVAX')).toBe(true);
    expect(objectSecurityIds('C-2023-AI-COMPUTE-SEMI')!.has('HUALANVAX')).toBe(false);
    expect(r.link).toBe('MAP_SUPPLEMENT');
    expect(r.reason).toContain('地图补充');
  });

  it('★★ FLU-2023-H1N1 已补齐对象关联（v0_7）→ 三只标的全部 OBJECT_REGISTERED', () => {
    const e = ev(flu, 'FLU-2023-H1N1');
    const r = eventReconciliation(e);
    expect(r.objectId).toBe('C-2023-PHARMA-FLU');   // evidence_basis 明确引用
    expect(r.objectKind).toBe('campaign');
    expect(r.objectFound).toBe(true);
    expect(r.counts.OBJECT_REGISTERED).toBe(e.participants.length);   // 3
    expect(r.counts.NO_OBJECT_REFERENCE).toBe(0);
    expect(r.counts.UNRESOLVED).toBe(0);
  });

  it('★★ 未登记对象关联：FLU-2017-AVIAN 未记录关联对象 → NO_OBJECT_REFERENCE（不暗示证券不存在）', () => {
    const e = ev(flu, 'FLU-2017-AVIAN');
    const r = eventReconciliation(e);
    expect(r.objectId).toBeNull();
    expect(r.objectFound).toBe(false);
    expect(r.counts.NO_OBJECT_REFERENCE).toBe(e.participants.length);
    expect(r.counts.UNRESOLVED).toBe(0);            // ★ 不是「对象解析失败」
    const one = reconciliationOf(e, e.participants[0].security_id);
    expect(one.link).toBe('NO_OBJECT_REFERENCE');
    expect(one.reason).toContain('未记录关联对象');
    expect(one.reason).toContain('无法做对象级对账');
  });

  it('★★ 真 UNRESOLVED：已提供对象引用但对象无法解析 → 与 NO_OBJECT_REFERENCE 区分', () => {
    const e = ev(flu, 'FLU-2017-AVIAN');
    const withBadRef = {
      ...e,
      campaign_facts: { object_id: 'NOT-A-REAL-OBJECT', start: null, peak_date: null, end: null },
    };
    const r = eventReconciliation(withBadRef);
    expect(r.objectId).toBe('NOT-A-REAL-OBJECT');
    expect(r.objectFound).toBe(false);
    expect(r.counts.UNRESOLVED).toBe(e.participants.length);
    expect(r.counts.NO_OBJECT_REFERENCE).toBe(0);   // ★ 有引用 → 不算「未登记」
    expect(reconciliationOf(withBadRef, e.participants[0].security_id).link).toBe('UNRESOLVED');
  });

  it('★ 四分类文案互不相同', () => {
    const labels = Object.values(RECON_LINK_LABEL);
    expect(new Set(labels).size).toBe(4);
    expect(RECON_LINK_LABEL.OBJECT_REGISTERED).toBe('对象已登记关联');
    expect(RECON_LINK_LABEL.MAP_SUPPLEMENT).toBe('地图补充记录');
    expect(RECON_LINK_LABEL.NO_OBJECT_REFERENCE).toBe('未登记对象关联');
    expect(RECON_LINK_LABEL.UNRESOLVED).toBe('无法核对');
  });
});

describe('C. ★★ 六题材对账汇总（真实数据锚点）', () => {
  const THEMES = ['FLU', 'POWER_SUMMER', 'MEDIA', 'ROBOTICS', 'AUTO_INTELLIGENCE', 'SEMICONDUCTOR_AI'];
  const totals = { OBJECT_REGISTERED: 0, MAP_SUPPLEMENT: 0, NO_OBJECT_REFERENCE: 0, UNRESOLVED: 0 };
  let records = 0;
  for (const t of THEMES) {
    const doc = eventMapByTheme(t)!.doc;
    const rec = themeReconciliation(doc);
    const n = doc.events.reduce((s, e) => s + (e.participants?.length ?? 0), 0);
    it(`★ ${t}：四分类之和 = 参与记录数（${n}）`, () => {
      expect(rec.OBJECT_REGISTERED + rec.MAP_SUPPLEMENT
        + rec.NO_OBJECT_REFERENCE + rec.UNRESOLVED).toBe(n);
    });
    totals.OBJECT_REGISTERED += rec.OBJECT_REGISTERED;
    totals.MAP_SUPPLEMENT += rec.MAP_SUPPLEMENT;
    totals.NO_OBJECT_REFERENCE += rec.NO_OBJECT_REFERENCE;
    totals.UNRESOLVED += rec.UNRESOLVED;
    records += n;
  }

  it('★★ 全局锚点：记录 123 条 · 已登记 66 · 地图补充 0 · 未登记对象关联 57 · 无法核对 0', () => {
    expect(records).toBe(123);
    expect(totals).toEqual({
      OBJECT_REGISTERED: 66, MAP_SUPPLEMENT: 0, NO_OBJECT_REFERENCE: 57, UNRESOLVED: 0,
    });
  });
});
