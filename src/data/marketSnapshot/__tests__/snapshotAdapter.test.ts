import { describe, it, expect } from 'vitest';
import { CANONICAL, loadCurrentSnapshot, snapshotIndex } from '../snapshotAdapter';

/**
 * 适配器测试 —— 重点是**门禁**：
 * 默认只展示 CANONICAL；全部未签发时必须给出明确空态，而不是空白或悄悄放行。
 */

describe('snapshotAdapter · 索引与门禁', () => {
  it('索引能读到快照，且按日期升序', () => {
    const idx = snapshotIndex();
    expect(idx.length).toBeGreaterThanOrEqual(2);
    const dates = idx.map((e) => e.snapshot_date);
    expect([...dates].sort()).toEqual(dates);
    for (const e of idx) {
      expect(e.snapshot_id).toMatch(/^MS-/);
      expect(e.file).toMatch(/\.json$/);
    }
  });

  it('★ 默认门禁：全部快照未签发时，state = no-canonical（不得放行）', async () => {
    const idx = snapshotIndex();
    const hasCanonical = idx.some((e) => e.status === CANONICAL);
    const v = await loadCurrentSnapshot(false);
    if (!hasCanonical) {
      expect(v.state).toBe('no-canonical');
      expect(v.snapshot).toBeNull();
      expect(v.diff).toBeNull();
      expect(v.draftCount).toBe(idx.length);
      expect(v.latestDate).toBe(idx[idx.length - 1].snapshot_date);
    } else {
      expect(v.state).toBe('ok');
      expect(v.snapshot?.status).toBe(CANONICAL);
    }
  });

  it('★ 预览模式：放宽门禁可拿到最新快照，但必须标记 preview', async () => {
    const idx = snapshotIndex();
    const v = await loadCurrentSnapshot(true);
    expect(v.state).toBe('ok');
    expect(v.snapshot).not.toBeNull();
    expect(v.snapshot?.snapshot_id).toBe(idx[idx.length - 1].snapshot_id);
    const hasCanonical = idx[idx.length - 1].status === CANONICAL;
    expect(v.preview).toBe(!hasCanonical);
  });

  it('★ 「上一期」必须是更早的**不同日期**（同日的 revision 不算上一期）', async () => {
    const v = await loadCurrentSnapshot(true);
    expect(v.snapshot).not.toBeNull();
    if (v.previous) {
      expect(v.previous.snapshot_date < v.snapshot!.snapshot_date).toBe(true);
      expect(v.previous.snapshot_id).not.toBe(v.snapshot!.snapshot_id);
    }
  });

  it('预览模式：两份快照能算出 diff（有上一期才有 diff）', async () => {
    const v = await loadCurrentSnapshot(true);
    expect(v.previous).not.toBeNull();
    expect(v.diff).not.toBeNull();
    expect(v.diff?.from.snapshot_id).toBe(v.previous?.snapshot_id);
    expect(v.diff?.to.snapshot_id).toBe(v.snapshot?.snapshot_id);
    // 汇总自洽
    const d = v.diff!;
    expect(d.summary.total).toBe(
      d.summary.regime + d.summary.objects + d.summary.candidates + d.summary.observations,
    );
  });

  it('★★ P0 回指解析：候选明细能解析出来，且「名字像的不像、跨主题的才像」', async () => {
    const v = await loadCurrentSnapshot(true);
    const bci = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH');
    expect(bci, '真实快照里应有该对象').toBeDefined();
    expect(bci!.resolved).toBe(true);
    expect(bci!.details).toHaveLength(79);

    // 唯一的结构支持来自**跨大主题**的智能驾驶
    const supported = bci!.details.filter((d) => d.status === 'STRUCTURAL_SUPPORTED');
    expect(supported).toHaveLength(1);
    expect(supported[0].historicalCycleId).toBe('C-2023-AD');
    expect(supported[0].themeRelation).toBe('CROSS_MACRO_THEME');
    expect(supported[0].whySimilar.length).toBeGreaterThan(0);
    expect(supported[0].dimensions).toHaveLength(4);

    // ★ 同大主题的创新药反而只是「仅主题相同」—— 这是 ThreeC 的立身之论
    const pharma = bci!.details.find((d) => d.historicalCycleId === 'C-2019-PHARMA-INNOV');
    expect(pharma?.status).toBe('THEME_ONLY');
    expect(pharma?.themeRelation).toBe('SAME_MACRO_THEME');
  });

  it('★★ 对应的特异性：同一历史对象被多个方向命中时如实报出（真实数据）', async () => {
    const v = await loadCurrentSnapshot(true);
    const bci = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    const sup = bci.details.find((d) => d.status === 'STRUCTURAL_SUPPORTED')!;
    expect(sup.historicalCycleId).toBe('C-2023-AD');
    // ★ 实测：C-2023-AD 同时是另外几个方向的结构支持 —— 必须报出来
    expect(sup.alsoSupportedBy.length).toBeGreaterThanOrEqual(1);
    expect(sup.alsoSupportedBy).not.toContain('CC-2026-BCI-MEDTECH'); // 不含自身
    // 计数与全量一致：该历史对象在全部对象中的 STRUCTURAL_SUPPORTED 次数 − 1
    const total = v.detailsByObject.filter((d) =>
      d.details.some((x) => x.historicalCycleId === 'C-2023-AD' && x.status === 'STRUCTURAL_SUPPORTED'),
    ).length;
    expect(sup.alsoSupportedBy.length).toBe(total - 1);
    // 非 SUPPORTED 的条目不应带该提示（避免把弱对应说成强对应）
    for (const d of bci.details) {
      if (d.status !== 'STRUCTURAL_SUPPORTED') expect(d.alsoSupportedBy).toEqual([]);
    }
  });

  it('回指解析只合并、不重算：状态与快照里的计数一致', async () => {
    const v = await loadCurrentSnapshot(true);
    const snapCount = new Map<string, number>();
    for (const c of v.snapshot!.historical_candidates) {
      snapCount.set(c.current_object_id, (snapCount.get(c.current_object_id) ?? 0) + 1);
    }
    for (const d of v.detailsByObject) {
      expect(d.details.length).toBe(snapCount.get(d.objectId) ?? 0);
    }
  });

  it('★ 只读：载入不修改快照内容', async () => {
    const a = await loadCurrentSnapshot(true);
    const b = await loadCurrentSnapshot(true);
    expect(JSON.stringify(a.snapshot)).toBe(JSON.stringify(b.snapshot));
  });
});
