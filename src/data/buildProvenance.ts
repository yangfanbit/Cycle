/**
 * Build Provenance —— Product build ↔ Research artifact 版本可追溯（Gate D7）。
 *
 * ## 定位
 * 回答**唯一**一个问题：**「线上这个 build 到底消费了哪一版 Research 结论？」**
 *
 * 它**不**引入新的 metadata 系统、不新增 API、不新增后端、不访问网络、
 * 不修改任何 Research artifact schema。全部字段都是**已有事实的汇总**：
 *
 *   | 字段 | 来源 | 说明 |
 *   |---|---|---|
 *   | `productVersion` | `package.json` `version` | 构建时由 Vite `define` 注入 |
 *   | `gitCommit` | `git rev-parse HEAD` | 构建时注入；CI 为 workflow 检出的 commit |
 *   | `gitCommitShort` | 同上 | UI 展示用的 7 位短 hash |
 *   | `buildTime` | 构建时刻 | CI 为 UTC ISO；本地构建同样填写（与上游 artifact 时间语义区分） |
 *   | `exportVersion` | `exports/timeline_export_v1.json` `timeline_export_version` | Contract 版本 |
 *   | `exportSourceCommit` | 同文件 `source_commit` | **Research 生成该 export 时的 commit** —— 关键溯源锚点 |
 *   | `exportGeneratedAt` | 同文件 `generated_at` | export 生成时间 |
 *   | `exportObjectCounts` | 同文件 `campaigns` / `research_candidates` 长度 | 52 / 27 |
 *   | `saArtifactVersion` | SA artifact `artifact_version` | 例：`0.5`（文件：`…_v0_5.json`） |
 *   | `saRuleSetVersion` | SA artifact `rule_set_version` | 例：`structural-analogy-ruleset-v0.3` |
 *   | `toArtifactVersion` | TO artifact `artifact_version` | 例：`0.3`（文件：`…_v0_2.json`） |
 *
 * ## 为什么这些能直接 import
 * 三个 artifact 都是**静态 import**（Vite 的 `@exports` / `@observation` alias，
 * 与 Product 其它模块消费它们的方式完全一致）→ 构建期就被打包，**运行时零网络请求**，
 * 不破坏「静态 PWA」前提。
 *
 * 注意：SA / TO 的**完整解析**走各自的 Adapter（`structuralAnalogy.ts` /
 * `timeObservationPatterns.ts`），本模块只取**版本元数据**，**不**重复解析业务内容。
 *
 * ## 边界
 * - 只读、只汇总；**不**做任何研究判断。
 * - **不**显示为「可信度 / 完整度 / 评分」—— 它是溯源信息，不是质量指标。
 * - 字段缺失时返回 `null` 并在 UI 明示「未标注」，**不猜测**。
 */

import timelineExportJson from '@exports/timeline_export_v1.json';
import saArtifactJson from '@observation/structural_analogy_explanations_v0_5.json';
import toArtifactJson from '@observation/time_observation_patterns_v0_2.json';

/** 构建时由 Vite `define` 注入；未注入时（如 vitest 直接跑源码）为 `undefined`。 */
declare const __THREEC_PRODUCT_VERSION__: string | undefined;
declare const __THREEC_GIT_COMMIT__: string | undefined;
declare const __THREEC_BUILD_TIME__: string | undefined;

const UNKNOWN_TOKEN = 'unknown';

function injected(v: string | undefined): string | null {
  const s = typeof v === 'string' ? v.trim() : '';
  if (s.length === 0 || s === UNKNOWN_TOKEN) return null;
  return s;
}

function asStringOrNull(v: unknown): string | null {
  return typeof v === 'string' && v.length > 0 ? v : null;
}

export interface BuildProvenance {
  /** `package.json` `version`（本轮仍为 `0.1.0` —— 未提前升为 1.0.0）。 */
  productVersion: string | null;
  /** 构建时的 Git commit（完整 SHA）；本地无 git 信息时为 null。 */
  gitCommit: string | null;
  /** 7 位短 hash（UI 展示用）。 */
  gitCommitShort: string | null;
  /** 构建时刻（ISO 8601）。 */
  buildTime: string | null;
  /** Timeline Export Contract 版本（`timeline_export_version`）。 */
  exportVersion: string | null;
  /** ★ Research 生成该 export 时的 commit —— Product build 与 Research 结论的对应锚点。 */
  exportSourceCommit: string | null;
  exportSourceCommitShort: string | null;
  /** export 生成时间（Research 侧时间，**不是** Product 构建时间）。 */
  exportGeneratedAt: string | null;
  exportObjectCounts: { campaigns: number; researchCandidates: number } | null;
  /** Structural Analogy artifact 版本。 */
  saArtifactVersion: string | null;
  saRuleSetVersion: string | null;
  /** Time Observation artifact 版本。 */
  toArtifactVersion: string | null;
}

function readInjected(): {
  version: string | null;
  commit: string | null;
  buildTime: string | null;
} {
  // `typeof` 保护：vitest 直接执行源码时 define 未生效，不抛 ReferenceError。
  const version = typeof __THREEC_PRODUCT_VERSION__ !== 'undefined'
    ? injected(__THREEC_PRODUCT_VERSION__) : null;
  const commit = typeof __THREEC_GIT_COMMIT__ !== 'undefined'
    ? injected(__THREEC_GIT_COMMIT__) : null;
  const buildTime = typeof __THREEC_BUILD_TIME__ !== 'undefined'
    ? injected(__THREEC_BUILD_TIME__) : null;
  return { version, commit, buildTime };
}

function short(sha: string | null): string | null {
  return sha ? sha.slice(0, 7) : null;
}

/**
 * 汇总 build provenance（纯读取，确定性，无副作用）。
 * 每次调用重新计算 —— 数据量极小（几个字符串），无需缓存。
 */
export function buildProvenance(): BuildProvenance {
  const { version, commit, buildTime } = readInjected();

  const exp = timelineExportJson as unknown as {
    timeline_export_version?: unknown;
    source_commit?: unknown;
    generated_at?: unknown;
    campaigns?: unknown[];
    research_candidates?: unknown[];
  };
  const exportSourceCommit = asStringOrNull(exp.source_commit);

  const campaigns = Array.isArray(exp.campaigns) ? exp.campaigns.length : null;
  const researchCandidates = Array.isArray(exp.research_candidates)
    ? exp.research_candidates.length : null;

  const sa = saArtifactJson as unknown as {
    artifact_version?: unknown;
    rule_set_version?: unknown;
  };
  const to = toArtifactJson as unknown as { artifact_version?: unknown };

  return {
    productVersion: version,
    gitCommit: commit,
    gitCommitShort: short(commit),
    buildTime,
    exportVersion: asStringOrNull(exp.timeline_export_version),
    exportSourceCommit,
    exportSourceCommitShort: short(exportSourceCommit),
    exportGeneratedAt: asStringOrNull(exp.generated_at),
    exportObjectCounts:
      campaigns !== null && researchCandidates !== null
        ? { campaigns, researchCandidates }
        : null,
    // artifact_version 在 export 侧是字符串、在 SA 侧是数字 0.5 —— 统一转字符串展示
    saArtifactVersion: asStringOrNull(
      typeof sa.artifact_version === 'number'
        ? String(sa.artifact_version)
        : sa.artifact_version,
    ),
    saRuleSetVersion: asStringOrNull(sa.rule_set_version),
    toArtifactVersion: asStringOrNull(
      typeof to.artifact_version === 'number'
        ? String(to.artifact_version)
        : to.artifact_version,
    ),
  };
}

/** 展示用「未标注」占位（**不猜测**，与 `UNKNOWN` 语义一致）。 */
export const PROVENANCE_NOT_AVAILABLE = '未标注';
