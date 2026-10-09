#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""make_research_handoff_sandbox.py —— 构建 Research Agent 交接沙箱。

## 为什么需要这个脚本（三条非显然的约束，踩过才知道）

1. **角色分离要求隔离**：`AGENTS.md` §3 / 协议 §3 —— Research Agent 只产出 package，
   **不得**接触 canonical 基座（DB · `exports/` · `src/` · `schema.sql`）。
   所以它的「操作空间」**不应**是仓库本身。

2. ★ **但沙箱必须复刻 `research/scripts/` 与 `research/intake/` 的相对结构** ——
   因为 `validate_historical_research_intake.py` 的根目录是**由脚本自身位置推导**的：
   ```python
   ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))   # <sandbox>/
   INTAKE_DIR = <sandbox>/research/intake
   ```
   **与 cwd 无关**。把校验器单独拷出来、或改变目录层级，它都会找不到 schema。

3. ★★ **`--check` 的 C02 硬编码 R01 manifest**（要求 `tasks` 恰为 `R01-01`…`R01-06`、
   `research_round_id == "R01"`）。所以沙箱**必须**带上
   `HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json`，否则新 Agent 跑 `--check` 必 FAIL ——
   而那份 manifest 与它的任务**毫无关系**，不解释清楚会让人以为环境坏了。

## 它产出什么

```text
<sandbox>/
├── 00_START_HERE.md              ← 交给新 Agent 的第一份文件（含自检命令）
├── EXISTING_UNIVERSE.md          ← 已有历史宇宙参照表（**只读**，供去重；不是研究结论）
├── research/
│   ├── intake/
│   │   ├── HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md
│   │   ├── HISTORICAL_UNIVERSE_COVERAGE_PLAN_v0_1.md
│   │   ├── historical_research_intake.schema.json
│   │   ├── HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json   （C02 需要，与任务无关）
│   │   ├── HISTORICAL_UNIVERSE_R02_TASK_MANIFEST_v0_1.json   （本任务 scope）
│   │   └── packages/
│   │       ├── R02-01/   ← 样例（只读参考）
│   │       └── R02-02/   ← 样例（只读参考）
│   └── scripts/
│       ├── validate_historical_research_intake.py
│       └── requirements.txt
└── docs/
    └── RESEARCH_AGENT_PROMPT_<TASK>.md
```

★ **新 Agent 唯一可写位置 = `<sandbox>/research/intake/packages/<TASK>/`**。

## 用法

    python research/scripts/make_research_handoff_sandbox.py --task R02-03
    python research/scripts/make_research_handoff_sandbox.py --task R02-03 --out ~/foo/bar
    python research/scripts/make_research_handoff_sandbox.py --task R02-03 --force

默认输出目录：`~/Aiworking/threec-<task 小写>-handoff/`（**仓库之外**，物理隔离）。

退出码：0 = 成功（含 `--check` 通过）；1 = 失败。
"""

import argparse
import io
import json
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INTAKE_DIR = os.path.join(ROOT, "research", "intake")
SCRIPTS_DIR = os.path.join(ROOT, "research", "scripts")
DOCS_DIR = os.path.join(ROOT, "docs")
EXPORT_PATH = os.path.join(ROOT, "exports", "timeline_export_v1.json")

# ★ 校验器解释器：系统 python3 缺 jsonschema → C25 必 FAIL（见 requirements.txt）
VENV_PY = "/Users/yangfan/.workbuddy-ai/binaries/python/envs/default/bin/python"

# 与任务无关、但 C02 硬编码要求存在的文件
R01_MANIFEST = "HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json"


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def copy_file(src, dst):
    if not os.path.isfile(src):
        raise SystemExit("缺少源文件：%s" % src)
    d = os.path.dirname(dst)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    shutil.copyfile(src, dst)


def find_manifest_for_task(task_id):
    """在 intake 目录里找到包含该 task_id 的 manifest。"""
    hits = []
    for name in sorted(os.listdir(INTAKE_DIR)):
        if not name.endswith(".json") or "TASK_MANIFEST" not in name:
            continue
        path = os.path.join(INTAKE_DIR, name)
        try:
            man = json.loads(read_text(path))
        except Exception:
            continue
        for t in man.get("tasks") or []:
            if isinstance(t, dict) and t.get("task_id") == task_id:
                hits.append((path, man, t))
    return hits


def build_existing_universe():
    """从 canonical export 生成**只读**参照表（供去重）。

    ★ 它**不是**研究结论、**不是**结构对应依据，只是「库里已有什么」的清单。
    """
    data = json.loads(read_text(EXPORT_PATH))
    campaigns = data.get("campaigns") or []
    rcs = data.get("research_candidates") or []

    # ★ 实测坑：**Campaign 在 export 里没有 `title` 字段**（只有 Research Candidate 有）。
    #   Campaign 的展示身份来自 `rule_id` → `rules[].name`。
    #   直接取 `title` 会得到一整列空白（已踩到并修正）。
    rule_name = {}
    for r in data.get("rules") or []:
        if isinstance(r, dict) and r.get("rule_id"):
            rule_name[r["rule_id"]] = r.get("name") or ""

    def label_of(obj):
        t = obj.get("title")
        if t:
            return str(t)
        rid = obj.get("rule_id")
        if rid and rule_name.get(rid):
            return "%s（%s）" % (rule_name[rid], rid)
        return "—"

    def themes_of(obj):
        out = []
        for t in obj.get("themes") or []:
            if isinstance(t, dict):
                out.append("%s(%s/%s)" % (t.get("name"), t.get("theme_type"), t.get("role")))
        return "、".join(out) if out else "—"

    def year_of(obj):
        s = obj.get("start") or obj.get("start_date") or ""
        return str(s)[:4] or "—"

    lines = []
    lines.append("# EXISTING_UNIVERSE.md —— 已有历史宇宙参照表（只读）\n")
    lines.append("> | 项 | 值 |")
    lines.append("> |---|---|")
    lines.append("> | 来源 | `exports/timeline_export_v1.json`（contract `%s` v%s） |"
                 % (data.get("contract"), data.get("timeline_export_version")))
    lines.append("> | source_commit | `%s` |" % str(data.get("source_commit"))[:7])
    lines.append("> | 规模 | %d Campaign + %d Research Candidate = **%d** |"
                 % (len(campaigns), len(rcs), len(campaigns) + len(rcs)))
    lines.append("> | 用途 | **仅供去重参照**（协议 §10 跨任务协调） |\n")
    lines.append("## ★★ 这份表**不能**用来做什么\n")
    lines.append("- ❌ 不能据它判断「某方向是否已有结构对应」——")
    lines.append("  `Theme / Name 相似 ≠ Structural Correspondence`（`AGENTS.md` §3）。")
    lines.append("- ❌ 不能据它判断「某方向已被覆盖所以不用做」—— 名字不在表里**才是**本任务的理由。")
    lines.append("- ❌ 它不是 canonical 写入依据；canonicalization 是 ThreeC Agent 的独有权限。\n")
    lines.append("## 它**能**用来做什么\n")
    lines.append("- ✅ 避免提交与既有对象**重复**的候选（若疑似重复，用 `possible_duplicate_of` 标注）。")
    lines.append("- ✅ 判断 `known_overlap`：你的方向与既有族/主题材在哪里交叉。\n")
    lines.append("---\n")
    lines.append("## Campaign（%d）\n" % len(campaigns))
    lines.append("| campaign_id | 起始年 | 名称（来自 `rules`） | 主题（name/type/role） |")
    lines.append("|---|---|---|---|")
    for c in sorted(campaigns, key=lambda x: str(x.get("start_date") or "")):
        lines.append("| `%s` | %s | %s | %s |"
                     % (c.get("campaign_id"), year_of(c),
                        label_of(c).replace("|", "／"), themes_of(c)))
    lines.append("\n## Research Candidate（%d）\n" % len(rcs))
    lines.append("| campaign_id | 起始年 | 标题 | 主题（name/type/role） |")
    lines.append("|---|---|---|---|")
    for c in sorted(rcs, key=lambda x: str(x.get("start_date") or "")):
        lines.append("| `%s` | %s | %s | %s |"
                     % (c.get("campaign_id"), year_of(c),
                        label_of(c).replace("|", "／"), themes_of(c)))

    # 主题材清单（供 overlap 判断）
    names = {}
    for c in list(campaigns) + list(rcs):
        for t in c.get("themes") or []:
            if isinstance(t, dict) and t.get("name"):
                names.setdefault(t["name"], 0)
                names[t["name"]] += 1
    lines.append("\n## 全部主题名（%d 个，按出现次数降序）\n" % len(names))
    lines.append("```text")
    for n, k in sorted(names.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append("%-28s %d" % (n, k))
    lines.append("```")
    lines.append("\n> ★ 你的四个方向（煤炭 / 电力 / 流感疫苗 / 文化传媒）")
    lines.append("> 在**这张表里一个都不出现** —— 这正是本任务存在的理由。")
    lines.append("\n---\n\n*由 `research/scripts/make_research_handoff_sandbox.py` 生成 · 只读参照*")
    return "\n".join(lines) + "\n"


def build_start_here(task_id, manifest_name, prompt_name, task_obj):
    directions = task_obj.get("macro_theme_candidates") or []
    return """# 00_START_HERE.md —— Research Agent 交接说明

> 本目录是你的**操作空间**。它是一份**精简沙箱**，只含完成 `{task}` 所需的文件。

---

## 一、你要读的四份文件（按顺序）

| # | 文件 | 作用 |
|---|---|---|
| 1 | `docs/{prompt}` | **任务 Prompt（先读这个）** |
| 2 | `research/intake/{manifest}` | **权威 scope**（与 Prompt 冲突时**以它为准**） |
| 3 | `research/intake/HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md` | 权威格式与纪律 |
| 4 | `research/intake/historical_research_intake.schema.json` | 机器可校验的字段定义 |

**样例包**（照它们的形状做，**不要修改它们**）：
`research/intake/packages/R02-01/` · `research/intake/packages/R02-02/`

**已有宇宙参照表**：`EXISTING_UNIVERSE.md` —— 只用于**去重**，
❌ **不得**据它判断「某方向已有结构对应」（名字相似 ≠ 结构对应）。

---

## 二、你**唯一**可以写的位置

```text
research/intake/packages/{task}/
```

**除此之外，不要修改、创建或删除任何文件。**
（本沙箱里其余文件都是只读参考资料。你在仓库外的独立副本上工作，改不到 canonical 基座。）

---

## 三、你的任务方向

{dirs}

★ 四个方向**各自独立成族**，必须分别给出 coverage 与 exclusions。

---

## 四、提交前**必须**跑自检

```bash
# 在**本目录**（沙箱根）执行 —— 校验器的根目录由脚本位置推导，与 cwd 无关
{venv} research/scripts/validate_historical_research_intake.py research/intake/packages/{task}

# 基础设施自检（可选）
{venv} research/scripts/validate_historical_research_intake.py --check
```

**必须贴出 `RESULT: PASS`。** 退出码 0 = 通过，1 = 存在 FAIL。

> ★★ 必须用上面这个解释器。**系统 `python3` 没装 `jsonschema`**，
> 会让 **C25（严格 JSON Schema）直接 FAIL** —— 而校验器规定
> 「**未通过严格 Schema 校验的 Package 不得接收**」。
> 依赖见 `research/scripts/requirements.txt`。

### ★ 关于 `--check` 的一个**已知困惑**（不是环境坏了）

`--check` 的 **C02 硬编码检查 `HISTORICAL_UNIVERSE_R01_TASK_MANIFEST_v0_1.json`**
（要求其 `tasks` 恰为 `R01-01`…`R01-06`）。那份 manifest 与你**毫无关系**，
但校验器把它当作基础设施的一部分。**所以它必须留在这个沙箱里** ——
请不要因为「它不是我任务的 manifest」就删掉它，否则 `--check` 会 FAIL。

---

## 五、你的产出会发生什么

1. 交给 **ThreeC Agent**（另一个执行者）逐条审查（八种封闭结果，协议 §4）。
2. 走 CMTR v1 解析 Macro Theme；走 Campaign Independence Gate 判 Campaign。
3. 只有通过审查的才写入 canonical。

★ **角色分离是硬规则**：你**不得**自己写入 canonical，也**不要**代替审查下结论。
把「为什么它成立」的理由写足即可。

---

## 六、最重要的一句

> **宁可空缺，不得凑数。**
> 「该方向历史上**没有**形成 Campaign」是**合法且有价值的结论** ——
> 用 `no_clear_campaign` / `exclusions[]` 显式记录，而不是把边缘事件升级成 Campaign。

---

*沙箱由 `research/scripts/make_research_handoff_sandbox.py` 生成 · 任务 `{task}`*
""".format(task=task_id, manifest=manifest_name, prompt=prompt_name,
           dirs="\n".join("- **%s**" % d for d in directions),
           venv=VENV_PY)


def main(argv):
    ap = argparse.ArgumentParser(description="构建 Research Agent 交接沙箱")
    ap.add_argument("--task", required=True, help="任务 ID，如 R02-03")
    ap.add_argument("--out", default=None, help="输出目录（默认 ~/Aiworking/threec-<task>-handoff）")
    ap.add_argument("--force", action="store_true", help="目标目录已存在时清空重建")
    args = ap.parse_args(argv)

    task_id = args.task
    hits = find_manifest_for_task(task_id)
    if not hits:
        raise SystemExit("在 %s 里找不到包含 task_id=%s 的 manifest" % (INTAKE_DIR, task_id))
    manifest_path, manifest, task_obj = hits[0]
    manifest_name = os.path.basename(manifest_path)

    prompt_name = "RESEARCH_AGENT_PROMPT_%s.md" % task_id
    prompt_path = os.path.join(DOCS_DIR, prompt_name)
    if not os.path.isfile(prompt_path):
        raise SystemExit("缺少 Prompt 文档：%s" % prompt_path)

    out = args.out or os.path.join(os.path.expanduser("~"), "Aiworking",
                                   "threec-%s-handoff" % task_id.lower())
    out = os.path.abspath(os.path.expanduser(out))

    # ★ 防呆：不要把沙箱建在仓库里面（那等于没有隔离）
    if out == ROOT or out.startswith(ROOT + os.sep):
        raise SystemExit("拒绝把沙箱建在仓库内部（等于没有隔离）：%s\n"
                         "请用 --out 指定仓库外的目录。" % out)

    if os.path.exists(out):
        if not args.force:
            raise SystemExit("目标已存在：%s\n（加 --force 清空重建）" % out)
        shutil.rmtree(out)
    os.makedirs(out)

    # ---- 1. 复刻 research/{intake,scripts} 相对结构（校验器的 ROOT 由脚本位置推导）----
    for name in ("HISTORICAL_UNIVERSE_INTAKE_PROTOCOL_v0_1.md",
                 "HISTORICAL_UNIVERSE_COVERAGE_PLAN_v0_1.md",
                 "historical_research_intake.schema.json",
                 R01_MANIFEST,
                 manifest_name):
        copy_file(os.path.join(INTAKE_DIR, name),
                  os.path.join(out, "research", "intake", name))

    copy_file(os.path.join(SCRIPTS_DIR, "validate_historical_research_intake.py"),
              os.path.join(out, "research", "scripts", "validate_historical_research_intake.py"))
    copy_file(os.path.join(SCRIPTS_DIR, "requirements.txt"),
              os.path.join(out, "research", "scripts", "requirements.txt"))

    # ---- 2. 样例包（只读参考）----
    for pkg in ("R02-01", "R02-02"):
        src = os.path.join(INTAKE_DIR, "packages", pkg)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(out, "research", "intake", "packages", pkg))

    # ---- 3. Prompt ----
    copy_file(prompt_path, os.path.join(out, "docs", prompt_name))

    # ---- 4. 参照表 + 入口说明 ----
    write_text(os.path.join(out, "EXISTING_UNIVERSE.md"), build_existing_universe())
    write_text(os.path.join(out, "00_START_HERE.md"),
               build_start_here(task_id, manifest_name, prompt_name, task_obj))

    print("✓ 沙箱已建：%s" % out)
    print("  任务      : %s" % task_id)
    print("  scope 依据: research/intake/%s" % manifest_name)
    print("  可写位置  : research/intake/packages/%s/" % task_id)

    # ---- 5. 就地自检（证明沙箱可用）----
    if os.path.isfile(VENV_PY):
        print("\n--- 沙箱内 --check 自检 ---")
        r = subprocess.run([VENV_PY,
                            os.path.join(out, "research", "scripts",
                                         "validate_historical_research_intake.py"),
                            "--check"], capture_output=True, text=True)
        tail = (r.stdout or "").strip().splitlines()[-3:]
        for line in tail:
            print("  " + line)
        if r.returncode != 0:
            print("✗ 沙箱自检未通过 —— 请先修复环境再交给 Research Agent")
            return 1
        print("✓ 沙箱自检通过")
    else:
        print("! 未找到校验器解释器 %s —— 请先按 research/scripts/requirements.txt 安装" % VENV_PY)

    print("\n--- 把下面这句连同 00_START_HERE.md 一起发给 Research Agent ---")
    print("你的操作空间是：%s" % out)
    print("先读 00_START_HERE.md，再按其中顺序读四份文件；"
          "唯一可写位置是 research/intake/packages/%s/。" % task_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
