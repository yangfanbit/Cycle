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

  it('★★ deploy.yml **不得**硬编码具体 SA 版本文件（必须自动发现）', () => {
    // 允许出现在注释里（解释历史教训），但**不得**出现在 `run:` 的命令中。
    //   ★ 本文件自身**不得**出现任何具体 SA 版本字面量 —— `refresh_downstream.py --check`
    //     的 C2 会全局扫 `src/**`（含测试、含注释），出现旧版本号会被判为「引用旧 SA」。
    const hardcoded = deployYml
      .split('\n')
      .filter((ln) => !ln.trimStart().startsWith('#'))
      .filter((ln) => /structural_analogy_explanations_v0_\d+\.json/.test(ln));
    expect(
      hardcoded,
      `deploy.yml 的命令行中硬编码了 SA 版本文件（应改为自动发现）：\n${hardcoded.join('\n')}`,
    ).toEqual([]);
  });

  it('★★ deploy.yml 保留硬门禁：与产品消费版本不一致时拒绝部署', () => {
    // 必须从 buildProvenance.ts 提取「产品实际消费的」版本作比对基准
    expect(deployYml).toContain('src/data/buildProvenance.ts');
    // 且必须在不一致时失败（`exit 1`）
    expect(deployYml).toMatch(/SA\s*版本不一致[\s\S]{0,200}exit 1/);
  });

  it('deploy.yml 的部署摘要从**自动发现的文件**取 artifact_version（不写死路径）', () => {
    expect(deployYml).toMatch(/SA_FILE=\$\(ls .*structural_analogy_explanations_v\*\.json/);
    expect(deployYml).toMatch(/require\('\.\/\$\{SA_FILE\}'\)\.artifact_version/);
  });
});
