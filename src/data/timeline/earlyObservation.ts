/**
 * earlyObservation.ts —— 「启动前观察」的**只读消费层**（ThreeC 1.2 · Usage-Driven）。
 *
 * ## 来源与规范
 *
 * - 数据：`research/research/reports/early_observation_v0_2.json`（Research-only 只读产物）
 * - 设计：`docs/DESIGN_EARLY_OBSERVATION_v0_2.md`
 * - 规范：`AGENTS.md` §5.1「Product 允许消费」清单中**正式指定**的 Product-facing artifact
 *
 * ## ★★ 分层（按**选择偏差的性质**分，不是按内容分）
 *
 * | 层 | 对象 | 选择偏差 | 可否与当前并列 |
 * |---|---|---|---|
 * | **L1 市场层** | 基准指数 `SH000300` | **无**（指数不是选出来的） | ✅ 可以 |
 * | **L2 标的层** | campaign 已登记标的 | **有**（**事后选定**） | ❌ 不可 |
 * | L3 当前对象→标的 | — | — | **不做**（会事实上成为个股清单） |
 *
 * ## ★★★ 三条硬约束
 *
 * 1. **不做「像不像」** —— 只有事实，无相似度 / 匹配 / 命中 / 概率 / 评分 / 排序。
 * 2. **全部 ex-ante** —— 每个检查点只用它当日及之前的数据。
 * 3. ★ **当前市场状态不与任何具体 campaign 并列** ——
 *    在某条 campaign 的面板里同时摆「它启动前」与「现在」，等于替使用者摆好像不像的题面。
 *    因此 `currentMarketOf()` 只供**全局位置**使用，`earlyObservationOf()` **不含**当前状态。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

import earlyJson from '@observation/early_observation_v0_2.json';
import exportJson from '@exports/timeline_export_v1.json';

/** 单点的观测量（`relStrength20` 仅 L2 有 —— L1 相对自身恒为 0，故不输出） */
export interface EarlyObservationPoint {
  date: string;
  close: number | null;
  /** 当日成交量在过去 60 个交易日中的分位（0–1） */
  volPct60: number | null;
  /** 过去 20 个交易日收益率（%） */
  ret20Pct: number | null;
  /** ret_20 − 基准同期收益（百分点）；L1 为 null */
  relStrength20: number | null;
  /** 20 日已实现波动率 / 60 日已实现波动率 */
  volRatio: number | null;
  aboveMa20: boolean | null;
  aboveMa60: boolean | null;
}

export interface EarlyObservationCheckpoint extends EarlyObservationPoint {
  /** 启动前 N 个交易日 */
  tMinus: number;
}

export interface EarlyObservationMarketLayer {
  seriesId: string;
  checkpoints: EarlyObservationCheckpoint[];
  atLastDay: EarlyObservationCheckpoint | null;
  note: string;
}

export interface EarlyObservationSecurity {
  securityId: string;
  securityName: string | null;
  atLastDay: EarlyObservationPoint | null;
  series: EarlyObservationPoint[];
}

export interface EarlyObservationSecurityLayer {
  securities: EarlyObservationSecurity[];
  /** 跨标的中位数（**辅助口径**，非主口径） */
  medianAtLastDay: {
    volPct60: number | null;
    ret20Pct: number | null;
    relStrength20: number | null;
    volRatio: number | null;
  } | null;
  /** ★ 偏差警告：标的是事后选定的，不得与当前并列 */
  biasNote: string;
}

export interface EarlyObservationView {
  campaignId: string;
  status: string;
  marketLayer: EarlyObservationMarketLayer | null;
  securityLayer: EarlyObservationSecurityLayer | null;
}

/** 当前市场状态（**仅供全局位置使用**，不得挂在具体 campaign 旁） */
export interface CurrentMarketView {
  seriesId: string;
  asOf: string | null;
  observables: EarlyObservationPoint | null;
  note: string;
}

const ARTIFACT = earlyJson as unknown as {
  by_campaign?: Record<string, RawRow>;
  current_market?: RawCurrent;
  rules?: { checkpoints_t_minus?: number[] };
};

/** ★ L3 未建的原因（Research 侧原样透传，去 Markdown 强调符） */
export const EARLY_OBSERVATION_L3_NOTE: string = (
  (ARTIFACT as unknown as { layers?: { L3_current_to_security?: { why?: string } } }).layers
    ?.L3_current_to_security?.why ?? ''
).replace(/\*\*/g, '');

interface RawPoint {
  date?: string;
  close?: number;
  vol_pct60?: number;
  ret_20_pct?: number;
  rel_strength_20?: number;
  vol_ratio?: number;
  above_ma20?: boolean;
  above_ma60?: boolean;
  t_minus?: number;
}
interface RawSecurity {
  security_id?: string;
  status?: string;
  series?: RawPoint[];
  at_last_day?: RawPoint;
}
interface RawMarketLayer {
  series_id?: string;
  checkpoints?: RawPoint[];
  at_last_day?: RawPoint;
  note?: string;
}
interface RawSecurityLayer {
  per_security?: RawSecurity[];
  median_series?: RawPoint[];
  bias_note?: string;
}
interface RawRow {
  campaign_id?: string;
  status?: string;
  market_layer?: RawMarketLayer;
  security_layer?: RawSecurityLayer;
}
interface RawCurrent {
  series_id?: string;
  as_of?: string;
  observables?: RawPoint;
  note?: string;
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
 * 取某个历史对象的「启动前观察」（**只含 L1 市场层 + L2 标的层**）。
 *
 * ★ **不含当前市场状态** —— 见文件头约束 3。
 *
 * @returns 视图模型；artifact 中没有该对象时返回 `null`（**不推断、不造默认值**）
 */
export function earlyObservationOf(campaignId: string): EarlyObservationView | null {
  const row = ARTIFACT.by_campaign?.[campaignId];
  if (!row) return null;

  const ml = row.market_layer;
  const marketLayer: EarlyObservationMarketLayer | null = ml
    ? {
        seriesId: ml.series_id ?? 'SH000300',
        checkpoints: (ml.checkpoints ?? [])
          .map((x) => {
            const base = pt(x);
            return base && x.t_minus !== undefined ? { ...base, tMinus: x.t_minus } : null;
          })
          .filter((x): x is EarlyObservationCheckpoint => x !== null),
        atLastDay: (() => {
          const base = pt(ml.at_last_day);
          return base && ml.at_last_day?.t_minus !== undefined
            ? { ...base, tMinus: ml.at_last_day.t_minus }
            : null;
        })(),
        note: ml.note ?? '',
      }
    : null;

  const sl = row.security_layer;
  const securities: EarlyObservationSecurity[] = (sl?.per_security ?? [])
    .filter((s) => s.security_id && s.status === 'OK')
    .map((s) => ({
      securityId: s.security_id as string,
      securityName: SECURITY_NAME[s.security_id as string] ?? null,
      atLastDay: pt(s.at_last_day),
      series: (s.series ?? []).map((x) => pt(x)).filter((x): x is EarlyObservationPoint => x !== null),
    }));
  const ms = sl?.median_series ?? [];
  const lastMed = ms.length ? ms[ms.length - 1] : undefined;
  const securityLayer: EarlyObservationSecurityLayer | null = sl
    ? {
        securities,
        medianAtLastDay: lastMed
          ? {
              volPct60: lastMed.vol_pct60 ?? null,
              ret20Pct: lastMed.ret_20_pct ?? null,
              relStrength20: lastMed.rel_strength_20 ?? null,
              volRatio: lastMed.vol_ratio ?? null,
            }
          : null,
        biasNote: (sl.bias_note ?? '').replace(/\*\*/g, ''),
      }
    : null;

  return {
    campaignId: row.campaign_id ?? campaignId,
    status: row.status ?? 'NO_DATA',
    marketLayer,
    securityLayer,
  };
}

/**
 * 取**当前**市场状态。
 *
 * ★★ **仅供全局位置使用** —— **不得**渲染在某条历史 campaign 的详情里：
 * 把「它启动前」与「现在」摆在同一张卡片，等于替使用者摆好「像不像」的题面。
 */
export function currentMarketOf(): CurrentMarketView | null {
  const c = ARTIFACT.current_market;
  if (!c) return null;
  return {
    seriesId: c.series_id ?? 'SH000300',
    asOf: c.as_of ?? null,
    observables: pt(c.observables),
    note: (c.note ?? '').replace(/\*\*/g, ''),
  };
}
