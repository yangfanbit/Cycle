/**
 * ★★ 经验概率（empirical probability）—— ThreeC 1.3 / v0.9 首个概率层。
 *
 * ## 这个模块是什么
 *
 * 把**已冻结的跨年份历史结果**换算成「历史结果分布」与「二元目标的经验比例」，
 * 并给出 **95% Wilson 区间**。它是**历史统计描述**，不是预测模型。
 *
 * ## 这个模块**不是**什么（口径红线）
 *
 * - 不是「已验证的未来概率」—— 没有经过任何预测模型校准；
 * - 不是「结构对应」—— 结构对应唯一入口仍是冻结 SA 解释；
 * - 不做评分 / 排名 / 推荐 / 买卖信号。
 *
 * ## 三条硬规则（全部由测试钉死）
 *
 * 1. **分母只算完整可比较的观察**：`comparable === true`。
 *    `partial` / 不可比 / 缺数据的年份**逐条列出并说明原因**，
 *    **不得**默默计入成功或失败。
 *    ★ `ThemeAnnualRow.comparableYears` **不能**当分母 —— 它只数「含历史窗口的年份」。
 * 2. **结果定义来自原数据**：`outcome` 码与 `outcome_rule` 原样引用，不重新判定。
 * 3. **样本小 → 区间宽**：n 小的时候 Wilson 区间会自然变宽，**不得**用点估计冒充精度。
 *
 * ## 为什么用 Wilson 而不是正态近似
 *
 * n = 7、k = 1 时正态近似给出 `0.143 ± 0.26` → 下界为负，且小样本覆盖很差。
 * Wilson 区间在 n 小、k 接近 0 或 n 时仍落在 [0,1] 内，覆盖率更接近名义水平。
 */

import type {
  CrossYearComparison,
  CrossYearYear,
  HistoricalEventsDoc,
} from './historicalEventMaps';

/* ============================================================== 区间 */

export interface WilsonInterval {
  /** 下界（0–1） */
  low: number;
  /** 上界（0–1） */
  high: number;
  /** 使用的分位数（1.96 = 95%） */
  z: number;
}

/**
 * Wilson score interval（比例置信区间）。
 *
 * @param successes 成功数 k
 * @param n         分母（**必须**是完整可比较观察数）
 * @param z         正态分位数（默认 1.96 → 95%）
 * @returns n <= 0 时返回 `null`（**不得**返回 [0,1] 冒充「有结论」）
 */
export function wilsonInterval(successes: number, n: number, z = 1.96): WilsonInterval | null {
  if (!Number.isFinite(n) || n <= 0) return null;
  const k = Math.min(Math.max(successes, 0), n);
  const p = k / n;
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const center = (p + z2 / (2 * n)) / denom;
  const half = (z / denom) * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n));
  return {
    low: Math.max(0, center - half),
    high: Math.min(1, center + half),
    z,
  };
}

/* ============================================================== 目标定义 */

/**
 * 二元目标的**显式定义**（目标 / 样本范围 / 观察期限 / 分母 / 排除规则全部写明）。
 *
 * ★ 这些字段不是装饰：没有它们，一个比例就没有意义（1/7 到底在数什么？）。
 */
export interface EmpiricalTarget {
  /** 稳定 id（用于测试与追溯，如 `power-summer-up`） */
  id: string;
  /** 人类可读的目标名 */
  label: string;
  /** 算作「成功」的 `outcome` 码（来自源数据码表，**不改写**） */
  successOutcomes: string[];
  /** ★ 原样引用的判定规则（源数据 `outcome_rule`） */
  outcomeRule: string;
  /** 观察窗口（源数据 `season_window`） */
  windowLabel: string;
  /** 标的池（源数据 `target_pool`） */
  poolLabel: string;
}

/** 被排除在分母之外的年份（**必须**逐条展示，不得只给一个数字） */export interface ExcludedYear {
  year: number;
  seasonLabel?: string;
  /** 源数据里的可比性取值（`partial` / `false` / 缺失 → `'unrecorded'`） */
  comparable: string;
  coverage?: string;
  /** 排除原因（源数据 `comparable_reason` 原文，不重写） */
  reason?: string;
}

/** 落在分母内、且判定为「成功」的年份明细（用于核对，不是结论） */
export interface SuccessYear {
  year: number;
  seasonLabel?: string;
  outcome: string;
  eventType?: string;
  inWindowEvent?: boolean;
  driver?: string;
}

/** 分母内的结果分布（一类一行） */
export interface OutcomeBucket {
  outcome: string;
  count: number;
  /** count / denominator；denominator = 0 时为 0 */
  rate: number;
}

/** 分母内的机制分布（区分「价格结果」与「事件机制」） */
export interface MechanismBucket {
  eventType: string;
  count: number;
  /** 该机制下判定为成功的年份数 */
  successCount: number;
}

export interface EmpiricalEstimate {
  target: EmpiricalTarget;
  /** ★ 分母 = `comparable === true` 的年份数 */
  denominator: number;
  successes: number;
  /** 点估计 k/n（分母为 0 时为 `null` —— **不得**用 0 冒充「从未发生」） */
  rate: number | null;
  wilson: WilsonInterval | null;
  /** 参与分母的年份（升序） */
  sampleYears: number[];
  successYears: SuccessYear[];
  /** 被排除的年份（逐条带原因） */
  excluded: ExcludedYear[];
  distribution: OutcomeBucket[];
  mechanismSplit: MechanismBucket[];
}

/* ============================================================== 计算 */

function seasonLabelOf(y: CrossYearYear): string | undefined {
  return y.season_label ?? undefined;
}

/** 源数据里的可比性 → 展示用字符串（缺失 → `unrecorded`，**不猜成 false**） */
export function comparableCodeOf(y: CrossYearYear): string {
  if (y.comparable === true) return 'true';
  if (y.comparable === 'partial') return 'partial';
  if (y.comparable === false) return 'false';
  return 'unrecorded';
}

/**
 * ★★ 核心：按**完整可比较**观察计算经验比例。
 *
 * 分母口径：只收 `comparable === true`。
 * 其余（`partial` / `false` / 未记录）一律进 `excluded`，并带上源数据给出的原因。
 */
export function computeEmpiricalEstimate(
  years: readonly CrossYearYear[],
  target: EmpiricalTarget,
): EmpiricalEstimate {
  const usable = years.filter((y) => y.comparable === true);
  const excluded: ExcludedYear[] = years
    .filter((y) => y.comparable !== true)
    .map((y) => ({
      year: y.year,
      seasonLabel: seasonLabelOf(y),
      comparable: comparableCodeOf(y),
      coverage: y.coverage,
      reason: y.comparable_reason,
    }))
    .sort((a, b) => a.year - b.year);

  const sampleYears = usable.map((y) => y.year).sort((a, b) => a - b);
  const denominator = usable.length;

  const successYears: SuccessYear[] = usable
    .filter((y) => target.successOutcomes.includes(y.outcome))
    .map((y) => ({
      year: y.year,
      seasonLabel: seasonLabelOf(y),
      outcome: y.outcome,
      eventType: y.event_type,
      inWindowEvent: y.in_window_event,
      driver: y.driver,
    }))
    .sort((a, b) => a.year - b.year);
  const successes = successYears.length;

  // 分布（只统计分母内；未知码原样保留，不合并、不猜）
  const counts = new Map<string, number>();
  for (const y of usable) counts.set(y.outcome, (counts.get(y.outcome) ?? 0) + 1);
  const distribution: OutcomeBucket[] = [...counts.entries()]
    .map(([outcome, count]) => ({
      outcome,
      count,
      rate: denominator > 0 ? count / denominator : 0,
    }))
    .sort((a, b) => b.count - a.count || a.outcome.localeCompare(b.outcome));

  // 机制分布（缺 `event_type` → 归到 `UNRECORDED`，**不猜**）
  const mech = new Map<string, { count: number; successCount: number }>();
  for (const y of usable) {
    const key = y.event_type ?? 'UNRECORDED';
    const cur = mech.get(key) ?? { count: 0, successCount: 0 };
    cur.count += 1;
    if (target.successOutcomes.includes(y.outcome)) cur.successCount += 1;
    mech.set(key, cur);
  }
  const mechanismSplit: MechanismBucket[] = [...mech.entries()]
    .map(([eventType, v]) => ({ eventType, ...v }))
    .sort((a, b) => b.count - a.count || a.eventType.localeCompare(b.eventType));

  return {
    target,
    denominator,
    successes,
    rate: denominator > 0 ? successes / denominator : null,
    wilson: wilsonInterval(successes, denominator),
    sampleYears,
    successYears,
    excluded,
    distribution,
    mechanismSplit,
  };
}

/* ============================================================== 目标构造（从源数据读，不硬编码结果） */

/**
 * ★★ 从题材文档构造**二元目标定义**。
 *
 * 关键：这里只读**定义**（`outcome_rule` / 窗口 / 标的池），**不读任何结果**。
 * 成功码固定为 `UP` —— 它是源数据 `outcome_rule` 里**严格定义**的那一类
 * （「全部上涨**且**全部跑赢基准」），不是「任意上涨」。
 *
 * ★ 缺 `outcome_rule` 时返回 `null`：没有判定规则的比例**没有意义**，
 *   宁可不展示，也不自己编一条规则。
 */
export function empiricalTargetOf(
  doc: HistoricalEventsDoc,
  cmp: CrossYearComparison,
): EmpiricalTarget | null {
  const c = (doc.cross_year_comparison ?? doc.cross_year) as Record<string, unknown> | undefined;
  const rule = typeof c?.outcome_rule === 'string' ? c.outcome_rule : undefined;
  if (!rule) return null;
  return {
    id: `${String(doc.artifact ?? 'events')}-up`,
    label: '窗口内标的池「全部上涨且全部跑赢基准」（源数据码 UP）',
    successOutcomes: ['UP'],
    outcomeRule: rule,
    windowLabel: cmp.season_window ?? cmp.window_basis ?? '（源数据未给出窗口）',
    poolLabel: cmp.target_pool ?? '（源数据未给出标的池）',
  };
}

/* ============================================================== 时间前推评估（D） */

export interface BaselineStep {
  /** 被预测的年份 */
  year: number;
  /** 训练用的历史年份（**严格早于**被预测年） */
  trainYears: number[];
  /** 训练集里的成功数 / 样本数 */
  trainSuccesses: number;
  trainN: number;
  /**
   * ★★ 评估用的**平滑**历史频率（Jeffreys：(k + 0.5) / (n + 1)）。
   *
   * 为什么不用原始 k/n：n = 3 且 k = 0 时原始频率 = **0**，
   * 一次未预料到的成功就会让 LogLoss 变成 `-log(1e-9) ≈ 20.7`，
   * 把整组结果**由一个样本主导**（实测电力 LogLoss 5.28 就是这么来的）。
   * ★ 这只是**评估基准**的平滑，不是对经验比例的修正 ——
   *   页面展示的 `k/n` 与 Wilson 区间**仍然是未平滑的原始值**。
   */
  predicted: number;
  /** 原始频率 k/n（**仅作参照**，不参与 Brier / LogLoss 计算） */
  rawFrequency: number;
  /** 实际结果（1/0） */
  observed: 0 | 1;
  brier: number;
  logLoss: number;
}

export interface CalibrationBin {
  /** 预测值区间 [low, high) */
  low: number;
  high: number;
  n: number;
  /** 该箱内的实际成功率；n = 0 时 `null` */
  observedRate: number | null;
  /** 该箱内的平均预测值；n = 0 时 `null` */
  meanPredicted: number | null;
}

export interface BaselineEvaluation {
  /** 目标定义 */
  targetId: string;
  /** ★ 评估基准的**显式定义**（读者必须能看出「这个 0.125 是怎么来的」） */
  baseline: {
    kind: 'JEFFREYS_SMOOTHED_FREQUENCY';
    label: string;
    alpha: number;
    beta: number;
  };
  /** 严格按时间顺序的逐步预测（**不得**随机拆分） */
  steps: BaselineStep[];
  /** 样本外步数 */
  n: number;
  /** 汇总 Brier（越小越好）；n = 0 → null */
  pooledBrier: number | null;
  /** 汇总 LogLoss；n = 0 → null */
  pooledLogLoss: number | null;
  /** 校准分箱（样本不足时为空数组，并给 `calibrationNote`） */
  calibration: CalibrationBin[];
  calibrationNote: string;
  /** 结论性说明（**只陈述事实**，不下研究判断） */
  note: string;
}

/** ★ Jeffreys 先验（Beta(0.5, 0.5)）—— **固定且事先声明**，不随数据调参 */
export const JEFFREYS_ALPHA = 0.5;
export const JEFFREYS_BETA = 0.5;

/** 评估基准的名称（UI 与文档共用同一句话） */
export const EVALUATION_BASELINE_LABEL =
  'Jeffreys 平滑历史频率（(k + 0.5) / (n + 1)，固定先验，不调参）';

/**
 * ★★ 评估用的平滑频率（Jeffreys）。
 *
 * @param successes 训练集成功数 k
 * @param n         训练集样本数
 * @returns `(k + 0.5) / (n + 1)` —— 恒在 (0,1) 内，n = 0 时为 0.5
 */
export function jeffreysFrequency(successes: number, n: number): number {
  const k = Math.max(0, successes);
  const m = Math.max(0, n);
  return (k + JEFFREYS_ALPHA) / (m + JEFFREYS_ALPHA + JEFFREYS_BETA);
}

/** 预测值裁剪（仅防御性；Jeffreys 已在 (0,1) 内，理论上不会触发） */
const EPS = 1e-9;
const clip = (p: number): number => Math.min(1 - EPS, Math.max(EPS, p));

/**
 * ★★ 时间前推（expanding window）基线评估。
 *
 * 规则：
 * - 只对 `comparable === true` 的年份评估，**按年份升序**；
 * - 第 i 步只用**严格早于**该年的年份训练（禁止未来信息泄漏）；
 * - 预测值 = 训练集的历史频率（**简单历史基准**，不含任何特征）；
 * - 前 `minTrain` 年只用于训练，不产生样本外预测。
 *
 * ★ 这不是「训练了一个模型」，而是**给未来的模型立一个必须打败的基准**。
 */
export function timeOrderedBaseline(
  years: readonly CrossYearYear[],
  target: EmpiricalTarget,
  opts: { minTrain?: number; bins?: number[] } = {},
): BaselineEvaluation {
  const minTrain = opts.minTrain ?? 3;
  const bins = opts.bins ?? [0, 0.2, 0.5, 0.8, 1.0000001];
  const usable = years
    .filter((y) => y.comparable === true)
    .slice()
    .sort((a, b) => a.year - b.year);

  const steps: BaselineStep[] = [];
  for (let i = minTrain; i < usable.length; i += 1) {
    const train = usable.slice(0, i);
    const trainSuccesses = train.filter((y) => target.successOutcomes.includes(y.outcome)).length;
    const rawFrequency = trainSuccesses / train.length;
    // ★ 评估用平滑频率（Brier / LogLoss 都基于这个**实际展示**的值）
    const predicted = jeffreysFrequency(trainSuccesses, train.length);
    const observed: 0 | 1 = target.successOutcomes.includes(usable[i].outcome) ? 1 : 0;
    const p = clip(predicted);
    steps.push({
      year: usable[i].year,
      trainYears: train.map((y) => y.year),
      trainSuccesses,
      trainN: train.length,
      predicted,
      rawFrequency,
      observed,
      brier: (predicted - observed) ** 2,
      logLoss: -(observed === 1 ? Math.log(p) : Math.log(1 - p)),
    });
  }

  const n = steps.length;
  const pooledBrier = n > 0 ? steps.reduce((s, x) => s + x.brier, 0) / n : null;
  const pooledLogLoss = n > 0 ? steps.reduce((s, x) => s + x.logLoss, 0) / n : null;

  const calibration: CalibrationBin[] = [];
  for (let b = 0; b < bins.length - 1; b += 1) {
    const low = bins[b];
    const high = bins[b + 1];
    const inBin = steps.filter((s) => s.predicted >= low && s.predicted < high);
    calibration.push({
      low,
      high,
      n: inBin.length,
      observedRate: inBin.length > 0
        ? inBin.reduce((s, x) => s + x.observed, 0) / inBin.length
        : null,
      meanPredicted: inBin.length > 0
        ? inBin.reduce((s, x) => s + x.predicted, 0) / inBin.length
        : null,
    });
  }

  const calibrationNote = n === 0
    ? '样本外步数为 0 —— 无法评估校准。'
    : n < 10
      ? `样本外仅 ${n} 步 —— 校准分箱**样本不足**，下表只作事实陈列，不足以判断校准好坏。`
      : `样本外 ${n} 步；分箱校准见下表。`;

  const note = n === 0
    ? `完整可比较年份 ${usable.length} 个，少于训练所需的最小样本（${minTrain} + 1），`
      + '**无法**做时间前推评估。'
    : `完整可比较年份 ${usable.length} 个 → 样本外预测 ${n} 步。`
      + `基准 = ${EVALUATION_BASELINE_LABEL}（无特征）。`
      + `Brier ${pooledBrier!.toFixed(3)} · LogLoss ${pooledLogLoss!.toFixed(3)}。`
      + '★ 这是**必须被超越的基准**，不是已交付的预测模型；'
      + '页面展示的 k/n 与 Wilson 区间**未做平滑**。';

  return {
    targetId: target.id,
    baseline: {
      kind: 'JEFFREYS_SMOOTHED_FREQUENCY',
      label: EVALUATION_BASELINE_LABEL,
      alpha: JEFFREYS_ALPHA,
      beta: JEFFREYS_BETA,
    },
    steps,
    n,
    pooledBrier,
    pooledLogLoss,
    calibration,
    calibrationNote,
    note,
  };
}

/* ============================================================== 模型可行性（D） */

/**
 * ★★ 预先声明的**样本外步数门槛**（不是统计检验，是工程门槛）。
 *
 * 理由：要判断「模型 vs 历史基准」的差异是否不是噪声，几十步都嫌少；
 * 当前每个题材只有 4–6 步 → 任何模型的 Brier 差异都会被单年结果主导。
 * ★ 这个数字**写死在这里**是有意的：门槛必须先定，再看数据，否则就是事后挑标准。
 */
export const MODEL_MIN_OUT_OF_SAMPLE_STEPS = 30;

/**
 * ★★ 预先声明的**事前特征数量门槛**。
 *
 * 一个只用「历史频率」的模型不是模型，是基准本身。
 * 要谈「训练模型」，至少要有几个**窗口开始前就可观测**的自变量
 * （如库存 / 来水 / 煤价 / 气温 / 政策日历），否则模型无法区分机制状态。
 * ★ 同样是先声明、后看数据。
 */
export const MODEL_MIN_EX_ANTE_FEATURES = 3;

export interface ModelFeasibility {
  targetId: string;
  outOfSampleSteps: number;
  requiredSteps: number;
  /** ★ 仅表示「步数达标」—— **不等于**可以训练 */
  stepsSufficient: boolean;
  /** 当前可用的**事前**特征数（窗口开始前可观测） */
  exAnteFeatureCount: number;
  requiredFeatures: number;
  /** ★ 仅表示「特征够用」 */
  featuresSufficient: boolean;
  /**
   * ★★ **是否具备训练条件** = 步数达标 **且** 特征够用。
   * ★ 不得用「步数达标」单独代表这个字段（v0.10 修正的正是这一点）。
   */
  sufficient: boolean;
  /** 事实陈述（不含建议措辞） */
  verdict: string;
  /** 还缺什么（数据缺口清单，逐条可核对） */
  missing: string[];
}

/**
 * 判断「现在能不能训练一个可信的预测模型」。
 *
 * ★★ v0.10 修正：原实现只比 `ev.n >= required`，于是「步数达标」被当成
 *   「已具备训练条件」—— 而现有数据**一个事前特征都没有**，那种「达标」毫无意义。
 *   现在把两件事**分开报**：`stepsSufficient` / `featuresSufficient`，
 *   `sufficient` 只在两者**同时**满足时为真。
 */
export function assessModelFeasibility(
  ev: BaselineEvaluation,
  opts: {
    required?: number;
    comparableYears?: number;
    /** 当前可用的事前特征数（默认 0 —— 现有数据确实没有） */
    exAnteFeatureCount?: number;
    requiredFeatures?: number;
  } = {},
): ModelFeasibility {
  const required = opts.required ?? MODEL_MIN_OUT_OF_SAMPLE_STEPS;
  const requiredFeatures = opts.requiredFeatures ?? MODEL_MIN_EX_ANTE_FEATURES;
  const exAnteFeatureCount = opts.exAnteFeatureCount ?? 0;

  const stepsSufficient = ev.n >= required;
  const featuresSufficient = exAnteFeatureCount >= requiredFeatures;
  const sufficient = stepsSufficient && featuresSufficient;

  const missing: string[] = [];
  if (!stepsSufficient) {
    missing.push(`样本外预测步数 ${ev.n} < 门槛 ${required}（缺 ${required - ev.n} 步）`);
  }
  if (!featuresSufficient) {
    missing.push(`可用**事前**特征 ${exAnteFeatureCount} 个 < 门槛 ${requiredFeatures} 个`
      + '（窗口开始前可观测：库存 / 来水 / 煤价 / 气温 / 政策日历等）'
      + '—— 现有数据只有结果，没有可用的事前自变量');
  }
  if ((opts.comparableYears ?? 0) > 0 && (opts.comparableYears ?? 0) < required) {
    missing.push(`完整可比较年份仅 ${opts.comparableYears} 个 —— 不足以覆盖多种机制状态`
      + '（如「有事件 / 无事件」「强基本面 / 弱基本面」的组合）');
  }
  missing.push('缺少**跨题材**样本（当前仅 2 个题材各自 7–9 个完整窗口）'
    + '—— 无法检验「同一规则换个题材还成立吗」');

  let verdict: string;
  if (sufficient) {
    verdict = `样本外步数 ${ev.n} ≥ ${required} 且事前特征 ${exAnteFeatureCount} ≥ ${requiredFeatures}`
      + ' —— 可以开始按时间前推训练并记录校准。';
  } else if (stepsSufficient) {
    verdict = `样本外步数 ${ev.n} 已达标（≥ ${required}），但**不具备训练条件**：`
      + `事前特征只有 ${exAnteFeatureCount} 个（需 ≥ ${requiredFeatures}）——`
      + '★ **步数达标 ≠ 可以训练**。';
  } else if (featuresSufficient) {
    verdict = `事前特征够用（${exAnteFeatureCount} 个），但样本外步数 ${ev.n} < 门槛 ${required}`
      + ' —— 仍**不训练**。';
  } else {
    verdict = `样本外步数 ${ev.n} < 门槛 ${required}，且事前特征 ${exAnteFeatureCount} 个`
      + `（需 ≥ ${requiredFeatures}）—— **不训练**预测模型；`
      + '保留经验基准概率，并把「还缺什么」写清楚。';
  }

  return {
    targetId: ev.targetId,
    outOfSampleSteps: ev.n,
    requiredSteps: required,
    stepsSufficient,
    exAnteFeatureCount,
    requiredFeatures,
    featuresSufficient,
    sufficient,
    verdict,
    missing,
  };
}

/* ============================================================== 文案常量 */

/** ★★ 唯一允许出现在本层的比例命名 —— 不得简写成「概率」或「未来概率」 */
export const EMPIRICAL_PROBABILITY_LABEL = '探索性经验基准概率';

/** 三类口径的标签（**必须**在 UI 上分开，不得混用） */
export const EVIDENCE_TIER_LABEL = {
  HISTORICAL_DESCRIPTION: '历史统计描述',
  EMPIRICAL_BASELINE: '经验基准概率（未校准）',
  VALIDATED_MODEL: '经验证的预测模型',
} as const;

export type EvidenceTier = keyof typeof EVIDENCE_TIER_LABEL;

/**
 * ★★ 本层的口径声明（UI 与导出共用）。
 *
 * ★ 措辞纪律：这里**不**写「未来上涨概率」「大概率」这类表述；
 *   只陈述「历史样本内比例 + 区间 + 尚未校准」。
 */
export const EMPIRICAL_PROBABILITY_DISCLAIMER =
  '★★ **这是历史样本内的比例，不是对未来窗口的预测**：'
  + '分母只含**完整可比较**的观察年份（`partial` / 不可比 / 缺数据的年份已逐条排除，见下表），'
  + '点估计旁的区间是 **95% Wilson 区间** —— 样本越小，区间越宽，'
  + '宽区间本身就说明「这个比例还不稳」。'
  + '本层**尚未**经过任何预测模型的训练与样本外校准，'
  + '因此只能称「**探索性经验基准概率**」，不得当作已验证的未来概率使用。';

/** 三层口径为什么必须分开（UI 上作为常驻说明） */
export const EVIDENCE_TIER_NOTE =
  '★★ 三层口径**互不等价**：① **历史统计描述** = 过去发生了什么（本区年份表）；'
  + '② **经验基准概率** = 把过去的结果折算成比例与区间（本区块）；'
  + '③ **经验证的预测模型** = 用事前特征、按时间前推、与基准比较并记录校准 —— '
  + 'ThreeC **目前没有**第 ③ 层。';

/** 「无法计算」的原因码（用于持续时间 / 时长的诚实展示） */
export const UNCOMPUTABLE_LABEL = {
  OPEN_INTERVAL: '开放区间（未记录结束日）',
  SINGLE_DAY: '单日锚点（起止同日）',
  MISSING_DATE: '缺日期',
  REVERSED: '起止倒置（源数据异常）',
  INVALID: '日期不可解析',
} as const;
