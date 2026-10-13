/**
 * Market Snapshot ↔ SA artifact **版本绑定**回归测试。
 *
 * ## 背景（2026-10-13 实测发现的静默混用）
 *
 * 快照是 `INDEX_ONLY` 模式 —— 它**只存** `identity + structural_status`，
 * 其余细节**回指**冻结的 SA artifact。因此「快照生成的版本」与
 * 「产品加载的 SA 版本」**必须一致**，否则会把两个不同版本的产物拼在一起。
 *
 * ★★ 实测缺口：`resolveDetails` 原先**只校验 `rule_set_version`** ——
 *   而该值在 SA v0.10 → v0.13 之间**一直是 `structural-analogy-ruleset-v0.3`**
 *   （规则集未变）→ 校验**恒等通过** → 「v0_12 的快照」与「v0_13 的细节」
 *   **被静默合并**（86 对象 vs 89 对象）。
 *
 * 修复：`resolveDetails` **同时校验 `artifact_version`**（快照的 `candidates_source`
 * 本来就带该字段，只是读取方没校验）。
 *
 * ## 本测试钉死的行为
 *
 * 无论「当前 CANONICAL 与产品 SA 是否同版本」，行为都必须自洽：
 * - **同版本** → 合并（`resolved = true`，details 非空）
 * - **不同版本** → **拒绝合并**（`resolved = false`，details 为空）—— 诚实空态
 *
 * ★ 这样写是为了**不把数据状态写成断言**：若把「必须同版本」写死，
 *   则每次「先升 SA、后签发快照」的窗口期都会红 —— 而那个窗口期是**正常的**
 *   （快照签发需人工审核）。本测试只钉**行为**，数据状态由 `--check` 的 C11 负责。
 */
import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { CANONICAL, loadCurrentSnapshot, snapshotIndex } from '../snapshotAdapter';

const repo = process.cwd();
const read = (rel: string) => fs.readFileSync(path.resolve(repo, rel), 'utf-8');

/** 产品实际消费的 SA artifact（唯一事实来源 = buildProvenance.ts 的静态 import） */
function importedSaFile(): string {
  const m = read('src/data/buildProvenance.ts').match(
    /structural_analogy_explanations_v0_(\d+)\.json/,
  );
  if (!m) throw new Error('buildProvenance.ts 中未找到 SA import');
  return m[0];
}

function artifactVersionOf(file: string): string {
  const doc = JSON.parse(read(path.join('research/research/reports', file))) as {
    artifact_version?: unknown;
  };
  return String(doc.artifact_version);
}

describe('★ 快照 ↔ SA 版本绑定（禁止静默混用）', () => {
  it('每个快照的 candidates_source 必须**声明** artifact 与 artifact_version', () => {
    const dir = path.resolve(repo, 'research/current/market_snapshots/snapshots');
    const files = fs.readdirSync(dir).filter((f) => f.endsWith('.json'));
    expect(files.length).toBeGreaterThan(0);
    for (const f of files) {
      const doc = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8')) as {
        candidates_source?: { artifact?: string; artifact_version?: string };
      };
      expect(doc.candidates_source?.artifact, `${f} 缺 candidates_source.artifact`).toBeTruthy();
      expect(
        doc.candidates_source?.artifact_version,
        `${f} 缺 candidates_source.artifact_version（读取方无法校验版本）`,
      ).toBeTruthy();
    }
  });

  it('★ 每个快照回指的 SA artifact **必须存在**，且其 artifact_version 与声明一致', () => {
    const dir = path.resolve(repo, 'research/current/market_snapshots/snapshots');
    for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.json'))) {
      const doc = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8')) as {
        candidates_source?: { artifact?: string; artifact_version?: string };
      };
      const declared = doc.candidates_source?.artifact_version;
      const file = path.basename(String(doc.candidates_source?.artifact ?? ''));
      const full = path.join(repo, 'research/research/reports', file);
      expect(fs.existsSync(full), `${f} 回指的 ${file} 不存在（回指悬空）`).toBe(true);
      expect(artifactVersionOf(file), `${f} 声明的版本与 ${file} 实际版本不符`).toBe(declared);
    }
  });

  it('★★ 行为钉死：版本**一致**才合并，**不一致**必须拒绝（resolved=false）', async () => {
    const v = await loadCurrentSnapshot(true);
    const snap = v.snapshot;
    expect(snap).not.toBeNull();

    const declared = (snap as unknown as { candidates_source?: { artifact_version?: string } })
      .candidates_source?.artifact_version;
    const consumed = artifactVersionOf(importedSaFile());

    const bci = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH');
    expect(bci, '真实快照里应有该对象').toBeDefined();

    if (declared === consumed) {
      // 版本一致 → 必须解析出细节
      expect(bci!.resolved, `快照 ${snap!.snapshot_id} 与产品 SA ${consumed} 同版本，应解析`).toBe(true);
      expect(bci!.details.length).toBeGreaterThan(0);
    } else {
      // ★ 版本不一致 → **必须拒绝合并**（诚实空态），不得把两个版本拼在一起
      expect(
        bci!.resolved,
        `快照 ${snap!.snapshot_id}(${declared}) 与产品 SA ${consumed} 版本不一致 → 必须拒绝合并`,
      ).toBe(false);
      expect(bci!.details).toHaveLength(0);
    }
  });

  it('★ 默认门禁（CANONICAL）与产品 SA 的版本关系同样必须自洽', async () => {
    const idx = snapshotIndex();
    const hasCanonical = idx.some((e) => e.status === CANONICAL);
    if (!hasCanonical) return; // 全部未签发时由既有「no-canonical」测试覆盖

    const v = await loadCurrentSnapshot();
    const declared = (v.snapshot as unknown as {
      candidates_source?: { artifact_version?: string };
    })?.candidates_source?.artifact_version;
    const consumed = artifactVersionOf(importedSaFile());

    const bci = v.detailsByObject.find((d) => d.objectId === 'CC-2026-BCI-MEDTECH');
    if (declared === consumed) {
      expect(bci!.resolved).toBe(true);
    } else {
      expect(bci!.resolved, 'CANONICAL 与产品 SA 版本不一致 → 必须拒绝合并').toBe(false);
      expect(bci!.details).toHaveLength(0);
    }
  });
});
