// @vitest-environment jsdom
/**
 * ★★ v0.22 端到端：历史事件 SA 列表 → **当前研究对象**详情（页面级 jsdom + 真实 App + 真实数据）。
 *
 * ① SA 记录里的真实 `CC-*` 当前研究对象 →「查看当前对象详情」经**既有**
 *    `focusObject` / CurrentTimeLens 流程定位到该当前对象，并展开其结构对应详情；
 * ② 当前对象 ID 无法被当前研究对象数据解析 → **不**渲染按钮，保留 ID / 名称 / 状态并说明无法导航；
 * ③ **历史对象**的既有导航（`查看对象详情` → CampaignDetail）不受影响 —— 两种对象各走各的流程；
 * ④ CANONICAL 唯一性门禁由 `saCrossReference.test.ts` 的纯函数覆盖。
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { renderToStaticMarkup } from 'react-dom/server';
import { act } from 'react';

import App from '../../App';
import { defaultCurrentCandidateDataset } from '../../data/timeline/currentCandidate';
import { EventCardBody } from '../ExternalSeasonalRadar/HistoricalEventMap';
import { eventMapByTheme, type HistoricalEvent } from '../../data/timeline/historicalEventMaps';
import {
  emptySaCrossReference,
  type SaCrossReferenceIndex,
  type SaReferenceRow,
} from '../../data/marketSnapshot/saCrossReference';

beforeEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  window.localStorage.clear();
});
afterEach(() => {
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = false;
  document.body.innerHTML = '';
});

const click = async (b: HTMLElement) => { await act(async () => { b.click(); }); };

/** 等待异步（冻结 SA 快照按需载入）完成：轮询式 act 冲刷 */
async function waitFor(pred: () => boolean, tries = 80): Promise<boolean> {
  for (let i = 0; i < tries; i += 1) {
    if (pred()) return true;
    // eslint-disable-next-line no-await-in-loop
    await act(async () => { await new Promise((r) => { setTimeout(r, 10); }); });
  }
  return pred();
}

const candidateName = (id: string): string =>
  defaultCurrentCandidateDataset().candidates.find((c) => c.candidate_id === id)?.display_name ?? '';

describe('v0.22 端到端：SA 列表 → 当前研究对象详情导航', () => {
  it('★★ 半导体 2023 AI 算力事件：点击 SA 里的真实 CC-* → 经既有流程定位到该当前对象及结构详情', async () => {
    const host = document.createElement('div');
    document.body.appendChild(host);
    const root: Root = createRoot(host);
    await act(async () => { root.render(<App />); });

    const maps = document.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    await click(maps.querySelector('button[data-theme-id="SEMICONDUCTOR_AI"]') as HTMLButtonElement);

    const card = maps.querySelector('li[data-event-id="SEMI-2023-AI-COMPUTE"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);

    // 冻结 SA 按需载入
    const ok = await waitFor(() => card.querySelector('[data-sa-match="found"]') !== null);
    expect(ok, '冻结 SA 块应载入').toBe(true);

    // 6 条当前对象记录，每条都带「查看当前对象详情」按钮（真实 CC-* 全部可解析）
    const rows = [...card.querySelectorAll('[data-sa-current]')] as HTMLElement[];
    expect(rows.length).toBe(6);
    const buttons = [...card.querySelectorAll('[data-sa-open="current-object"]')] as HTMLButtonElement[];
    expect(buttons.length).toBe(6);
    expect(card.querySelector('[data-sa-open="unresolved"]')).toBeNull();

    // 取第一条：记录其精确 ID 与名称
    const row = rows[0];
    const targetId = row.getAttribute('data-sa-current') as string;
    const targetName = candidateName(targetId);
    expect(targetId.startsWith('CC-')).toBe(true);
    expect(targetName.length).toBeGreaterThan(0);

    // 点击 → 既有 focusObject / CurrentTimeLens 流程
    const btn = row.querySelector('[data-sa-open="current-object"]') as HTMLButtonElement;
    await click(btn);

    // ① 承载它的原生 <details> 被展开
    const lens = document.getElementById('drill-current-time-lens') as HTMLDetailsElement;
    expect(lens.open).toBe(true);

    // ② 恰好一个当前研究对象被就地展开，且**是该精确对象**
    const openItems = [...document.querySelectorAll('.ccs-item.open')] as HTMLElement[];
    expect(openItems.length).toBe(1);
    expect(openItems[0].querySelector('.ccs-name')?.textContent ?? '').toContain(targetName);

    // ③ 并展开其结构对应详情（异步载入冻结 SA 解释）
    const saOk = await waitFor(() =>
      openItems[0].querySelector('.sa-subject-name')?.textContent === targetName);
    expect(saOk, '应定位到该当前对象的结构对应详情').toBe(true);

    await act(async () => { root.unmount(); });
  });

  it('★ 历史对象的既有导航不受影响：`查看对象详情` 仍打开 CampaignDetail', async () => {
    const host = document.createElement('div');
    document.body.appendChild(host);
    const root: Root = createRoot(host);
    await act(async () => { root.render(<App />); });

    const maps = document.querySelector('[aria-label="历史题材地图"]') as HTMLElement;
    await click(maps.querySelector('button[data-theme-id="SEMICONDUCTOR_AI"]') as HTMLButtonElement);
    const card = maps.querySelector('li[data-event-id="SEMI-2023-AI-COMPUTE"]') as HTMLElement;
    await click(card.querySelector('button.fem-event-head') as HTMLButtonElement);
    await waitFor(() => card.querySelector('[data-sa-match="found"]') !== null);

    const objBtn = card.querySelector('button.fem-obj-open') as HTMLButtonElement;
    expect(objBtn, '历史对象的「查看对象详情」按钮仍在').not.toBeNull();
    await click(objBtn);
    // 打开的是既有历史对象详情（CampaignDetail），不是当前对象流程
    expect(document.querySelector('.detail-panel')).not.toBeNull();

    await act(async () => { root.unmount(); });
  });
});

describe('v0.22：当前对象 ID 无法解析 → 不渲染按钮（组件级，注入合成索引）', () => {
  const row = (
    id: string, name: string, status = 'NO_VALID_CORRESPONDENCE',
  ): SaReferenceRow => ({
    currentObjectId: id,
    currentObjectName: name,
    currentObjectTheme: null,
    structuralStatus: status,
    statusLabel: status,
    strictStructuralSupported: false,
  });

  it('★★ 不可解析行：保留 ID / 名称 / 状态 + 明确说明，不出现无效按钮', () => {
    const e = eventMapByTheme('SEMICONDUCTOR_AI')!.doc.events
      .find((x) => x.event_id === 'SEMI-2023-AI-COMPUTE') as HistoricalEvent;
    const objectId = (e.campaign_facts?.object_id ?? e.campaign_facts?.campaign_id) as string;

    const realIds = new Set(defaultCurrentCandidateDataset().candidates.map((c) => c.candidate_id));
    const canOpen = (id: string) => realIds.has(id);

    // 一条真实可解析 + 一条**不存在**的当前对象 ID
    const idx: SaCrossReferenceIndex = emptySaCrossReference(null);
    idx.loaded = true;
    idx.snapshotId = 'MS-TEST';
    idx.byHistoricalObject = new Map([[objectId, [
      row('CC-2026-COMPUTE-POWER', '算力电力'),
      row('CC-9999-NOT-REAL', '未知研究对象'),
    ]]]);

    const html = renderToStaticMarkup(
      <EventCardBody
        e={e}
        saRef={idx}
        onOpenObject={() => {}}
        canOpenObject={() => true}
        onOpenCurrentObject={() => {}}
        canOpenCurrentObject={canOpen}
      />,
    );

    // 可解析行 → 恰好一个按钮
    expect((html.match(/data-sa-open="current-object"/g) ?? []).length).toBe(1);
    // 不可解析行 → 说明文本，**无**按钮
    expect(html).toContain('data-sa-open="unresolved"');
    expect(html).toContain('无法通过现有详情流程解析');
    // ID / 名称 / 状态**原样保留**
    expect(html).toContain('CC-9999-NOT-REAL');
    expect(html).toContain('未知研究对象');
    expect(html).toContain('data-sa-status="NO_VALID_CORRESPONDENCE"');
  });
});
