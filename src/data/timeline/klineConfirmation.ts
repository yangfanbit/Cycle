/**
 * klineConfirmation.ts —— 「K 线证实状态」的**只读消费层**（ThreeC 1.2 · Usage-Driven）。
 *
 * ## 来源与规范
 *
 * - 数据：`research/research/reports/kline_confirmation_v0_1.json`（Research-only 只读产物）
 * - 规范：`AGENTS.md` §5.1「Product 允许消费」清单中**正式指定**的 Product-facing artifact
 *
 * ## ★★ 这一层解决什么
 *
 * 产品四个视角（Timeline · Lifecycle · Structural Analogy · 季节性地图）**全部读**
 * campaign 的 start / peak / end，但**此前没有任何机制对照过市场** —— 全都信任记录。
 *
 * 2026-10-08 用真实 K 线（原始价盘中最高）对照 49 个 campaign 后：**32 个被证实、17 个未被证实**。
 * 本模块把这件事**如实呈现**：记录峰值是否被**已登记标的**的价格高点证实。
 *
 * ## ★★★ 语义边界（硬约束，不得违反）
 *
 * **「未证实」≠「日期错误」。** 二者可以同时成立：
 * 记录峰值在 ±7 日内**有记录依据**（指数高点 / 商品价 / 行业价 / 政策事件），
 * 只是**没有任何已登记标的**在该周创出价格高点。
 *
 * 因此本模块：
 * - **只读** artifact，**不重算**任何峰值，**不改动**任何研究数据；
 * - **不做归类**：不替 evidence 打「这是猪价 / 这是政策」的标签 —— 只给**原文摘录**；
 * - **不含** score / ranking / probability / 预测 —— 只有「证实状态」与**原文依据**；
 * - 判断留给读者，结论留给研究侧。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

import confirmationJson from '@observation/kline_confirmation_v0_1.json';
import exportJson from '@exports/timeline_export_v1.json';

/** 证实状态（封闭集合） */
export type KlineConfirmationStatus =
  | 'CONFIRMED'
  | 'UNCONFIRMED'
  | 'NO_PEAK_RECORDED'
  | 'NO_DATA';

/** 记录峰值 ±N 日内的依据行（**原文**，不改写、不归类） */
export interface KlineEvidenceAnchor {
  kind: 'evidence' | 'event';
  date: string;
  type: string;
  excerpt: string;
  /** 摘录取自哪个字段（可追溯：`evidences.description` / `events.name`） */
  sourceField: string;
}

/** 展示用视图模型 */
export interface KlineConfirmationView {
  campaignId: string;
  status: KlineConfirmationStatus;
  statusLabel: string;
  /** 记录峰值（可能为 null —— 合法空状态） */
  recordedPeak: string | null;
  /** 最接近记录峰值的**已登记标的**（名字由 canonical export 解析） */
  nearest: {
    securityId: string;
    securityName: string | null;
    peakDate: string;
    deltaDays: number;
  } | null;
  /** 未证实时的记录依据（原文）；已证实或空状态时为 [] */
  anchors: KlineEvidenceAnchor[];
  /** 判定容差（自然日）—— 2026-10-08 用户明确：历史日期按**周**粒度即可 */
  toleranceDays: number;
  coverage: { securities: number | null; withData: number | null };
}

const STATUS_LABEL: Record<KlineConfirmationStatus, string> = {
  CONFIRMED: 'K 线已证实',
  UNCONFIRMED: 'K 线未证实',
  NO_PEAK_RECORDED: '记录未标注峰值',
  NO_DATA: '无行情数据',
};

interface RawNearest {
  security_id?: string;
  peak_date?: string;
  delta_days?: number;
}
interface RawAnchor {
  kind?: string;
  date?: string;
  type?: string;
  excerpt?: string;
  source_field?: string;
}
interface RawRow {
  campaign_id?: string;
  recorded?: { start?: string | null; peak?: string | null; end?: string | null };
  confirmation?: string;
  nearest?: RawNearest;
  evidence_anchors?: RawAnchor[];
  coverage?: { securities?: number | null; with_data?: number | null };
}
interface RawArtifact {
  summary?: Record<string, number>;
  rules?: { tolerance_days?: number };
  by_campaign?: Record<string, RawRow>;
}

const ARTIFACT = confirmationJson as unknown as RawArtifact;

/** 判定容差：**取自 artifact 原文**，不在产品侧硬编码 */
export const KLINE_TOLERANCE_DAYS: number = ARTIFACT.rules?.tolerance_days ?? 7;

/** 证实状态汇总（计数事实，非评分） */
export const klineConfirmationSummary: Record<string, number> = ARTIFACT.summary ?? {};

/** security_id → 中文名（**来自 canonical export**，产品不碰 research/database） */
const SECURITY_NAME: Record<string, string> = (() => {
  const out: Record<string, string> = {};
  const arr = (exportJson as { securities?: { security_id?: string; name?: string }[] }).securities ?? [];
  for (const s of arr) {
    if (s.security_id && s.name) out[s.security_id] = s.name;
  }
  return out;
})();

const KNOWN_STATUS: readonly string[] = ['CONFIRMED', 'UNCONFIRMED', 'NO_PEAK_RECORDED', 'NO_DATA'];

/**
 * ★ 未知状态**不得猜测**：若 artifact 出现本产品不认识的状态值，
 *   `status` 退化为 `NO_DATA`（本产品无法呈现该状态），
 *   但 `statusLabel` **原样显示 artifact 的取值**，以免信息丢失或误导。
 */
function resolveStatus(raw: string | undefined): { status: KlineConfirmationStatus; label: string } {
  const v = raw ?? 'NO_DATA';
  if (KNOWN_STATUS.includes(v)) {
    const s = v as KlineConfirmationStatus;
    return { status: s, label: STATUS_LABEL[s] };
  }
  return { status: 'NO_DATA', label: v };
}

/**
 * 取某个历史对象的 K 线证实状态。
 *
 * @param campaignId canonical campaign_id（与 export 一致）
 * @returns 视图模型；artifact 中没有该对象时返回 `null`（**不推断、不造默认值**）
 */
export function klineConfirmationOf(campaignId: string): KlineConfirmationView | null {
  const row = ARTIFACT.by_campaign?.[campaignId];
  if (!row) return null;

  const { status, label } = resolveStatus(row.confirmation);
  const n = row.nearest;
  const anchors: KlineEvidenceAnchor[] = (row.evidence_anchors ?? [])
    .filter((a) => a.date)
    .map((a) => ({
      kind: a.kind === 'event' ? 'event' : 'evidence',
      date: String(a.date),
      type: a.type ?? '',
      excerpt: a.excerpt ?? '',
      sourceField: a.source_field ?? '',
    }));

  return {
    campaignId: row.campaign_id ?? campaignId,
    status,
    statusLabel: label,
    recordedPeak: row.recorded?.peak ?? null,
    nearest:
      n && n.security_id && n.peak_date
        ? {
            securityId: n.security_id,
            securityName: SECURITY_NAME[n.security_id] ?? null,
            peakDate: n.peak_date,
            deltaDays: n.delta_days ?? 0,
          }
        : null,
    anchors,
    toleranceDays: KLINE_TOLERANCE_DAYS,
    coverage: {
      securities: row.coverage?.securities ?? null,
      withData: row.coverage?.with_data ?? null,
    },
  };
}
