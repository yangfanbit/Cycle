/**
 * 快照 × SA 版本门禁回归测试（v0.6 B 工作流验收，2026-10-16）。
 *
 * 守护**真实失效路径**（不是快照式断言）：
 *   ① artifact_version 不一致 → 必须拒绝合并（2026-10-13 v0.12×v0.13 混版事故的复发守护）
 *   ② rule_set_version 不一致 → 必须拒绝合并
 *   ③ 版本**匹配** → 必须合并（同时证明 mock 脚手架有效，不是「永远拒绝」的假通过）
 *   ④ ★★ fail-closed：`candidates_source` 缺失 / 缺任一版本字段 → **也必须拒绝合并**
 *      —— 原实现 `if (expected && 不一致)` 在缺字段时**短路放行**，
 *         与 ① 是同一模式（「没得可校」≠「校验通过」）。2026-10-16 修为 fail-closed。
 *
 * 运行：npx vitest run src/data/marketSnapshot/__tests__/snapshotVersionGate.test.ts \
 *        --pool=forks --poolOptions.forks.singleFork
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { loadCurrentSnapshot } from '../snapshotAdapter';

/** 可变的假快照内容（vi.mock 工厂惰性读取） */
const hoisted = vi.hoisted(() => ({ fake: null as Record<string, unknown> | null }));
const setFakeSnapshot = (v: Record<string, unknown> | null) => {
  hoisted.fake = v;
};

// 索引只留一条 CANONICAL 10-13（隔离默认加载逻辑）
vi.mock('@market/index.json', () => ({
  default: {
    contract: 'market_snapshot_index',
    index_version: '0.1',
    snapshots: [
      {
        file: 'MS-2026-10-13-01.json',
        market_snapshot_version: '0.3',
        snapshot_date: '2026-10-13',
        snapshot_id: 'MS-2026-10-13-01',
        status: 'CANONICAL',
      },
    ],
  },
}));

// 必须用 getter 惰性读取 —— vi.mock 工厂结果会被缓存，直接固化第一个测试的值
vi.mock('@market/snapshots/MS-2026-10-13-01.json', () => ({
  get default() {
    return hoisted.fake;
  },
}));

function makeSnapshot(candidatesSource: unknown): Record<string, unknown> {
  return {
    contract: 'market_snapshot',
    market_snapshot_version: '0.3',
    snapshot_id: 'MS-2026-10-13-01',
    snapshot_date: '2026-10-13',
    status: 'CANONICAL',
    market_regime: {
      broad_index_state: 'UNKNOWN',
      breadth_state: 'UNKNOWN',
      liquidity_state: 'UNKNOWN',
      risk_appetite_state: 'UNKNOWN',
    },
    research_objects: [
      {
        object_id: 'CC-2026-BCI-MEDTECH',
        object_kind: 'theme',
        display_name: 'x',
        declared_phase: 'UNKNOWN',
        resolution_state: 'RESOLVED',
      },
    ],
    observations: [],
    historical_candidates: [],
    ...(candidatesSource === undefined ? {} : { candidates_source: candidatesSource }),
  };
}

beforeEach(() => {
  setFakeSnapshot(null);
});
afterEach(() => {
  vi.restoreAllMocks();
});

describe('快照 × SA 版本门禁（真实失效路径）', () => {
  it('★★ artifact_version 不一致 → resolved=false（诚实空态，不混版）', async () => {
    setFakeSnapshot(makeSnapshot({
      artifact: 'research/research/reports/structural_analogy_explanations_v0_13.json',
      artifact_version: '0.99',
      rule_set_version: 'structural-analogy-ruleset-v0.3',
    }));
    const v = await loadCurrentSnapshot(false);
    expect(v.state).toBe('ok');
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved).toBe(false);
    expect(o.details).toHaveLength(0);
    expect(o.profile).toBeNull();
  });

  it('★★ rule_set_version 不一致 → resolved=false', async () => {
    setFakeSnapshot(makeSnapshot({
      artifact: 'research/research/reports/structural_analogy_explanations_v0_13.json',
      artifact_version: '0.13',
      rule_set_version: 'structural-analogy-ruleset-v9.9',
    }));
    const v = await loadCurrentSnapshot(false);
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved).toBe(false);
    expect(o.details).toHaveLength(0);
  });

  it('★★ 对照（脚手架有效性）：版本**匹配** → 必须合并（resolved=true，89 条解释）', async () => {
    setFakeSnapshot(makeSnapshot({
      artifact: 'research/research/reports/structural_analogy_explanations_v0_13.json',
      artifact_version: '0.13',
      rule_set_version: 'structural-analogy-ruleset-v0.3',
    }));
    const v = await loadCurrentSnapshot(false);
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved).toBe(true);
    expect(o.details.length).toBe(89);
  });

  it('★★★ fail-closed：`candidates_source` 整个缺失 → 不得放行合并', async () => {
    setFakeSnapshot(makeSnapshot(undefined));
    const v = await loadCurrentSnapshot(false);
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved, '缺 candidates_source 时无法校验版本 → 必须拒绝合并').toBe(false);
    expect(o.details).toHaveLength(0);
    expect(o.profile).toBeNull();
  });

  it('★★★ fail-closed：缺 `artifact_version`（仅 rule_set 匹配）→ 不得放行', async () => {
    // ★ 这正是 2026-10-13 事故的形状：rule_set_version 跨 v0.10→v0.13 一直没变，
    //   只有 artifact_version 能区分版本。缺它就无法分辨 → 必须拒绝，不能赌。
    setFakeSnapshot(makeSnapshot({
      artifact: 'research/research/reports/structural_analogy_explanations_v0_13.json',
      rule_set_version: 'structural-analogy-ruleset-v0.3',
    }));
    const v = await loadCurrentSnapshot(false);
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved, '缺 artifact_version 时不得放行合并').toBe(false);
    expect(o.details).toHaveLength(0);
  });

  it('★★★ fail-closed：缺 `rule_set_version`（仅 artifact 匹配）→ 不得放行', async () => {
    setFakeSnapshot(makeSnapshot({
      artifact: 'research/research/reports/structural_analogy_explanations_v0_13.json',
      artifact_version: '0.13',
    }));
    const v = await loadCurrentSnapshot(false);
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved, '缺 rule_set_version 时不得放行合并').toBe(false);
    expect(o.details).toHaveLength(0);
  });

  it('★★★ fail-closed：版本字段为**空串** → 同样不得放行', async () => {
    setFakeSnapshot(makeSnapshot({
      artifact: 'research/research/reports/structural_analogy_explanations_v0_13.json',
      artifact_version: '',
      rule_set_version: '',
    }));
    const v = await loadCurrentSnapshot(false);
    const o = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH')!;
    expect(o.resolved, '空版本字段等同缺失 → 必须拒绝合并').toBe(false);
  });
});
