# RESEARCH_PIPELINE_SAFETY.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **操作安全说明**（Research 管线） |
> | 日期 | 2026-10-07 |
> | 起因 | 一次**真实的误写事故**：试跑脚本时把产物写回了仓库 |

---

## 1. 事故经过（必须记录，否则会重演）

试跑 `build_structural_analogy_research_v0_5.py` 以验证「加一个候选会怎样」时，
**只重定向了「输入」路径，没有重定向「输出」路径** → 脚本**写回了仓库**的
`structural_analogy_research_v0_5.json` 与 `..._candidates_v0_5.csv`。

**已处理**：确认改动完全来自本次误写 → `git checkout --` 回退 → 验证工作树干净、冻结产物仍逐字节可复现。

### 两个根因（都已修）

| # | 根因 | 修法 |
|---|---|---|
| **1** | 脚本的**输出常量不止一个**（`OUT_JSON` + `OUT_CSV`），只 sed 一个不够 | 用 `sandbox_try.sh` 整体重定向（见 §3） |
| **2** | ★ **13 个脚本的 CSV 写入不在 `--check` 的保护范围内** → `--check` **不是真正的 dry-run** | 写入点内联：`io.open(os.devnull if CHECK else X, "w", ...)` |

> ★ 根因 2 是**真缺陷**，不只是我的操作失误：
> 任何人用 `--check` 都会以为「只检查、不写盘」，实际仍会写 CSV。

---

## 2. 现在的三重保护

| 保护 | 说明 |
|---|---|
| **`--check` 是真正的 dry-run** | 已修：`--check` 下**零写入**（实测 mtime 不变）。**试跑永远先跑 `--check`。** |
| **`THREEC_ROOT` 环境变量** | 设了它，**读写整体重定向**到该目录（22 个脚本已支持）。 |
| **`sandbox_try.sh`** | 自动建沙箱 + 跑 + **打印与仓库的产物差异**（见 §3）。 |

---

## 3. 安全试跑的标准做法

```bash
# ★ 推荐：用沙箱助手（仓库绝不被触碰）
research/scripts/sandbox_try.sh build_structural_analogy_research_v0_5.py
research/scripts/sandbox_try.sh build_structural_analogy_explanation_v0_5.py --check
```

助手会：
1. 复制 `research/` 与 `exports/` 到临时沙箱（**不复制** `.git` / `node_modules`）；
2. 以 `THREEC_ROOT=<沙箱>` 运行目标脚本；
3. **打印沙箱与仓库的产物差异** —— 有差异就说明「这次试跑会改动这些文件」；
4. 明确提示：**仓库未被改动**，要采纳须人工审阅后**显式**拷回。

**手工等价做法**（不想用助手时）：

```bash
SB=$(mktemp -d)/threec-sandbox && mkdir -p "$SB"
cp -R research "$SB/research" && cp -R exports "$SB/exports"
THREEC_ROOT="$SB" python3 "$SB/research/scripts/<脚本名>" [参数...]
diff -rq research/research/reports "$SB/research/research/reports"   # 看差异
```

---

## 4. 硬约束（不得违反）

1. **试跑先 `--check`**；要真跑就**必须**用沙箱（`THREEC_ROOT` 或助手）。
2. **不得**为了试跑而临时改仓库里的 canonical 输入（`current_candidates.json` 等）后忘记改回。
3. **冻结 artifact 不得就地编辑** —— 新内容一律**新版本**（`v0_5` → `v0_6`），旧版逐字节保留。
4. 沙箱产物**采纳前必须人工审阅差异**。

---

## 5. 相关（本轮一并修掉的）

- **`ROOT` 原本写死 Windows 路径 `D:/@AW/投资/ThreeC`**（22 个脚本）→
  在这台 Mac 上**整条管线跑不了**，与「Research 逐字节可复现」的声明相矛盾。
  已改为由 `__file__` 推导（可被 `THREEC_ROOT` 覆盖）；**已验证冻结产物仍逐字节复现**。

---

*Research 管线安全说明 · 2026-10-07*
