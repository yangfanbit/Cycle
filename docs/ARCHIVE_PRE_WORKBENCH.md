# 重构前存档（2026-11-04）

> 目的：按「重构方案 B（另起研究工作台，当前站点退为只读档案）」开始之前，
> 把 **v0.73 的完整现状**冻结成一个可追溯、可离线打开的快照。
> **本轮未修改任何既有文件**：产品代码 / 研究产物 / 数据库 / 三份状态文档正文全部原样保留。

## 1 · 基线

| 项 | 值 |
|---|---|
| 代码基线 | **`6a190cf`**（v0.73，当时 `origin/main == HEAD`，0 个未推提交） |
| git 锚点 | tag **`archive/v0.73-pre-workbench`** → 直接指向 `6a190cf`（**不含**本次新增的存档文件，checkout 即得到干净的产品代码状态） |
| 实体包 | `archive/three-c_v0.73_pre-workbench_20261104.tar.gz`（1.1 MB，sha256 `c5294590bc…`） |
| 行情截止 | **2026-10-30** |
| 主要产物生成 | **2026-10-31** |
| 状态文档更新 | **2026-11-02** |
| **本存档生成** | **2026-11-04 21:22 +0800** |

★ 四类日期分开记录，不得互相冒充。

## 2 · 包内容

```
MANIFEST.txt          生成时间 / 基线 / site 文件逐项 sha256 前 16 位 / 预览与回退命令
site/                 生产等价静态站点（THREEC_BASE=/Cycle/ 构建，20 个文件 / 9,046,058 字节）
state/                README.md · PROJECT_STATE.md · ROADMAP.md（存档当天的三份状态文档副本）
```

`site/` 的资源路径是 `/Cycle/assets/...`（与 GitHub Pages 项目站一致），**不能直接双击 index.html 打开**。

## 3 · 本地打开存档站点

```bash
mkdir -p preview/Cycle && tar -xzf archive/three-c_v0.73_pre-workbench_20261104.tar.gz -C /tmp/x
cp -R /tmp/x/site/. preview/Cycle/
cd preview && python3 -m http.server 8080
# → http://localhost:8080/Cycle/
```

或在仓库内：`THREEC_BASE=/Cycle/ npx vite preview --outDir <解开后的 site 目录>`。

**代码回退**：`git checkout archive/v0.73-pre-workbench`。git 历史本身就是完整回退点，
实体包只是「线上不可用时仍能打开页面」的额外保险。

## 4 · 存档时的已知问题（如实记录，不掩饰）

### 4.1 线上入口不可用（重构前的阻断项）

| 实测 | 结果 |
|---|---|
| `https://yangfanbit.github.io/Cycle/` | **301** → `location: http://yfnwu.com/Cycle/`（`server: GitHub.com`，`age: 0`，非 CDN 缓存） |
| `https://yangfanbit.github.io/`（根） | 同样 **301** → `http://yfnwu.com/` |
| `https://www.yfnwu.com/Cycle/` | **404**（Gridea 站点 404 页） |
| `https://www.yfnwu.com/` | **200**（另一个站点，非 ThreeC） |
| DNS | `www.yfnwu.com` CNAME → `cname-china.vercel-dns.com`；`yfnwu.com` A → `76.223.126.88`（**均非 GitHub Pages IP**） |
| `yangfanbit/Cycle` 最近一次 CI | `6a190cf` **success**（2026-11-01）→ 部署本身没问题 |

**根因**：自定义域绑在**用户级 Pages 仓库** `yangfanbit/yangfanbit.github.io`（该仓库 homepage = `http://yfnwu.com/`）。
只要用户级站点设了 Custom domain，GitHub 就会把 `yangfanbit.github.io/<任意路径>`（含 `/Cycle/`）
整体 301 到 `yfnwu.com/<同名路径>`；而该域名现在的 DNS 已迁走（Vercel / 停放），
上面没有 `/Cycle/` 这个路径 → 404。

→ **不是** `Cycle` 仓库的配置：仓库内无 `CNAME` 文件、workflow 用 `actions/deploy-pages@v4`
且不写 CNAME、301 带 query 实时返回（排除缓存）。
→ 用户「域名已解绑」很可能在 **DNS / 域名注册商侧**生效了，
但 **GitHub 用户级仓库 Settings → Pages → Custom domain 里仍留着 `yfnwu.com`**。
→ 修复需在该仓库的 Pages 设置里清空 Custom domain（跨仓库设置，本存档不触碰），
之后 `https://yangfanbit.github.io/Cycle/` 才会恢复 200。

### 4.2 其余已知边界（存档时不改）

- 首页实测：可见文本 **20,370 字** / 页高 **10,172 px** / **1,078** 个按钮 / 63 个折叠区；
  唯一用户提问入口 `#direction-lookup` 在 **y=9451 px**（页面 93% 处）；新题材雷达占页面高度 **59%**。
- 雷达 263 事件中 **204 条无关联**，75 条关联**全部来自标题关键词**（正文命中 0）。
- 候选账本 204 条，`PRE_WINDOW` 152 / `IN_WINDOW` 52，**20 日结果 0 条成熟**。
- 真实使用记录 `.tmp/real_use/records` **0 条**（该目录被 Git 忽略，不入库）。
- Market Snapshot 维持既有治理状态：未签发、未归档、未改 `index.json`。

## 5 · 边界

本存档**不**构成对现有研究口径、冻结产物、Schema、Export Contract、SA / TO / Driver 的修改或复核结论；
也不代表这些状态已被重新验证。后续重构从 `6a190cf` 之后的**新提交**开始，旧版本与旧产物一律保留。
