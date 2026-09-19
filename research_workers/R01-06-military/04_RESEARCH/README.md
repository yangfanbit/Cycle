# 04_RESEARCH/ — 临时研究区

> 这是 Research Worker 的**过程区**，不是交付结构。

---

## 允许

- `notes` —— 研究笔记
- research working papers —— 研究草稿
- downloaded text summaries —— 下载资料的摘要
- candidate analysis —— 候选分析
- source discovery notes —— 来源发现记录
- 中间态草稿（JSON / Markdown / 文本均可）

---

## 不允许

> **最终可交付结果必须整理进入 `05_OUTPUT/`。**

- ❌ 不得在这里建立**第二套交付结构**（不要在这里放 `manifest.json` / `candidates.json` / …）
- ❌ 不得把 `04_RESEARCH/` 当作交付目录
- ❌ 不得让 `04_RESEARCH/` 的内容成为 ThreeC Agent 的输入

---

## 关系

```text
04_RESEARCH/          ← 过程（可混乱、可迭代、可丢弃）
      ↓  整理 / 收敛
05_OUTPUT/            ← 交付（必须通过 validator）
      ↓
ThreeC Agent
```

---

## 校验范围

`python tools/validate_historical_research_intake.py --check` **不会**校验本目录。
本目录的内容不受 validator 约束 —— 但也不会被 ThreeC Agent 读取。
