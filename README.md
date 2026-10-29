# ThreeC

**A股历史机会时间轴 / 历史机会地图**

> 看今天处于一年中的什么位置 → 看历史同期 → 看历史周期阶段 → 看当前研究对象 → 找历史结构对应 → 继续研究。

**ThreeC = Research + Cycle Product**

- **Research**：历史研究 / 数据生产 / Research Artifacts（`research/`）
- **Product**：Timeline / Current Lens / 历史比较呈现（`src/`）

> **产品目标 = 机会发现（长期方向，效果未验证）。**
> ThreeC 用于**发现值得进一步研究的 A 股题材线索** —— 把「今天在年内什么位置、历史上同期发生过什么、
> 当时的机制与参与标的如何」摊开，供使用者自己判断要不要继续研究。
> ★★ **其相对于常规研究方法的增量价值仍待验证**：ThreeC 目前**没有**做过对照实验，
> 也**没有**任何证据表明「用 ThreeC 找到的线索」优于「不用 ThreeC」。不要把「有这个功能」
> 读成「这个功能已被证明有用」。
> ThreeC 不负责基本面、技术面、个股选择、买卖时机或自动交易。

### 三层能力：已实现 / 待验证（不得混为一谈）

| 层 | 内容 | 当前状态 |
|---|---|---|
| ① **历史证据整理** | 历史事件 / 参与标的 / 时间窗口 / 来源与证据等级 / PIT 时点纪律 | ✅ **已实现**（可复算、有合同与测试） |
| ② **研究线索发现** | 季节性窗口、当前观察台、方向查询、外部线索核验、候选追踪 | ✅ **已实现**（机制与流程已落地）· ❌ **有效性未验证**（无对照实验，增量价值未知） |
| ③ **经过验证的预测能力** | 用事前特征、按时间前推、与基准比较并记录校准的模型 | ❌ **不存在**（样本外 4–6 步 << 门槛 30 步，事前特征 0 个） |

> ★ ② 里的「线索」是**研究起点**，不是结论，更不是「已被验证的发现」。
> ★ ③ 只有在**时间顺序验证 + 与简单历史基准比较 + 校准记录**全部具备后才算建立；当前**一项都没有**。


**明确不提供（Product 非目标）**：

- ❌ 不提供买卖信号 / 不自动交易
- ❌ 不选股 / 不荐股
- ❌ 不提供「没有口径的预测」/ 不提供「未经验证的概率」
- ❌ 不运行时联网 / 不做实时行情或资金异动监控

> ★★ **2026-10-18 规则调整（v0.9）**：原「不预测价格 / 不预测收益 / 不提供概率」已**撤销**。
> ThreeC **可以**研究历史频率、条件概率、阶段变化概率与未来窗口预测，但**必须**写明
> 预测目标 / 样本范围 / 观察期限 / 分母 / 排除规则 / 来源 / 不确定性，
> 并以**时间顺序**验证、与**简单历史基准**比较、记录**校准与误差**（见 `AGENTS.md` §3.1）。
>
> **三层口径分开**：① 历史统计描述 · ② **经验基准概率**（比例 + 95% Wilson 区间，**未校准**）·
> ③ 已验证预测模型（**目前没有**）。②**不得**写成「未来概率」。

---

## 当前状态

> ★ **本节 2026-10-25 重写（v0.44）** —— 上一版停在 **2026-10-20（v0.25）**，未反映其后的
> Market Snapshot 月度刷新（10-23 DRAFT）、历史事件 PIT 补证（v0.43 + v0.44 两批共 8 个事件）、
> 季节性「先筛选后检验」偏差修正（v0.40–v0.42）与首页数据瘦身（主包 −2.76 MB）。
> 以 `docs/PROJECT_STATE.md` 为准；下方「ThreeC 1.0 — RELEASED」小节保留（仍是事实），**不代表当前进度**。

截至 **2026-10-29**（行情与页面已刷新；标「实测」的行均为本轮或上轮实测值）：

| 项 | 当前基线 |
|---|---|
| Historical Universe | **89** Historical Objects（**62 Campaign** + 27 Research Candidate） |
| Macro Theme roots | **13**（DB `themes` 共 59 行） |
| Export Contract | **v1.2**（含 `macro_theme_root` + `taxonomy` 段） |
| Driver Canonicalization | **v0.4** |
| Structural Analogy | **v0.13**（**534** pairs · 规则集 `structural-analogy-ruleset-v0.3` **冻结未变**） |
| Time Observation | **v0.2**（内部 `artifact_version` 0.3） |
| Current Candidates | **6**（研究记录 **2026-10-23** · 每个对象带 `stage_review = REVIEWED_MAINTAINED` + 维持理由） |
| **Market Snapshot** | 索引 **15** 份 · **`MS-2026-10-13-01` = CANONICAL（已签发）** · **`MS-2026-10-23-01` = DRAFT（未签发，待人工审阅；未归档旧快照）** |
| **行情数据截止（按数据集分别标注，不得互相冒充）** | `history_scan.db` = **2026-10-29**（基准指数 / 行业板块 / 概念篮子 / 个股）· `market_data.db` = **2026-10-29**，但**只对 21 条当前前瞻序列**成立；其余 187 条停在各自事件窗口末（**设计如此，不追**）· **题材行情转写用 `adjusted` 前复权序列，本轮未动** |
| **历史市场角色（PIT）** | `historical_market_roles_v0_13` · **84 条角色**（报道点名 63 / 盘面异动 21）· 事件研究状态 **RESEARCHED_PIT 15 · DERIVED_FROM_REPORT 3 · DERIVED_FROM_MARKET 9 · NOT_RESEARCHED 6** · **「报道称龙头」仍 0** · `pit_safe_violations = 0` · ★ 6 个 `NOT_RESEARCHED` 均写明「为什么推不动」（证据形态不匹配 / 机制不同轴），**不是「没查」** |
| **季节性发现** | `pattern_discovery_v0_10` · as_of **20261023** · **1,300** 条（STRICT 893 / 探索 407）· 当前/下月窗口 **204** · 仅时点资格 **960** · 可报告样本外 **736** |
| **候选摘要** | `candidate_digest_v0_9` · **213** 张（G1 29 / G2 62 / G3 0 / G4 122） |
| 测试 | **1494 passed / 0 failed / 80 files**（2026-10-29 本地实测） |
| CI 门禁 | **Product**（`tsc -b` / `npm test` / `vite build`）+ **Research 只读**（`validate_db` · `validate_timeline_export` · intake · `refresh_downstream` · 题材行情一致性 · 参与者证据 · 涨停审计 · 角色 PIT · 前瞻观察 · 季节性）—— **全部只读，失败即不部署**；不新增 Job |
| **历史题材地图（v0.10–v0.16 · v0.25 · v0.43–v0.44）** | 首页**直接入口**：**8 题材 / 33 事件**（流感 6 · 电力 4 · 文化传媒 2 · 机器人 1 · 汽车智能化 6 · 半导体 / AI 算力 7 · 消费旺季 5 · 资源品 / 黄金·稀土 2）· 每题材含**历史参与标的索引**（关系性质分层）· 事件卡内可「查看对象详情」· **历史市场角色区块**按 PIT 口径展示：支持等级徽标 + **全部支持性来源**（发布主体 / 链接 / 发布日 / 来源组 / 层级）+ 独立来源组计数 · ★ 新题材窗口 = Campaign **主升段**，**不是**季节性月份窗口（不证明季节性规律） |
| 外部季节性日历 | **v0.2**（25 项外部线索 · **逐项核验**：处置 **MAPPED 1 · OBSERVING 13 · PARTIALLY_VALIDATED 2 · EXTERNAL_REFERENCE 9**（以产物 `verification_summary` 实测为准），**无一项**达到 `THREEC_VALIDATED`；原报告不在仓库 → 逐项写明 `report_available: false`，**没有一项声称读过原报告**）· **v0.12 起 25 条全部铺到 1–12 月时间轴**（23 条上轴 / 24 段窗口 / 跨年拆成 28 段 + 2 条无固定窗口单列）· **v0.13 起每条 MAPPED 线索可展开「外部月份窗口 × 该主题历史 MAIN_RISE 窗口」两层对照；UNMAPPED 线索可带入现有研究请求草稿** · **v0.14 起历史对象可一键「查看对象详情」（复用既有案例面板，返回不丢对照上下文），窗口计数改为「投影段数 / 去重对象数」可核对口径** · **v0.25 起**：每条线索显示**核验结论**（性质 / 依据 / 反例 / 下一步）；有地图 → 跳地图（10 条），无地图 → 「带入『研究方向』草稿」按钮（13 条，携带题材、原始窗口、外部来源**与 ThreeC 已有核验结论**），拒绝项（2 条）只给结论不给入口 |
| **经验基准概率（v0.9 新增 · 探索性，未校准）** | 电力 **1/7**（95% Wilson **2.6%–51.3%**）· 流感 **1/9**（**2.0%–43.5%**，唯一 UP 属 `UNKNOWN_PUBLIC_HEALTH`，**不是**流感驱动）· 均标「**未校准**」<br>★★ **就地说明**：**样本量** n=7 / n=9 = 各题材**完整可比较**的年份数（`partial` / 不可比年份已逐条排除并写原因）· **观察期限** 电力 每年 5/1–7/31、流感 秋冬季窗口（见事件卡「观察窗口」）· **分母范围 = 本题材在它自己这些年份里的窗口**，**不是**「所有可能题材（含从未成势方向）」的完整总体 → **不能**外推为「任意题材同期上涨的概率」，也**不能**当跨题材基准率 · **限制** ① n 小、区间极宽 ② 未做任何模型训练与样本外校准 ③ 价格结果 ≠ 机制成功 |
| **题材行情转写（v0.24 新增）** | 合同 `theme_market_performance_v2`（adjusted 收盘 · 窗口双端包含 · 至高点 = 窗口内最高收盘 · **回撤自至高点之后** · 超额 = 个股 − 基准 · 缺失给 `error+reason` · **v0.25 起** 非正价格 / >45% 单日跳变 → `invalid_price_series`）· 唯一入口 `research/scripts/build_theme_market_performance.py`（`--check` 只读 / `--write` 升版不覆盖）· 实测：**93/105 组数值可逐字段复现**，大基金三期 4 只标的各 **44** 个 adjusted 交易日（+61.4% ~ +101.3%，同期基准 **+16.8%**，`study_state` → `HAS_PRICE_DATA`，RC 仍 `INSUFFICIENT`）· **2026-10-25 `--check` 实测：题材 8 / 事件 33 / FAIL 0 / WARN 0** |
| 预测模型 | **未建立**（样本外 4–6 步 << 门槛 30，且 **0 个事前特征**）· 已交付 Jeffreys 平滑基线与可行性结论 |

### 季节性「源数据核验」与「CI 校验」是两条不同的边界（不得混说）

| 场景 | 实际做了什么 | **不能**宣称什么 |
|---|---|---|
| **本地（有 `history_scan.db`）** | `discover_seasonal_patterns_v0_5.py --check` 重算 **204 个当前窗口**的 `n_years` / 历史中位超额 / 命中率 / 历史层级 / 时点资格 / OOS 次数与分层，并与产物**逐字段比对** → 输出「**窗口指标核对**」 | 不是「完整产物逐字节复现」 |
| **CI（无该库 —— 1.3 GB 未入库）** | 显式打印 **`SKIP 源数据核对`**，只做结构不变量（protocol / criteria 阈值逐项 / `reconcile` 重算 / 分层加总 / 伪造标记） | **CI 通过 ≠ 源数据已重算** |
| **合成 SQLite 测试** | **30 用例（4 个跳过：依赖真实大库）**，覆盖 OOS 漂移 / 分层漂移 / **历史窗口指标漂移** / 伪造 `reconcile` | 合成库不能替代真实数据全量核对 |

> ★★ 另有一条口径纪律：`pit_eligible_years` 只是「按**当前**序列、只用该年之前数据取得的**统计**资格」，
> **不等于**当时的分类 / 成分 / 研究机会可得；当前成分回溯、历史分类变化、退市股缺失**不能**被 walk-forward 消除。

**当前阶段**：**ThreeC 1.3**（用户驱动研究 + 概率研究）—— v0.40–v0.44 是其中的
「研究可信度收口 + 历史证据覆盖」轮次：季节性「先筛选后检验」偏差已修正并落地为可复现流程
（高估 9.3pp 已量化并作废旧口径），历史事件 PIT 角色证据从 1 个事件扩到 9 个；
**预测模型仍未训练**（门槛未达）。R02 波次仍有 4 条 DEFER 待处置；粒度已裁定为「**机制段**」。
待人工决策的两项：`MS-2026-10-23-01` 是否签发；「负面点名」角色等级是否立项。

### ThreeC 1.0 — RELEASED（历史，仍是事实）

| 项 | 值 |
|---|---|
| **Version** | **`1.0.0`** |
| **Tag** | **`v1.0.0`**（annotated） |
| **Release commit** | **`064d39c`** |
| **Production** | **https://yangfanbit.github.io/Cycle/** |
| **Gate R / P / T / Q / U / M / D / G** | **全部 PASS** |
| **P0 / P1** | **0 / 0** |

> ✅ **ThreeC 1.0 已正式发布。**
> Research Core 冻结 · Product 1.0 已发布 · Deployment 已进入生产 · 8 个 Release Gate 全部 PASS。
> 后续版本（1.1+）只允许由真实 Product Usage 或明确 Research Question 触发，**不预设新功能**。

最新状态详见：

- `docs/PROJECT_STATE.md`（动态状态，以它为准）
- `docs/ROADMAP.md`（路线）
- `docs/THREEC_1_0_RELEASE_DEFINITION.md`（1.0 发布定义与 Gate）
- `docs/DEPLOYMENT_RUNBOOK.md`（部署 / 重建 / 回滚规程）

---

## 线上访问入口（Production · v1.0.0）

| 项 | 值 |
|---|---|
| **正式入口** | **https://yangfanbit.github.io/Cycle/** |
| **版本** | **`1.0.0`**（tag `v1.0.0`，release commit `064d39c`） |
| 宿主 | GitHub Pages（纯静态） |
| 部署 | GitHub Actions（`.github/workflows/deploy.yml`）· push `main` 自动构建 + 部署 |
| 研究预览 | https://yangfanbit.github.io/Cycle/?preview=1 |
| 示例 fixture | https://yangfanbit.github.io/Cycle/?candidates=example |

**构建溯源**：页面页脚「Build Provenance」可查本次线上 build 的
`Product version` / `构建 commit` / **Research export `source_commit`** / SA 版本 / TO 版本 ——
用于确认线上 build 与 Research artifact 的对应关系（Gate D7）。

部署与回滚规程：`docs/DEPLOYMENT_RUNBOOK.md`。

---

## 快速开始

### Product

需要 Node.js ≥18（CI 使用 Node 22）。

```bash
npm install
npm run dev
npm test
npx tsc -b
npm run build
```

默认运行的是静态 Product。

Research Preview：

```
http://localhost:5173/?preview=1
```

Current Candidate 示例 fixture：

```
http://localhost:5173/?candidates=example
```

**复现 GitHub Pages 子路径行为**（本地验证 `/Cycle/` 下的资源是否正确）：

```bash
GITHUB_ACTIONS=true npx vite build      # base 变为 /Cycle/
grep -oE '(src|href)="[^"]*"' dist/index.html   # 期望 /Cycle/assets/...
```

本地 `dev` / `preview` / `build` 默认 `base = /`，**不受子路径影响**。
规则与回滚方式见 `docs/DEPLOYMENT_RUNBOOK.md` §4。

### Research

需要 Python 3 + 标准库 sqlite3。

```bash
cd research
python scripts/validate_db.py
python scripts/validate_timeline_export.py
python scripts/validate_current_research.py
```

研究脚本与 Artifact 均要求可复现。

---

## 数据流

```
Research DB / Current Research
        ↓
Research Artifacts / canonical export
        ↓
Product Adapter
        ↓
Timeline / Current Lens / Calendar / Lifecycle
```

Product runtime 不联网、不调用 LLM。

---

## 仓库原则

- 一个 Git / 一个项目根
- 一个 canonical Research
- 一个 Product
- Research 与 Product 逻辑分层
- 不编造历史事实
- `PROVISIONAL ≠ VERIFIED`
- UNKNOWN / NOT_AVAILABLE 是合法状态
- 历史比较禁止 look-ahead
- 不为了“好看”放松研究门槛

接手顺序：

`AGENTS.md → docs/PROJECT_STATE.md → 按任务读取局部文档`
