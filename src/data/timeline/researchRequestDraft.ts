/**
 * 用户研究请求**草稿**（Research Request Draft）—— ThreeC 1.3 · Usage-Driven。
 *
 * ## 这是什么 / 不是什么
 * 用户在「查一个方向」之后，可能想把这个方向**变成一次真正的研究请求**。
 * 本模块把用户的输入 + 覆盖查询结果整理成一份**可交接的草稿**（JSON / Markdown）。
 *
 * ★★ **草稿不是研究请求本身**：
 *   - **不生成**正式 ID（`URO-*` / `R<NN>-*` 均属 Research 侧签发，见
 *     `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` §9 与
 *     `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` §5）；
 *   - **不写库**、**不改** `current_candidates.json`、**不新增** Research Candidate / Campaign；
 *   - **不上传**（纯客户端字符串拼接，无网络、无 LLM）；
 *   - 必须经 **Human Review / Research 审查**后才可能成为正式任务。
 *
 * ## 语义边界（沿用 directionLookup，硬约束）
 * 「主题名命中 ≠ 结构对应」；「未覆盖 ≠ 结构上不存在对应」。
 * 本模块**只做字段整理与序列化**，不产生任何评分 / 排序 / 概率 / 推荐。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。localStorage 的读写由 UI 层负责（便于测试与降级）。
 */
import type { DirectionLookupResult } from './directionLookup';

/**
 * 冻结证据里的**一条命中**。
 *
 * ★★ `matchedOn` 的三种取值（v0.8）：
 *   - `string[]`（**当前**草稿）—— 真实匹配依据（主题名 / 大主题 / 标题），可解释、可核对；
 *   - `null`（**v0.7 及更早**的本机草稿）—— 当时**没有保存**该信息；
 *   - `[]` —— 理论上表示「上游确实没有依据」（当前 `lookupDirection` 总会给 ≥1 条）。
 * ★ **绝不**用 `[]` 冒充「没有依据」：缺少就是缺少，必须标「未保存该信息」。
 */
export interface CoverageHit {
  id: string;
  title: string;
  matchedOn: string[] | null;
}

/**
 * ★★ 与草稿**关联的那一次**覆盖查询的**冻结快照**（v0.7）。
 *
 * 为什么必须冻结：`result` 随用户每次查询而变，而草稿是独立 state。
 * v0.6 导出时直接取「当前 result」→ 用户先查「汽车」（草稿方向自动填「汽车」）再改查「医药」，
 * 导出的「覆盖查询证据」就变成**医药的**，而草稿内容还是汽车的 → **静默混合两份请求**。
 *
 * → 把「草稿成立时那一次查询」的证据**冻结**下来随草稿一起持久化：
 *   · 恢复草稿时能如实展示**原来的**证据（不是用新查询冒充）；
 *   · 用户换查询时能**披露**「证据已变」，而不是无声改绑。
 */
export interface LinkedCoverage {
  query: string;
  verdict: DirectionLookupResult['verdict'];
  current: CoverageHit[];
  historical: CoverageHit[];
  resolution: DirectionLookupResult['resolution'];
  captured_at: string;
}

/** 用户可填写的草稿字段（全部是**自然语言**，不做结构化推断） */
export interface ResearchRequestDraft {
  /** 方向（与查询一致；可编辑以细化，如「汽车 → 智能驾驶合规化」） */
  direction: string;
  /** 希望回答的**具体**研究问题（一行一条，允许空行） */
  researchQuestions: string;
  /** 为什么关注这个方向 */
  whyCare: string;
  /** 已知线索 / 来源（可选） */
  knownLeads: string;
  /** 希望调查的历史时间范围（如 2018-2025） */
  timeRange: string;
  /**
   * ★ 本草稿关联的**那一次**覆盖查询词（未关联 → ''）。
   *   它是「证据归属」的唯一依据 —— 与 `direction` **不要求相同**
   *   （用户可把方向细化为「智能驾驶合规化」而查询词仍是「汽车」）。
   */
  linkedQuery: string;
  /** 关联建立时间（ISO；未关联 → ''） */
  linkedAt: string;
  /** 关联的冻结证据（未关联 → null） */
  linkedCoverage: LinkedCoverage | null;
}

export const EMPTY_DRAFT: ResearchRequestDraft = {
  direction: '',
  researchQuestions: '',
  whyCare: '',
  knownLeads: '',
  timeRange: '',
  linkedQuery: '',
  linkedAt: '',
  linkedCoverage: null,
};

/** ★ 单字段长度上限：草稿是**交接线索**，不是论文；超长应引导用户分次提交 */
export const DRAFT_FIELD_MAX = 2000;

/** 草稿里的**纯文本**字段（关联字段是对象/时间，不参与「空不空」的文本判定） */
export type DraftTextField =
  | 'direction' | 'researchQuestions' | 'whyCare' | 'knownLeads' | 'timeRange';

/** 草稿必填项（缺了仍可导出，但会在 `missing` 里如实列出 —— 不阻塞、不伪造） */
export const DRAFT_REQUIRED_FIELDS: DraftTextField[] = ['direction', 'researchQuestions'];

export function isDraftEmpty(d: ResearchRequestDraft): boolean {
  return DRAFT_REQUIRED_FIELDS.every((k) => !d[k].trim())
    && !d.whyCare.trim() && !d.knownLeads.trim() && !d.timeRange.trim();
}

/** 草稿是否**完全**没有内容（含关联）—— 用于判断「这份记录值不值得保留」 */
export function isDraftBlank(d: ResearchRequestDraft): boolean {
  return isDraftEmpty(d) && !d.linkedQuery.trim() && d.linkedCoverage === null;
}

/** 缺哪些必填项（用于 UI 提示；**不**阻止导出 —— 草稿允许不完整） */
export function missingDraftFields(d: ResearchRequestDraft): string[] {
  return DRAFT_REQUIRED_FIELDS.filter((k) => !d[k].trim()).map((k) =>
    k === 'direction' ? '研究方向' : '希望回答的研究问题',
  );
}

/** 把多行文本拆成非空条目（保留原文顺序，去首尾空白） */
export function toLines(s: string): string[] {
  return s
    .split('\n')
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

/** 草稿 → 可交接载荷（**确定性**：同输入同输出，便于用户核对与 diff） */
export interface ResearchRequestPayload {
  kind: 'threec_research_request_draft';
  draft_version: '0.1' | '0.2' | '0.3';
  /** ★ 明确：草稿**没有**正式 ID —— 不伪造 URO / R 编号 */
  id: null;
  status: 'DRAFT_NOT_REVIEWED';
  review_required: true;
  generated_at: string;
  request: {
    /** 用户填写（或经用户确认自动填入）的方向 —— **请求原文** */
    direction: string;
    research_questions: string[];
    why_care: string;
    known_leads: string[];
    time_range: string;
  };
  /**
   * ★★ 请求原文 ↔ 查询证据的**关联事实**（v0.7）。
   *   只披露事实，**不做**相似度匹配、不判断「是否同一方向」、不评分。
   */
  linkage: {
    /** 本草稿的证据属于哪一次查询（未关联 → ''） */
    linked_query: string;
    /** 关联建立时间（未关联 → ''） */
    linked_at: string;
    /** 当前界面上的查询词（未查询 → ''） */
    current_query: string;
    /** 当前查询是否与关联查询不同（★ 只比字符串，不做语义归并） */
    changed: boolean;
    /** 证据来源：冻结快照 / 未关联 */
    evidence_source: 'frozen_snapshot' | 'none';
    /** ★ 关联证据不可用时为 true（读者不得把缺失当成「无对应」） */
    evidence_unavailable: boolean;
    note: string;
  };
  /**
   * 与覆盖查询的衔接。
   * ★★ `executed: false` 时 `verdict` 为 **null** —— v0.6 用默认值 `'none'` 会让读者
   *   把「没查过」误读成「查过、两侧都没覆盖」（两者字面完全相同）。
   */
  coverage_check: {
    executed: boolean;
    query: string;
    verdict: DirectionLookupResult['verdict'] | null;
    verdict_meaning: string;
    /** ★ `matched_on: null` = 旧草稿未保存该信息；`[]` = 上游确实无依据 */
    current_objects: { id: string; title: string; matched_on: string[] | null }[];
    historical_cases: { id: string; title: string; matched_on: string[] | null }[];
    resolution: DirectionLookupResult['resolution'];
  };
  /** 拟交接范围（对齐 intake 协议的 `task_scope`；**不含** `task_id` —— 由 Research 侧签发） */
  handoff: {
    intended_protocol: string;
    task_scope_sketch: {
      task_id: null;
      family_directions: string[];
      years: string;
      included_scope: string;
      excluded_scope: string;
    };
    drop_location: string;
    note: string;
  };
  /** 已知限制（必须在导出里出现，避免被当成结论） */
  known_limitations: string[];
  /** 本草稿做了什么 / 没做什么 */
  constraints: string[];
}

const VERDICT_MEANING: Record<DirectionLookupResult['verdict'], string> = {
  both: '当前与历史两侧都有覆盖 —— 可走完整工作流。',
  'current-only': '只有当前研究对象，历史侧没有命中 —— 历史结构对应可能为空。',
  'historical-only': '只有历史案例，当前侧没有研究对象 —— 无法回答「现在处于什么阶段」。',
  none: '两侧都未覆盖 —— 历史研究与当前研究对象里都没有命中。',
};

export const KNOWN_LIMITATIONS: string[] = [
  '★ 「主题名命中」**不等于**「结构对应」：命中的是主题名 / 标题，'
    + '真正的结构对应只由冻结 SA 解释给出。',
  '★ 「未覆盖」**不等于**「结构上不存在对应」：结构对应比的是机制 / 序列 / 事件结构，'
    + '一个历史里没有的方向，在建立当前研究对象后仍可能得到结构支持。',
  '★ 覆盖查询是**字符串匹配**，不做同义词 / 上位词推断，可能漏掉表述不同的同一方向。',
  '★ 本草稿由用户填写，**未经任何审查**；其中的「为什么关注」「已知线索」是用户主张，'
    + '不是已核实事实。',
  '★ 时间范围是**用户的期望**，与库内实际覆盖范围可能不一致（以覆盖查询结果为准）。',
];

export const DRAFT_CONSTRAINTS: string[] = [
  '本文件是**草稿**：未生成正式任务 ID，未写入数据库，未新增 Research Candidate / Campaign。',
  '必须经 Research 审查（Human Review）后才可能成为正式研究任务。',
  '纯客户端生成：未上传、无网络请求、无 LLM 参与。',
  // ★ 逐项否定：每项都紧邻否定词，便于人工与自动化检查（沿用项目既有约定）
  // ★ v0.9：项目已允许概率 / 预测研究，故此处**不再**写「不做预测」这种全局禁令；
  //   改为陈述「本草稿本身不含数值」，并要求概率类请求声明口径。
  '不含评分；不做排序；不构成任何买卖信号；本文件本身不含概率或预测数值'
    + '（若请求涉及历史频率 / 条件比例，须在正式研究中声明分母、样本与不确定性）。',
];

/**
 * 构造交接载荷。
 *
 * ★★ v0.7 关键语义：**证据只来自草稿自己冻结的那一次查询**（`draft.linkedCoverage`）。
 *   参数 `lookup` 是**当前界面**上的查询结果，**只**用于披露「当前查询已与关联查询不同」，
 *   **绝不**被当作本草稿的证据 —— 否则用户换了查询词就会把新证据静默贴到旧草稿上。
 *
 * @param draft   草稿（含 `linkedQuery` / `linkedAt` / `linkedCoverage`）
 * @param lookup  当前查询结果（可为 null）；**不作为证据**
 * @param now     生成时间（ISO；由调用方注入，便于测试确定性）
 */
export function buildResearchRequestPayload(
  draft: ResearchRequestDraft,
  lookup: DirectionLookupResult | null,
  now: string,
): ResearchRequestPayload {
  const direction = draft.direction.trim();
  const linkedQuery = draft.linkedQuery.trim();
  const currentQuery = (lookup?.query ?? '').trim();
  const frozen = draft.linkedCoverage;
  const executed = frozen !== null;

  return {
    kind: 'threec_research_request_draft',
    draft_version: '0.3',
    id: null,
    status: 'DRAFT_NOT_REVIEWED',
    review_required: true,
    generated_at: now,
    request: {
      direction,
      research_questions: toLines(draft.researchQuestions),
      why_care: draft.whyCare.trim(),
      known_leads: toLines(draft.knownLeads),
      time_range: draft.timeRange.trim(),
    },
    linkage: {
      linked_query: linkedQuery,
      linked_at: draft.linkedAt,
      current_query: currentQuery,
      // ★ 只做字符串比较（trim 后），**不做**语义归并 / 相似度 —— 事实披露，不是判断
      changed: Boolean(currentQuery) && currentQuery !== linkedQuery,
      evidence_source: executed ? 'frozen_snapshot' : 'none',
      evidence_unavailable: !executed,
      note: executed
        ? (Boolean(currentQuery) && currentQuery !== linkedQuery
          ? `★ 本草稿的证据属于查询「${linkedQuery}」；当前界面的查询是「${currentQuery}」，`
            + '**两者不同** —— 新查询结果**未**附加到本草稿。若要以新查询新建草稿，请用界面上的'
            + '「以当前查询新建草稿」。'
          : `本草稿的证据来自查询「${linkedQuery}」（${draft.linkedAt || '时间未记录'}）。`)
        : '★ 本草稿**未关联任何覆盖查询** —— 导出内容里没有查询证据。'
          + '这不代表「未覆盖」，只代表「没查过」（或原证据已不可恢复）。',
    },
    coverage_check: {
      executed,
      query: executed ? frozen!.query : '',
      verdict: executed ? frozen!.verdict : null,
      verdict_meaning: executed
        ? VERDICT_MEANING[frozen!.verdict]
        : '未执行覆盖查询 —— **无结论**（不是「未覆盖」，也不是「无有效对应」）。',
      current_objects: executed
        // ★★ v0.8：`matched_on` 透传真实依据；`null` = 旧草稿未保存该信息（**不得**用 [] 冒充）
        //   ★ `?? null` 也兜住「未过 normalizeDraft 的旧对象」（缺键 → null，而不是 undefined）
        ? frozen!.current.map((h) => ({
          id: h.id, title: h.title, matched_on: h.matchedOn ?? null,
        }))
        : [],
      historical_cases: executed
        ? frozen!.historical.map((h) => ({
          id: h.id, title: h.title, matched_on: h.matchedOn ?? null,
        }))
        : [],
      resolution: executed ? frozen!.resolution : null,
    },
    handoff: {
      intended_protocol: 'research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md',
      task_scope_sketch: {
        task_id: null, // ★ 由 Research 侧签发，草稿不得伪造
        family_directions: direction ? [direction] : [],
        years: draft.timeRange.trim(),
        included_scope: direction ? `与「${direction}」相关的历史周期与当前研究对象` : '',
        excluded_scope: '待 Research 界定（草稿不得自行缩小或扩大研究边界）',
      },
      drop_location: 'research/intake/packages/<task_id>/（task_id 由 Research 侧签发后确定）',
      note: '★ 本 sketch 仅供研究侧起草参考，**不构成**任务边界；'
        + '正式边界由 Research 依据 intake 协议与 CMTR 口径确定。',
    },
    known_limitations: KNOWN_LIMITATIONS,
    constraints: DRAFT_CONSTRAINTS,
  };
}

/**
 * 把一次**查询结果**冻结成草稿证据（纯函数）。
 * ★ 只保留 id / title / **matchedOn**（不复制全部字段）：证据是「查了哪个词、命中了哪些对象、
 *   各因什么命中」，具体解释仍以冻结 SA 为唯一入口。
 */
export function freezeCoverage(
  r: DirectionLookupResult,
  at: string,
): LinkedCoverage {
  return {
    query: r.query,
    verdict: r.verdict,
    current: r.current.map((h) => ({ id: h.id, title: h.title, matchedOn: [...h.matchedOn] })),
    historical: r.historical.map((h) => ({ id: h.id, title: h.title, matchedOn: [...h.matchedOn] })),
    resolution: r.resolution,
    captured_at: at,
  };
}

/**
 * ★★ v0.8：**一次性**建立一份「已关联当前查询」的完整草稿（纯函数）。
 *
 * v0.7 的「以当前查询新建草稿」只设了 `direction`，指望随后的自动回填 effect 补关联 ——
 * 而 effect 的守卫是 `isDraftBlank(draft)`：`direction` 非空 ⇒ 不 blank ⇒ **effect 不跑**
 * ⇒ **关联永远不建立**（导出仍显示「未关联任何查询」，SSR 渲染实测复现）。
 *
 * → 改为在此处**一次性**写入 `direction` + `linkedQuery` + `linkedAt` + `linkedCoverage`，
 *   **不依赖任何后续 effect**。自动回填与「新建草稿」共用它，避免两处漂移。
 */
export function buildLinkedDraft(
  query: string,
  r: DirectionLookupResult,
  at: string,
): ResearchRequestDraft {
  return {
    ...EMPTY_DRAFT,
    direction: query,
    linkedQuery: query,
    linkedAt: at,
    linkedCoverage: freezeCoverage(r, at),
  };
}

/** 渲染人类可读 Markdown（便于直接粘贴进 issue / 邮件 / 研究交接单） */
export function renderResearchRequestMarkdown(p: ResearchRequestPayload): string {
  const L: string[] = [];
  L.push('# ThreeC 研究请求草稿（**未经审查**）');
  L.push('');
  L.push('> ★ 这是**草稿**，不是正式研究任务：没有正式 ID、未入库、未新增研究对象。');
  L.push('> 需经 Research 审查后才可能成为正式任务。');
  L.push('');
  L.push(`- 生成时间：\`${p.generated_at}\``);
  L.push(`- 草稿版本：\`${p.draft_version}\` · 状态：\`${p.status}\``);
  L.push(`- 正式 ID：**未分配**（\`id: null\`）`);
  L.push('');
  L.push('## 1. 研究方向');
  L.push('');
  L.push(p.request.direction ? `**${p.request.direction}**` : '（未填写）');
  L.push('');
  L.push('## 2. 希望回答的研究问题');
  L.push('');
  if (p.request.research_questions.length === 0) L.push('（未填写）');
  for (const q of p.request.research_questions) L.push(`- ${q}`);
  L.push('');
  L.push('## 3. 为什么关注这个方向');
  L.push('');
  L.push(p.request.why_care || '（未填写）');
  L.push('');
  L.push('## 4. 已知线索 / 来源');
  L.push('');
  if (p.request.known_leads.length === 0) L.push('（未填写）');
  for (const k of p.request.known_leads) L.push(`- ${k}`);
  L.push('');
  L.push('## 5. 希望调查的历史时间范围');
  L.push('');
  L.push(p.request.time_range || '（未填写）');
  L.push('');
  L.push('## 6. 覆盖查询结果（工具侧事实）');
  L.push('');
  L.push(`- 本草稿**关联的查询词**：\`${p.linkage.linked_query || '（未关联任何查询）'}\``);
  L.push(`- 关联建立时间：\`${p.linkage.linked_at || '（未记录）'}\``);
  if (p.linkage.current_query) {
    L.push(`- 当前界面上的查询词：\`${p.linkage.current_query}\``
      + (p.linkage.changed ? ' —— ★ **与关联查询不同**，新查询结果**未**附加到本草稿' : ''));
  }
  L.push('');
  if (!p.coverage_check.executed) {
    L.push('★ **本草稿未关联任何覆盖查询** —— 因此**没有**查询证据可附。');
    L.push('  这不代表「未覆盖」，只代表「没查过」（或原证据已不可恢复）。');
    L.push('');
  } else {
    L.push(`- 查询词：\`${p.coverage_check.query}\``);
    L.push(`- 结论：**${p.coverage_check.verdict}** —— ${p.coverage_check.verdict_meaning}`);
    L.push(`- 当前研究对象命中 ${p.coverage_check.current_objects.length} 个`
      + (p.coverage_check.current_objects.length
        ? `：${p.coverage_check.current_objects.map((o) => `**${o.id}**（${o.title}）`
          + (o.matched_on === null
            ? '〔命中依据：未保存该信息（旧草稿）〕'
            : o.matched_on.length
              ? `〔命中：${o.matched_on.join(' / ')}〕`
              : '〔命中依据：无〕')).join('；')}`
        : ''));
    L.push(`- 历史案例命中 ${p.coverage_check.historical_cases.length} 个`
      + (p.coverage_check.historical_cases.length
        ? `：${p.coverage_check.historical_cases.map((o) => `**${o.id}**（${o.title}）`
          + (o.matched_on === null
            ? '〔命中依据：未保存该信息（旧草稿）〕'
            : o.matched_on.length
              ? `〔命中：${o.matched_on.join(' / ')}〕`
              : '〔命中依据：无〕')).join('；')}`
        : ''));
    if (p.coverage_check.resolution) {
      const r = p.coverage_check.resolution;
      L.push(`- 名称解析：${r.matchedTheme
        ? `库内主题「${r.matchedTheme.name}」${r.root && r.root.name !== r.matchedTheme.name ? `（属「${r.root.name}」）` : ''}，`
          + `该主题下直接挂靠对象 ${r.directObjectCount} 个；根下共 ${r.rootObjectCount} 个`
        : `不在库内主题表中（库内共 ${r.taxonomySize} 个主题）`}`);
    }
    L.push('');
  }
  L.push(`> ${p.linkage.note}`);
  L.push('');
  L.push('## 7. 已知限制（**请勿把本草稿当作结论**）');
  L.push('');
  for (const t of p.known_limitations) L.push(`- ${t}`);
  L.push('');
  L.push('## 8. 本草稿的边界');
  L.push('');
  for (const t of p.constraints) L.push(`- ${t}`);
  L.push('');
  L.push('## 9. 拟交接（仅供 Research 起草参考）');
  L.push('');
  L.push(`- 目标协议：\`${p.handoff.intended_protocol}\``);
  L.push(`- 拟放置位置：\`${p.handoff.drop_location}\``);
  L.push(`- \`task_id\`：**未分配**（由 Research 侧签发）`);
  L.push(`- 拟 family_directions：${p.handoff.task_scope_sketch.family_directions.join(' / ') || '（未填写）'}`);
  L.push(`- 拟 years：${p.handoff.task_scope_sketch.years || '（未填写）'}`);
  L.push(`- 说明：${p.handoff.note}`);
  L.push('');
  return L.join('\n');
}
