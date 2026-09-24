import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

/**
 * Monorepo（ThreeC）：canonical Research Export 只有一份 —— 根 exports/timeline_export_v1.json。
 * 前端 Adapter 经 `@exports/*` alias 直接消费，不再维护 src/data/timeline/data/ 手工副本。
 * 见 docs/PROJECT_STATE.md「Export canonical source」与 contracts/timeline_export_v1.md。
 *
 * `@current` 指向 research/current/ —— Current Research Discovery 的**静态研究 Artifact**
 * （Phase 7）。同样是「Research 生成、Product 只读消费」：静态 import，无运行时网络请求。
 * 网络 / AI 只出现在研究数据生成端，不进入产品运行端。
 *
 * `@observation` 指向 research/research/reports/ —— Time-based Observation Layer 的
 * **静态研究 Artifact**（Phase 7.2，`time_observation_patterns_v0_2.json`）。
 * 同样只读消费；该目录下的探索性脚本与中间结果**不是**产品依赖。
 *
 * ## base（部署子路径）
 * GitHub Pages 正式入口为 `https://yangfanbit.github.io/Cycle/` → 产物资源必须为 `/Cycle/assets/...`。
 * 采用**双变量 + 本地默认 `/`** 的设计，避免把子路径硬编码进本地开发：
 *   - `THREEC_BASE`  —— 显式覆盖（回滚 / 私有镜像 / 本地子路径复现）
 *   - `GITHUB_ACTIONS` —— GitHub 官方内置变量（恒为 `"true"`），CI 自动取 `/Cycle/`
 *   - 两者皆无 → `/`，本地 `dev` / `preview` / `test` 行为与部署前完全一致。
 * **不使用** `command === 'serve'` 分支：那会让 `vite preview` 与 `build` 产物不一致，
 * 无法在本地复现 GitHub Pages 行为（preview 的意义正在于复现 production）。
 */
function resolveBase(): string {
  const explicit = process.env.THREEC_BASE;
  if (explicit !== undefined) return explicit;
  if (process.env.GITHUB_ACTIONS === 'true') return '/Cycle/';
  return '/';
}

/**
 * 构建溯源注入（Gate D7）。
 * - `version` 读 `package.json`（**不**在代码里硬编码，避免与 package.json 漂移）
 * - `commit` 取当前 checkout 的 HEAD（CI 中即 workflow 检出的 commit）
 * - `buildTime` 取构建时刻
 * 任一不可得 → 注入字面量 `"unknown"`，由 `src/data/buildProvenance.ts` 转为 `null` 并显示「未标注」。
 * 全部是**字符串字面量**，不使用 `process.env` 的运行时取值（否则在浏览器里会 ReferenceError）。
 */
function provenanceDefines(): Record<string, string> {
  let version = 'unknown';
  try {
    const pkg = JSON.parse(
      readFileSync(fileURLToPath(new URL('./package.json', import.meta.url)), 'utf8'),
    ) as { version?: string };
    if (typeof pkg.version === 'string' && pkg.version.length > 0) version = pkg.version;
  } catch {
    /* 保留 unknown */
  }

  let commit = 'unknown';
  try {
    commit = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
  } catch {
    /* 无 git 环境（如仅解压源码）→ 保留 unknown */
  }

  return {
    __THREEC_PRODUCT_VERSION__: JSON.stringify(version),
    __THREEC_GIT_COMMIT__: JSON.stringify(commit),
    __THREEC_BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  };
}

export default defineConfig({
  base: resolveBase(),
  define: provenanceDefines(),
  plugins: [react()],
  resolve: {
    alias: {
      '@exports': fileURLToPath(new URL('./exports', import.meta.url)),
      '@current': fileURLToPath(new URL('./research/current', import.meta.url)),
      '@observation': fileURLToPath(new URL('./research/research/reports', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'node',
  },
});
