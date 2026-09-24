/**
 * deployment.test.ts —— ThreeC 1.0 Deployment / Release Engineering 的**机械校验**。
 *
 * 把「部署正确性」从「文档声明」变成「可重复执行的断言」。覆盖三件事：
 *
 *   1. **Gate D7 · Build provenance 可追溯**
 *      线上 build 必须能确定：Product version / Git commit / Research export source_commit /
 *      SA 版本 / TO 版本。本测试断言这些字段**确实可被 Product 读出且非空**，
 *      并断言它们与 artifact 原文**一致**（防止 provenance 是硬编码的假值）。
 *
 *   2. **Vite base 解析规则**
 *      本地必须为 `/`（不破坏 dev/preview），GitHub Actions 必须为 `/Cycle/`，
 *      `THREEC_BASE` 显式覆盖时必须被尊重（回滚 / 子路径复现的逃生口）。
 *
 *   3. **GitHub Pages workflow 契约**
 *      workflow 存在、必须跑 `npm test`、必须跑 build、必须上传 `dist`
 *      （**不得**上传源码）、permissions 最小化、不得把 `dist/` 提交进 Git。
 *
 * 注意：本文件**不**验证线上 URL 是否可用（那需要网络，属人工 production smoke test）。
 * 它只保证「一旦部署，部署物本身是对的」。
 */

import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

import { buildProvenance } from '../buildProvenance';

const repo = fileURLToPath(new URL('../../../', import.meta.url));
const read = (p: string) => readFileSync(new URL(p, import.meta.url), 'utf8');
const readJson = <T>(p: string): T =>
  JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8')) as T;

/* ============================ 1. Gate D7 · provenance ============================ */

describe('Deployment · Gate D7 build provenance', () => {
  const p = buildProvenance();

  const exportJson = readJson<{
    timeline_export_version: string;
    source_commit: string;
    generated_at: string;
    campaigns: unknown[];
    research_candidates: unknown[];
  }>('../../../exports/timeline_export_v1.json');

  const saJson = readJson<{ artifact_version: string | number; rule_set_version: string }>(
    '../../../research/research/reports/structural_analogy_explanations_v0_5.json',
  );
  const toJson = readJson<{ artifact_version: string | number }>(
    '../../../research/research/reports/time_observation_patterns_v0_2.json',
  );

  it('D7-1 Product version 可读且与 package.json 一致（不是硬编码假值）', () => {
    const pkg = readJson<{ version: string }>('../../../package.json');
    // 本地 vitest 不经过 vite define → 注入值为 undefined → provenance 为 null。
    // 构建期（vite build）才注入 —— 因此这里只在「已注入」时校验一致性。
    if (p.productVersion !== null) {
      expect(p.productVersion).toBe(pkg.version);
    } else {
      // 未构建环境下必须诚实为 null，**不得**退化成某个字面量
      expect(p.productVersion).toBeNull();
    }
  });

  it('D7-2 Research export provenance 可读且与 artifact 一致', () => {
    expect(p.exportVersion).toBe(exportJson.timeline_export_version);
    expect(p.exportSourceCommit).toBe(exportJson.source_commit);
    expect(p.exportGeneratedAt).toBe(exportJson.generated_at);
    expect(p.exportSourceCommitShort).toBe(exportJson.source_commit.slice(0, 7));
  });

  it('D7-3 SA / TO artifact 版本可读且与 artifact 一致', () => {
    expect(p.saArtifactVersion).toBe(String(saJson.artifact_version));
    expect(p.saRuleSetVersion).toBe(saJson.rule_set_version);
    expect(p.toArtifactVersion).toBe(String(toJson.artifact_version));
  });

  it('D7-4 研究对象数可读且与 export 一致（52 / 27）', () => {
    expect(p.exportObjectCounts).toEqual({
      campaigns: exportJson.campaigns.length,
      researchCandidates: exportJson.research_candidates.length,
    });
    expect(p.exportObjectCounts!.campaigns).toBe(52);
    expect(p.exportObjectCounts!.researchCandidates).toBe(27);
  });

  it('D7-5 provenance 是纯溯源信息：不含任何 score / 可信度 / 排名字段', () => {
    const keys = Object.keys(p).map((k) => k.toLowerCase());
    for (const bad of ['score', 'rank', 'confidence', 'probability', 'rating', 'grade']) {
      expect(keys.some((k) => k.includes(bad))).toBe(false);
    }
  });

  it('D7-6 git commit 在「有 git 环境」时必须等于真实 HEAD（构建期注入）', () => {
    if (p.gitCommit === null) return; // 无 inject 环境（vitest 直跑源码）
    let head = '';
    try {
      head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8' }).trim();
    } catch {
      return; // 无 git → 跳过（不编造）
    }
    expect(p.gitCommit).toBe(head);
  });
});

/* ============================ 2. Vite base 解析规则 ============================ */

describe('Deployment · Vite base 解析', () => {
  /**
   * 直接按 `vite.config.ts` 的 `resolveBase()` 契约断言。
   * 这里**不 import** vite.config（它会拖入 vite 运行时），而是断言源码中的规则存在 ——
   * 规则若被改动，本测试会失败并提醒同步（防「悄悄改成硬编码 /Cycle/」）。
   */
  const cfg = read('../../../vite.config.ts');

  it('base 规则：无环境变量 → `/`（本地 dev / preview 不被破坏）', () => {
    expect(cfg).toContain("return '/';");
  });

  it('base 规则：GITHUB_ACTIONS === "true" → `/Cycle/`（与 GitHub Pages 项目站路径一致）', () => {
    expect(cfg).toContain("process.env.GITHUB_ACTIONS === 'true'");
    expect(cfg).toContain("return '/Cycle/';");
  });

  it('base 规则：THREEC_BASE 显式覆盖优先（回滚 / 子路径复现的逃生口）', () => {
    expect(cfg).toContain('process.env.THREEC_BASE');
  });

  it('不使用 `command === "serve"` 分支（否则 preview 无法复现 production 行为）', () => {
    // 只检查**代码行**（去掉注释行），否则说明性注释里提到该反模式会误报
    const code = cfg
      .split('\n')
      .filter((l) => !/^\s*(\/\/|\*|\/\*)/.test(l))
      .join('\n');
    expect(code).not.toContain("command === 'serve'");
    expect(code).not.toContain('command === "serve"');
  });

  it('base 解析基于官方内置变量 GITHUB_ACTIONS + 显式覆盖，不依赖第三方环境变量名', () => {
    for (const foreign of ['NETLIFY', 'VERCEL', 'CF_PAGES', 'GITLAB_CI']) {
      expect(cfg).not.toContain(foreign);
    }
  });
});

/* ============================ 3. GitHub Pages workflow 契约 ============================ */

describe('Deployment · GitHub Pages workflow', () => {
  const wfPath = '../../../.github/workflows/deploy.yml';
  const wf = read(wfPath);

  it('workflow 文件存在且为 GitHub Pages 官方形式', () => {
    expect(existsSync(new URL(wfPath, import.meta.url))).toBe(true);
    expect(wf).toContain('actions/upload-pages-artifact@');
    expect(wf).toContain('actions/deploy-pages@');
    expect(wf).toContain('actions/checkout@');
    expect(wf).toContain('actions/setup-node@');
  });

  it('触发条件：push main + workflow_dispatch（可在 Actions 页手动重跑）', () => {
    expect(wf).toMatch(/branches:\s*\[main\]/);
    expect(wf).toContain('workflow_dispatch:');
  });

  it('★ 不允许跳过 npm test：workflow 必须执行 `npm test`', () => {
    expect(wf).toMatch(/run:\s*npm test/);
  });

  it('★ 必须执行类型检查与构建，且 build 与 test 同 job 串行（test 先于 build）', () => {
    const iTsc = wf.indexOf('npx tsc -b');
    const iTest = wf.indexOf('npm test');
    const iBuild = wf.indexOf('npm run build');
    expect(iTsc).toBeGreaterThan(-1);
    expect(iTest).toBeGreaterThan(-1);
    expect(iBuild).toBeGreaterThan(-1);
    expect(iTest).toBeLessThan(iBuild); // 测试在构建之前 → 测试失败绝不产出部署物
  });

  it('★ 安装走 npm ci（锁文件确定性），不用 npm install', () => {
    expect(wf).toMatch(/run:\s*npm ci/);
    expect(wf).not.toMatch(/run:\s*npm install/);
  });

  it('★ 只上传构建产物 dist（不部署源码）', () => {
    expect(wf).toMatch(/path:\s*dist/);
  });

  it('★ base path 硬门禁：产物不得含 /assets/ 绝对引用，且必须含 /Cycle/assets/', () => {
    expect(wf).toContain('"/assets/');
    expect(wf).toContain('/Cycle/assets/');
  });

  it('deploy job 依赖 build job，且绑定 github-pages environment', () => {
    expect(wf).toMatch(/needs:\s*build/);
    expect(wf).toContain('name: github-pages');
  });

  it('permissions 最小化：contents:read + pages:write + id-token:write（无多余写权限）', () => {
    expect(wf).toContain('contents: read');
    expect(wf).toContain('pages: write');
    expect(wf).toContain('id-token: write');
    // 不得出现宽泛的 write-all / 危险权限
    expect(wf).not.toContain('write-all');
    expect(wf).not.toContain('actions: write');
    expect(wf).not.toContain('packages: write');
    expect(wf).not.toContain('deployments: write');
  });

  it('不引入第三方托管 / 后端 / 容器', () => {
    for (const foreign of ['vercel', 'netlify', 'docker', 'aws-actions', 'azure', 'gcloud']) {
      expect(wf.toLowerCase()).not.toContain(foreign);
    }
  });

  it('concurrency 固定 group=pages 且不取消进行中部署（避免半成品上线）', () => {
    expect(wf).toMatch(/group:\s*pages/);
    expect(wf).toMatch(/cancel-in-progress:\s*false/);
  });
});

/* ============================ 4. dist 不得进版本控制 ============================ */

describe('Deployment · 生成物不入库', () => {
  it('.gitignore 忽略 dist/ 与 node_modules/（部署走 CI artifact）', () => {
    const gi = read('../../../.gitignore');
    expect(gi).toMatch(/^dist\/$/m);
    expect(gi).toMatch(/^node_modules\/$/m);
  });

  it('dist/ 确实未被 git 跟踪（若存在）', () => {
    let tracked = '';
    try {
      tracked = execFileSync('git', ['ls-files', 'dist'], { cwd: repo, encoding: 'utf8' }).trim();
    } catch {
      return; // 无 git → 跳过
    }
    expect(tracked).toBe('');
  });
});
