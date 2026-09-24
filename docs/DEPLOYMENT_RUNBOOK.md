# ThreeC Deployment Runbook v0.1

> **本文件是 ThreeC 的唯一部署操作规程。** 任何重新构建 / 重新部署 / 回滚都必须按本文件执行。
>
> 相关文件：
> - 部署定义与 Gate：`docs/THREEC_1_0_RELEASE_DEFINITION.md`
> - 当前状态：`docs/PROJECT_STATE.md`
> - 项目宪法（不可违反的边界）：`AGENTS.md`
> - 本文件不重复 Research 的验证方法，只定义**部署链路**。

---

## 0. 平台与入口

| 项 | 值 |
|---|---|
| 宿主 | **GitHub Pages** |
| Repo | `yangfanbit/Cycle`（public） |
| branch | `main` |
| 正式入口 | **https://yangfanbit.github.io/Cycle/** |
| 部署方式 | GitHub Actions（`.github/workflows/deploy.yml`） |
| 产物 | 纯静态 `dist/`（HTML / JS / CSS） |

> ⚠️ **入口当前不可用（HTTP 404）** —— 由 **user-site 自定义域名级联 301** 造成，**不在本仓库控制范围**。
> 详见 **§8.2**（含实测证据、根因链与两种修复方案）。**在 §8.2 阻塞解除前不得宣称入口可用。**

**不引入**（除非 GitHub Pages 出现无法接受的技术限制，且须先记录阻塞原因）：
Vercel · Netlify · Docker · 云服务器 · 后端 · 数据库 · CDN 产品化改造 · 任何运行时 API · LLM runtime。

### 0.1 一次性前置：启用 GitHub Pages（**不可由 CI 自动完成**）

`actions/deploy-pages` 要求仓库已存在 Pages site 且 `build_type = workflow`。
**在 Pages 首次启用前，`deploy` job 必然失败**（`build` job 会全绿）。

**人工操作（仅需一次，仓库所有者执行）**：

```text
GitHub → repo `yangfanbit/Cycle` → Settings → Pages
  Source:            Deploy from a branch   ← 改为 ↓
  Source:            GitHub Actions
  （Build and deployment → Source = "GitHub Actions"）
保存后无需选择 branch / folder。
```

> **★ 已完成（2026-09-24）**：本项目 Pages 已启用，`build_type = workflow`，`has_pages = true`。
> 亦可由具备 `admin` 权限的 token 通过
> `POST /repos/{owner}/{repo}/pages {"build_type":"workflow"}` 设置。

**验证是否已启用**（`has_pages` 必须为 `true`）：

```bash
curl -s https://api.github.com/repos/yangfanbit/Cycle | grep has_pages
```

**启用后**：`Actions` → `Deploy to GitHub Pages` → `Re-run jobs`（或再次 push `main`）。
此后每次 push `main` 自动构建 + 部署，无需任何人工步骤。

> ⚠️ **这不是 workflow 缺陷**。GitHub 设计上要求 Pages 首次启用必须由仓库所有者在
> Settings 中显式确认（涉及站点可见性与域名归属），CLI / Actions 均无权限代劳。
> `gho_` OAuth token **不含** `pages: write`，因此脚本也无法代设。

---

### 为什么不需要 SPA fallback

ThreeC **没有 client-side router**（无 `react-router`，无 `history.pushState`）。
所有导航都是同页状态切换 + **query 参数**（`?preview=1` / `?candidates=example`）。
因此 GitHub Pages 静态服务不需要 `404.html` / `_redirects` 之类的 SPA 回退配置。

> ⚠️ **若未来引入 client-side router**，必须同时补 SPA fallback，
> 否则深层路径直接刷新会 404。这是引入 router 的**前置条件**，不是可选项。

### 为什么不需要 `.nojekyll`

产物 `dist/` 内**没有**以 `_` 开头的文件或目录（见 `npm run build` 输出：
仅 `index.html` + `assets/*.js|css`）。Jekyll 不会吞掉任何资源，故不需要 `.nojekyll`。

> ⚠️ **若未来产物中出现 `_` 前缀文件/目录**（某些 bundler 插件会产出 `_plugin/`），
> 必须补 `dist/.nojekyll`（在 workflow 中生成，不提交），否则该资源会被 GitHub Pages 静默丢弃。

---

## 1. 正常发布（Research artifact 有更新）

> 适用：`exports/` 或 `research/research/reports/` 下的 artifact 发生变化。

```text
1.  Research artifact 更新（在 Research 侧完成，不在本仓库的 Product 层做）

2.  Research validator 全 PASS
    · research/scripts/validate_*.py（研究侧既定验证器）

3.  generator --check 全 PASS（逐字节可复现）
    · Driver v0.4 生成器 --check
    · SA v0.5 生成器 --check
    · TO v0.2 生成器 --check
    · lifecycle coverage validator（validate_lifecycle_coverage_v0_1.py）PASS

4.  确认 Product 消费的 artifact 版本（★ 关键步骤，见 §5）

5.  npm ci

6.  npm test                  ← 必须 0 failed

7.  npx tsc -b                ← 必须 PASS

8.  npm run build             ← 本地构建（base = /），验证可构建

9.  git push origin main      ← 触发 GitHub Actions 自动部署
                              （CI 内会再跑一次 tsc -b + npm test + build(base=/Cycle/)）

10. GitHub Actions 验证        ← build PASS + deploy PASS

11. Production smoke test      ← 按 §6 执行
```

**硬规则**

- 第 2–4 步属于 **Research 侧**，**不得**为了让 Product 好看而绕过或放宽。
- 第 6 步失败 → **不要 push**。CI 也会拦，但本地先拦更省事。
- 第 8 步只是「本地可构建」的自检；**真正部署的产物由 CI 生成**（`base=/Cycle/`）。

---

## 2. Product-only 更新（不动 Research）

> 适用：只改 `src/` / `vite.config.ts` / `index.html` / `.github/` 等，`exports/` 与
> `research/research/reports/` 的 artifact **未变**。

```text
npm ci
npm test          ← 0 failed
npx tsc -b        ← PASS
npm run build     ← PASS
git push origin main
```

Research 验证链**不需要**重跑 —— 因为 Research 输出未被触碰。

> **判据（机械）**：`git diff --name-only <上次部署 commit>..HEAD -- exports/ research/` 为空。
> 非空则必须走 §1 的完整流程。

---

## 3. Research artifact 更新（额外要求）

只要 `exports/` 或 `research/` 下的**已冻结研究结论 / artifact** 发生变化，就必须额外经过完整
Research validation chain（validator + `--check` + lifecycle coverage），并明确记录：

> **Research 是唯一真源。**
> **Product 不允许为了适配研究结果而修改研究语义。**

具体：

| 允许 | 不允许 |
|---|---|
| 重新生成下游 artifact（新版本文件，旧版逐字节保留） | 覆盖旧版本 artifact |
| 更新 Product Adapter 以消费**新版** artifact | 让 Product 重新计算 Research 结论 |
| 修 Product 侧读取 / 展示缺陷 | 改 Research 结论以迁就 Product 展示 |

**禁止**：改 Research Model · `research/schema/schema.sql` · Export Contract v1.0 · CMTR v1 ·
SA Rule Set · TO 标准 · 新增 Historical Objects。

---

## 4. Vite base path（子路径部署）

正式入口是 `https://yangfanbit.github.io/Cycle/`，因此**部署产物的资源必须是 `/Cycle/assets/...`**。

`vite.config.ts` 的 `resolveBase()` 规则：

| 条件 | base | 场景 |
|---|---|---|
| `THREEC_BASE` 已设置 | 取该值 | 显式覆盖（回滚 / 子路径复现 / 私有镜像） |
| `GITHUB_ACTIONS === 'true'` | `/Cycle/` | GitHub Actions（官方内置变量，恒为 `"true"`） |
| 两者皆无 | `/` | 本地 `dev` / `preview` / `test` |

**设计取舍（已定，不要改回）**：**不使用** `command === 'serve'` 分支。
那样会让 `vite preview` 与 `build` 产物不一致，**无法在本地复现 GitHub Pages 行为** ——
而 preview 的全部意义就是复现 production。

### 本地复现 GitHub Pages 行为

```bash
# 1) 按 CI 方式构建
GITHUB_ACTIONS=true npx vite build          # Windows bash: export GITHUB_ACTIONS=true

# 2) 断言 base 生效
grep -oE '(src|href)="[^"]*"' dist/index.html
#    期望：/Cycle/assets/...  且**没有** /assets/... 绝对引用

# 3) 起本地静态服务复现子路径
mkdir -p /tmp/ghp/Cycle && cp -r dist/* /tmp/ghp/Cycle/
cd /tmp/ghp && python -m http.server 8899
# 访问 http://127.0.0.1:8899/Cycle/
```

CI 里对应的是一个**硬门禁**步骤（`Verify base path is /Cycle/`）：
产物含 `/assets/` 绝对引用 → **fail**；未发现 `/Cycle/assets/` → **fail**。

---

## 5. Build provenance（Gate D7）—— Research artifact ↔ Product build 对应关系

**要回答的问题只有一个**：「线上这个 build 到底消费了哪一版 Research 结论？」

同一份信息有**三个**可查入口，互相交叉验证：

| 入口 | 位置 | 用途 |
|---|---|---|
| ① 页面页脚 | 「Build Provenance」折叠区块 | 任何人打开站点即可自查 |
| ② GitHub Actions Summary | 每次部署的 `Deployment provenance` 表 | 对账「哪个 commit 部署了哪个 Research 版本」 |
| ③ 构建产物 | `dist/assets/index-*.js` 内的字面量 | 机器校验（`src/data/__tests__/deployment.test.ts`） |

追踪字段与来源：

```text
Product version              ← package.json version          （构建时 vite define 注入）
Git commit                   ← git rev-parse HEAD            （构建时注入；CI = workflow checkout 的 commit）
Build time                   ← 构建时刻                       （构建时注入）
Research export version      ← exports/… source_commit 同文件的 timeline_export_version
Research export source_commit← exports/timeline_export_v1.json.source_commit  ★ 关键锚点
Research export generated_at ← exports/timeline_export_v1.json.generated_at
Historical objects           ← export.campaigns.length / research_candidates.length
SA artifact_version          ← structural_analogy_explanations_v0_5.json.artifact_version
SA rule_set_version          ← 同文件 rule_set_version
TO artifact_version          ← time_observation_patterns_v0_2.json.artifact_version
```

**实现方式（最小改动，不要扩成新系统）**

- `src/data/buildProvenance.ts`：**只读汇总**已有字段。三个 artifact 都经 Vite 静态 import
  （`@exports` / `@observation` alias，与 Product 其它模块消费方式一致）
  → 构建期打包，**运行时零网络请求**。
- `vite.config.ts` 的 `provenanceDefines()`：把 `package.json` version / `git rev-parse HEAD` /
  构建时刻以**字符串字面量**注入（不用运行时 `process.env`，否则浏览器端 ReferenceError）。
- 任一字段不可得 → 注入 `"unknown"` → 模块转 `null` → UI 显示 **「未标注」**（**不猜测**）。
- **不新增** backend / API / runtime metadata 系统；**不改**任何 Research artifact schema。

> ⚠️ **致命失败状态**：若上线后页脚「Research export source commit」显示的 commit **不等于**
> 你刚更新的 Research artifact 的 `source_commit`，说明部署用的还是旧 artifact。
> 处理：按 §7 回滚或重新部署，**不要**在线上用任何方式「就地修正」数据。

---

## 6. Production smoke test（每次部署后必做）

在**正式 URL** 上执行：**https://yangfanbit.github.io/Cycle/**

### 6.1 首页

- [ ] 页面能打开，标题为「A股机会时间轴」
- [ ] DevTools Network：JS / CSS **全部 200**，**无 404**
- [ ] DevTools Console：**无致命错误**（红字）
- [ ] 页脚「Build Provenance」可展开，且 `Research export source commit` = 本次部署对应的 artifact commit

### 6.2 Current Candidate

- [ ] 5 个 Current Candidate 均能进入
- [ ] 当前时间（Current Time Lens）/ Calendar 正常渲染

### 6.3 Lifecycle

- [ ] 有 Research lifecycle 的对象**正确显示阶段**
- [ ] **UNKNOWN-only RC 不显示具体阶段**（不出现「主升 / 扩张 / 峰值 / 退潮 / 结束」）
- [ ] 已结束 Campaign **不显示成「当前仍在扩张」**

### 6.4 Structural Analogy

- [ ] SA 正常加载（展开候选时加载）
- [ ] **不出现** score / ranking / probability / 预测 措辞

### 6.5 Historical Case

- [ ] Campaign / Research Candidate identity 正确（RC 明确标注「研究候选」）
- [ ] lifecycle 正确
- [ ] evidence 正常
- [ ] `UNKNOWN` / `NOT_AVAILABLE` 语义**不丢失**（与 `MISMATCH` 可区分）

### 6.6 URL / asset

- [ ] `/Cycle/` base path 下 JS / CSS / 静态资源**无 404**
- [ ] **直接刷新**页面仍能正常加载
- [ ] `https://yangfanbit.github.io/Cycle/?preview=1` 可用
- [ ] `https://yangfanbit.github.io/Cycle/?candidates=example` 可用

---

## 7. 回滚（Gate D6）

> **本轮不创建 `v1.0.0`、不打 tag。** 因此回滚目标用**已验证的 Git commit SHA**，
> 而不是一个被伪造成「v1.0.0」的版本号。

### 7.1 判定：什么时候回滚

线上出现下列任一情况：

- 首页打不开 / 资源 404 / console 致命错误
- Gate T 语义回归（例如 UNKNOWN-only RC 又显示具体阶段；已结束 Campaign 又显示为扩张）
- 出现 score / ranking / probability / 预测 措辞
- 页脚 provenance 的 `Research export source commit` 与预期 artifact 不一致

### 7.2 确定 rollback target

```bash
# 看部署历史（Actions 每次部署都对应一个 commit）
git log --oneline -20

# 选定「上一个已验证稳定」的 commit SHA
#   ★ 必须是一个**已经通过 npm test / tsc -b / build 且 smoke test 过**的 commit
TARGET=<stable-commit-sha>

# 确认它当时部署的 Research artifact 版本（防止回滚到与 Research 不匹配的 build）
git show ${TARGET}:exports/timeline_export_v1.json | grep -E '"source_commit"|"timeline_export_version"'
```

**Research artifact 与 Product build 的对应关系不能被破坏**：
`TARGET` 的 `exports/timeline_export_v1.json` 的 `source_commit` 必须与当时的研究基线一致。
若不一致 → 该 commit **不是**合法 rollback target。

### 7.3 执行回滚（通过 revert，保留历史）

**推荐方式 —— revert 一个反向 commit（不改写公共历史）：**

```bash
git revert --no-commit <bad-commit-sha>     # 生成反向改动，保留完整历史
# 若涉及多次提交：git revert --no-commit <sha1> <sha2> ...
npm ci
npm test          # ← 必须 0 failed；失败则中止回滚
npx tsc -b        # ← 必须 PASS
npm run build     # ← 必须 PASS
git commit -m "revert: rollback to <stable-commit-sha> (<reason>)"
git push origin main                        # 触发 CI 重新部署
```

**替代方式 —— 用 `THREEC_BASE` 之外不要做的事**：不要 `git reset --hard`、不要 force push、
不要 amend、不要 rebase 公共历史（见 `AGENTS.md` §6 Git 安全）。

### 7.4 验证回滚成功

```text
1. GitHub Actions：build PASS + deploy PASS
2. 访问 https://yangfanbit.github.io/Cycle/
3. 重跑 §6 全部 smoke test 项
4. 页脚 provenance 的 Research export source commit = 期望值
5. 记录：回滚原因 / 被回滚 commit / 回滚后 commit / 验证结果
```

---

## 8. CI 门禁总览（`.github/workflows/deploy.yml`）

```text
push main
    ↓
checkout
    ↓
setup Node 22（npm cache）
    ↓
npm ci
    ↓
npx tsc -b                       ← 门禁
    ↓
npm test                         ← 门禁（0 failed 才继续）
    ↓
npm run build                    ← GITHUB_ACTIONS=true → base=/Cycle/
    ↓
Verify base path is /Cycle/      ← 门禁（产物含 /assets/ 绝对引用 → fail）
    ↓
Write build provenance summary   ← 写入 Actions Summary（Gate D7）
    ↓
upload-pages-artifact (path: dist)
    ↓
deploy-pages (environment: github-pages)
```

硬约束：

- `npm test` **不可跳过**；测试失败**不得**产出部署物。
- **不部署源码**，只部署 `dist/`。
- `dist/` **不提交** Git（`.gitignore` 已忽略；走 CI artifact）。
- permissions 最小化：`contents: read` + `pages: write` + `id-token: write`。
- `concurrency: group=pages, cancel-in-progress=false`（不取消进行中部署，避免半成品上线）。
- 可重复执行：`workflow_dispatch` 支持手动重跑同一 commit。

### 机械校验

上述 workflow 契约由 **`src/data/__tests__/deployment.test.ts`** 自动断言
（workflow 存在 / 必跑 test / 不跳过 / 只传 dist / 权限最小 / 无第三方托管 / concurrency 正确 /
base 规则 / provenance 字段与 artifact 一致）。
**改 workflow 或 vite config 若破坏这些契约，`npm test` 会失败。**

### 8.1 已知首次部署阻塞：`has_pages = false`

**症状**：`build` job 全绿（含 `tsc -b` / `npm test` / base-path gate / provenance summary），
但 `deploy` job 在 `Deploy to GitHub Pages` 步骤 `failure`。

**根因**：仓库从未启用 GitHub Pages（`GET /repos/{owner}/{repo}` → `has_pages: false`；
`GET /repos/{owner}/{repo}/pages` → `404`）。`actions/deploy-pages` 要求 Pages site 已存在。

**处置**：执行 §0.1 一次性启用，然后 `Re-run jobs`。
**这不是代码或 workflow 缺陷**，也不应通过换平台绕过（见 §0 约束）。

### 8.2 ★ 已知线上入口阻塞：user-site 自定义域名级联 301

**状态：待用户决策（不在本仓库控制范围内）。**

**症状**：`https://yangfanbit.github.io/Cycle/` 返回 **HTTP 404**，
但 Actions 的 `deploy` job **成功**（deployment environment `github-pages`，sha = 部署 commit）。

**实测证据**（直连真实 GitHub Pages IP `185.199.108.153`，绕过代理）：

```http
GET /Cycle/ HTTP/1.1
Host: yangfanbit.github.io

HTTP/1.1 301 Moved Permanently
Server: GitHub.com
Location: http://yfnwu.com/Cycle/
```

**根因链**：

| 层 | 观测 | 说明 |
|---|---|---|
| `yangfanbit/yangfanbit.github.io`（**user site**） | `cname: "yfnwu.com"` · `build_type: legacy` | ★ **此处设置了账户级自定义域名** |
| `yangfanbit/Cycle`（本项目 · **project site**） | `cname: null` · `build_type: workflow` | 本项目**没有**设置任何自定义域名 |
| `yfnwu.com` DNS | `76.223.126.88`（**非** GitHub Pages 的 `185.199.108.153`） | 该域名由 **Vercel** 托管 |
| `yfnwu.com/Cycle/` | `HTTP 308 → https://yfnwu.com/Cycle/` → **404**（`server: Vercel`） | Vercel 上**没有** `/Cycle/` 路由 |

**机制**：GitHub Pages 会把 **user site 的自定义域名级联到该账户下所有 project site**。
因此 `yangfanbit.github.io/Cycle/` 被 301 到 `yfnwu.com/Cycle/`，而 `yfnwu.com` 由 Vercel 托管且无该路由 → 404。

**★ 本项目**无法**自行修复**：`Cycle` 的 `cname` 已经是 `null`；
修复必须改动**另一个仓库**（`yangfanbit/yangfanbit.github.io`）的 Pages 自定义域名设置，
或把 `yfnwu.com` 的 DNS/路由接到 GitHub Pages。**两者都超出本轮授权范围。**

**可选修复（需用户明确授权，二选一）**：

```text
方案 A —— 释放 user-site 的自定义域名（推荐，最快）
  GitHub → repo `yangfanbit/yangfanbit.github.io` → Settings → Pages
  → Custom domain 清空 → Save
  效果：`https://yangfanbit.github.io/Cycle/` 立即可用。
  影响：`yfnwu.com` 不再由 GitHub Pages 服务（若该域名目前由 Vercel 服务，则无实际影响）。

方案 B —— 保留自定义域名，改由 GitHub Pages 托管
  把 `yfnwu.com` 的 DNS 指向 GitHub Pages（A 记录 185.199.108-111.153 或 CNAME）
  + 在 user site 配好 `yfnwu.com/Cycle`（需把 `Cycle` 部署为 user site 的子路径，结构冲突）
  代价高、影响面大，不推荐。
```

**★ 在阻塞解除前**：**不得宣称 `https://yangfanbit.github.io/Cycle/` 可用**。
可用的证据目前只有 Actions `deploy` 成功 + artifact 已上传。

---

## 9. 部署 ≠ 发布（重要）

> **本轮「Deployment Engineering 完成」≠「ThreeC 1.0 正式发布」。**

本轮**不**做：

- ❌ `package.json` → `1.0.0`（本轮仍为 `0.1.0`）
- ❌ 创建 `git tag v1.0.0`
- ❌ 对外宣称「ThreeC 1.0 Released」

只有 `docs/THREEC_1_0_RELEASE_DEFINITION.md` 的 **Eight Gates 全部 PASS**（含 Gate M 真机复核、
Gate D 完整）之后，**下一轮**才执行：

```text
package.json → 1.0.0
    ↓
release commit
    ↓
git tag v1.0.0
    ↓
正式 production deployment
    ↓
最终访问验证
    ↓
PROJECT_STATE / ROADMAP / README 最终锁定
```
