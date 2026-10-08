/**
 * earlyObservation.ts —— 「启动前观察」的**只读消费层**（ThreeC 1.2 · Usage-Driven）。
 *
 * ## 来源与规范
 *
 * - 数据：`research/research/reports/early_observation_v0_1.json`（Research-only 只读产物）
 * - 规范：`AGENTS.md` §5.1「Product 允许消费」清单中**正式指定**的 Product-facing artifact
 *
 * ## ★★ 这一层解决什么
 *
 * 核心链路声明 `… → 相关因素 → **提前观察** → 当前状态与历史结构对照`，
 * 但实测 export 里 `early_signal` **0 个 campaign 有值** —— 这一段**从未实现**。
 * 本模块呈现其中的**历史侧**：*该 Campaign 启动前 20 个交易日，K 线上长什么样。*
 *
 * ## ★★★ 红线（硬约束，不得违反）
 *
 * `AGENTS.md` §1 明令禁止 **概率 / 胜率 / 推荐分 / 预测**。因此本模块**只描述事实**：
 *
 * - ✅ 「启动前 20 个交易日，成交量分位 / 相对强度 / 波动率 / 均线位置分别是多少」
 * - ❌ 「出现这种形态后 N 日内上涨的概率」—— **不做**
 * - ❌ 任何评分 / 排序 / 档位 —— **不做**
 *
 * 全部观测量都是 **ex-ante**（只用当日及之前的数据），不引入未来信息。
 *
 * ## ★ 当前侧**无法对照**（如实呈现，不掩盖）
 *
 * 6 个当前研究对象**没有任何标的字段**，无法用同一套量计算「现在像不像」。
 * 因此设计文档设想的「历史 ↔ 当前并列呈现」**目前无法实现** ——
 * 需研究侧先决定「当前对象如何映射到标的」。本模块把这一点**明写进界面**。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

import earlyJson from '@observation/early_observation_v0_1.json';
import exportJson from '@exports/timeline_export_v1.json';

/** 单个标的在「启动前最后一日」的观测量 */
export interface EarlyObservationPoint {
  date: string;
  close: number | null;
  /** 当日成交量在过去 60 个交易日中的分位（0–1） */
  volPct60: number | null;
  /** 过去 20 个交易日收益率（%） */
  ret20Pct: number | null;
  /** ret_20 − 基准 SH000300 同期收益（百分点） */
  relStrength20: number | null;
  /** 20 日已实现波动率 / 60 日已实现波动率 */
  volRatio: number | null;
  aboveMa20: boolean | null;
  aboveMa60: boolean | null;
}

export interface EarlyObservationSecurity {
  securityId: string;
  securityName: string | null;
  /** 启动前最后一日 */
  atLastDay: EarlyObservationPoint | null;
  /** 启动前 20 个交易日的逐日序列（描述性） */
  series: EarlyObservationPoint[];
}

export interface EarlyObservationView {
  campaignId: string;
  status: 'OK' | 'PARTIAL' | 'NO_DATA' | 'NO_START';
  lookbackTradingDays: number;
  benchmark: string;
  securities: EarlyObservationSecurity[];
  /** 跨标的中位数（**辅助口径**，非主口径） */
  medianAtLastDay: {
    volPct60: number | null;
    ret20Pct: number | null;
    relStrength20: number | null;
    volRatio: number | null;
  } | null;
  /** 覆盖不足时的说明（原样透传 Research 的 notes） */
  notes: string[];
}

/** ★ 当前侧不可对照的原因（Research 侧 `scope.not_covered` 原样透传，仅去掉 Markdown 强调符） */
export const EARLY_OBSERVATION_SCOPE_NOTE: string = (
  (earlyJson as unknown as { scope?: { not_covered?: string } }).scope?.not_covered ?? ''
).replace(/\*\*/g, '');

const ARTIFACT = earlyJson as unknown as {
  by_campaign?: Record<string, RawRow>;
};
const RULES = earlyJson as unknown as { rules?: { window?: number } };

interface RawPoint {
  date?: string;
  close?: number;
  vol_pct60?: number;
  ret_20_pct?: number;
  rel_strength_20?: number;
  vol_ratio?: number;
  above_ma20?: boolean;
  above_ma60?: boolean;
}
interface RawSecurity {
  security_id?: string;
  status?: string;
  series?: RawPoint[];
  at_last_day?: RawPoint;
}
interface RawRow {
  campaign_id?: string;
  status?: string;
  lookback_trading_days?: number;
  benchmark?: string;
  per_security?: RawSecurity[];
  median_series?: RawPoint[];
  notes?: string[];
}

/** security_id → 中文名（**来自 canonical export**，产品不碰 research/database） */
const SECURITY_NAME: Record<string, string> = (() => {
  const out: Record<string, string> = {};
  const arr = (exportJson as { securities?: { security_id?: string; name?: string }[] }).securities ?? [];
  for (const s of arr) {
    if (s.security_id && s.name) out[s.security_id] = s.name;
  }
  return out;
})();

function pt(p: RawPoint | undefined): EarlyObservationPoint | null {
  if (!p || !p.date) return null;
  return {
    date: String(p.date),
    close: p.close ?? null,
    volPct60: p.vol_pct60 ?? null,
    ret20Pct: p.ret_20_pct ?? null,
    relStrength20: p.rel_strength_20 ?? null,
    volRatio: p.vol_ratio ?? null,
    aboveMa20: p.above_ma20 ?? null,
    aboveMa60: p.above_ma60 ?? null,
  };
}

/**
 * 取某个历史对象的「启动前观察」。
 *
 * @param campaignId canonical campaign_id（与 export 一致）
 * @returns 视图模型；artifact 中没有该对象时返回 `null`（**不推断、不造默认值**）
 */
export function earlyObservationOf(campaignId: string): EarlyObservationView | null {
  const row = ARTIFACT.by_campaign?.[campaignId];
  if (!row) return null;

  const securities: EarlyObservationSecurity[] = (row.per_security ?? [])
    .filter((s) => s.security_id && s.status === 'OK')
    .map((s) => ({
      securityId: s.security_id as string,
      securityName: SECURITY_NAME[s.security_id as string] ?? null,
      atLastDay: pt(s.at_last_day),
      series: (s.series ?? []).map((x) => pt(x)).filter((x): x is EarlyObservationPoint => x !== null),
    }));

  const m = (row.median_series ?? [])[row.median_series?.length ? row.median_series.length - 1 : 0];
  return {
    campaignId: row.campaign_id ?? campaignId,
    status: (row.status as EarlyObservationView['status']) ?? 'NO_DATA',
    lookbackTradingDays: row.lookback_trading_days ?? RULES.rules?.window ?? 20,
    benchmark: row.benchmark ?? 'SH000300',
    securities,
    medianAtLastDay: m
      ? {
          volPct60: m.vol_pct60 ?? null,
          ret20Pct: m.ret_20_pct ?? null,
          relStrength20: m.rel_strength_20 ?? null,
          volRatio: m.vol_ratio ?? null,
        }
      : null,
    notes: row.notes ?? [],
  };
}
