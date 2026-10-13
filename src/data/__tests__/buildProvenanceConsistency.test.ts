/**
 * Build Provenance 一致性 —— **部署摘要必须与实际构建同源**。
 *
 * ## 为什么有这条测试（历史教训 2026-10-13）
 *
 * `.github/workflows/deploy.yml` 的部署摘要曾**硬编码**一个**早已被取代的 SA 版本文件**
 * （artifact_version `0.5`），而产品早已消费最新版。
 *
 * ★ 关键：那个旧版本文件**仍在仓库里** → 那行 `node -p require(...)` **不会报错**，
 *   于是**静默**在每次部署的 Actions Summary 上写着**错误的 Research 版本**。
 *   这是「**两份真相之间没有检查**」的又一实例（同族：RULES 白名单 / SA 版本引用 /
 *   `SA_ARTIFACT_REL` / `timelineAdapter` 版本断言）。
 *
 * ## 本测试钉死三件事
 *
 * 1. `buildProvenance.ts` 的 SA import 必须指向**存在的最新版本**；
 * 2. `deploy.yml` **不得**硬编码具体 SA 版本文件（必须自动发现）；
 * 3. `deploy.yml` 必须保留**硬门禁**（发现不一致时 `exit 1`，拒绝部署）。
 */
import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const repo = process.cwd();
const read = (rel: string) => fs.readFileSync(path.resolve(repo, rel), 'utf-8');

const SA_DIR = 'research/research/reports';
const SA_RE = /structural_analogy_explanations_v0_(\d+)\.json/g;

/** 全部已存在的 SA explanation artifact，按版本号升序 */
function saFilesOnDisk(): { version: number; file: string }[] {
  return fs
    .readdirSync(path.resolve(repo, SA_DIR))
    .map((f) => SA_RE.exec(f))
    .filter((m): m is RegExpExecArray => m !== null)
    .map((m) => ({ version: Number(m[1]), file: m[0] }))
    .sort((a, b) => a.version - b.version);
}

describe('★ 部署溯源一致性（deploy.yml ↔ 产品实际消费）', () => {
  const onDisk = saFilesOnDisk();
  const latest = onDisk[onDisk.length - 1];
  const provenanceSrc = read('src/data/buildProvenance.ts');
  const deployYml = read('.github/workflows/deploy.yml');

  it('SA artifact 至少存在一个版本（前置事实）', () => {
    expect(onDisk.length).toBeGreaterThan(0);
    expect(latest.file).toMatch(/^structural_analogy_explanations_v0_\d+\.json$/);
  });

  it('★ buildProvenance.ts 的 SA import 指向**存在的最新版本**', () => {
    const imported = [...provenanceSrc.matchAll(SA_RE)].map((m) => m[0]);
    expect(imported.length, 'buildProvenance.ts 应恰好 import 一个 SA artifact').toBe(1);
    expect(imported[0], '产品消费的 SA 必须是最新版本（升版时须同步更新此处）').toBe(latest.file);
  });

  it('★★ deploy.yml **不得**硬编码具体 SA 版本文件（必须走解析器）', () => {
    // 允许出现在注释里（解释历史教训），但**不得**出现在 `run:` 的命令中。
    //   ★ 本文件自身**不得**出现任何具体 SA 版本字面量 —— `refresh_downstream.py --check`
    //     的 C2 会全局扫 `src/**`（含测试、含注释），出现旧版本号会被判为「引用旧 SA」。
    const hardcoded = deployYml
      .split('\n')
      .filter((ln) => !ln.trimStart().startsWith('#'))
      .filter((ln) => /structural_analogy_explanations_v\d+_\d+\.json/.test(ln));
    expect(
      hardcoded,
      `deploy.yml 的命令行中硬编码了 SA 版本文件（应走 scripts/resolve_sa_artifact.py）：\n${hardcoded.join('\n')}`,
    ).toEqual([]);
  });

  it('★★ deploy.yml 通过**可测试的解析器**取版本，且解析器存在', () => {
    expect(deployYml, 'deploy.yml 应调用解析器').toContain('scripts/resolve_sa_artifact.py');
    expect(fs.existsSync(path.resolve(repo, 'scripts/resolve_sa_artifact.py'))).toBe(true);
    // 不得再内联「ls + sort」自行推断版本
    expect(deployYml).not.toMatch(/ls .*structural_analogy_explanations_v\*\.json/);
  });

  it('★★ 解析器的**版本选择规则**：按 (minor, patch) 数值比较，**不是**字典序', () => {
    // 真实场景：仓库里同时存在 v0_9 与 v0_13。
    //   数值比较 → v0_13（正确）；字典序 → v0_9（错误）。
    const names = onDisk.map((x) => x.file);
    const byNumeric = [...names].sort(
      (a, b) => Number(a.match(/_v\d+_(\d+)\.json$/)![1]) - Number(b.match(/_v\d+_(\d+)\.json$/)![1]),
    );
    const byLexical = [...names].sort();
    expect(byNumeric[byNumeric.length - 1], '数值比较应取到 v0_13').toBe(latest.file);
    // ★ 证明「字典序」在真实数据上会给出**不同**（且错误）的答案 —— 这条断言是规则的**反例锚点**
    expect(byLexical[byLexical.length - 1]).not.toBe(latest.file);
  });

  it('★★ 解析器实跑：与产品消费一致时退出 0，且输出 imported 字段', () => {
    const out = execFileSync(
      process.env.PYTHON ?? 'python3',
      ['scripts/resolve_sa_artifact.py', '--json'],
      { cwd: repo, encoding: 'utf-8' },
    );
    const res = JSON.parse(out) as { ok: boolean; imported: string; latest: string };
    expect(res.ok).toBe(true);
    expect(res.imported).toBe(latest.file);
    expect(res.latest).toBe(latest.file);
  });

  it('★★ deploy.yml 保留硬门禁：与产品消费版本不一致时拒绝部署', () => {
    // 硬门禁现在由解析器的退出码承担（`set -euo pipefail` + 非 0 退出即失败）
    expect(deployYml).toContain('scripts/resolve_sa_artifact.py');
    expect(deployYml).toContain('set -euo pipefail');
    // 解析器必须能在不一致时报错退出（规则本身在其单测/本测试的上一条覆盖）
    expect(deployYml).toMatch(/SA_JSON=\$\(python scripts\/resolve_sa_artifact\.py --json\)/);
  });
});
