#!/usr/bin/env bash
# ============================================================================
# sandbox_try.sh —— 在**沙箱副本**里试跑 Research 脚本，绝不动仓库产物。
#
# 为什么需要它（2026-10-07 的真实事故）：
#   试跑 `build_structural_analogy_research_v0_5.py` 时只改了「输入」路径，
#   **没改「输出」路径**，脚本于是**写回了仓库**的两个 Research artifact。
#   根因有二：① 脚本的输出常量不止一个（json + csv），只 sed 一个不够；
#            ② 部分脚本的 CSV 写入**不在 `--check` 的保护范围内**（已修）。
#
# 本脚本把「读写整体重定向」做成一件事：
#   复制 research/ 与 exports/ 到临时沙箱 → 以 THREEC_ROOT 指向它运行 →
#   **打印沙箱与仓库的产物差异**，供人工审阅后再决定是否应用。
#
# 用法：
#   research/scripts/sandbox_try.sh <脚本名> [参数...]
# 例：
#   research/scripts/sandbox_try.sh build_structural_analogy_research_v0_5.py
#   research/scripts/sandbox_try.sh build_structural_analogy_explanation_v0_5.py
#
# 退出码：脚本自身退出码；沙箱路径与差异打印在末尾。
# ============================================================================
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: $0 <research/scripts 下的脚本名> [参数...]" >&2
  exit 2
fi

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$1"; shift

if [ ! -f "$REPO/research/scripts/$SCRIPT" ]; then
  echo "找不到脚本: research/scripts/$SCRIPT" >&2
  exit 2
fi

SB="$(mktemp -d)/threec-sandbox"
mkdir -p "$SB"
echo "沙箱: ${SB}"

# 只复制脚本会读到的两棵树；不复制 node_modules / .git（沙箱不是仓库）
cp -R "$REPO/research" "$SB/research"
cp -R "$REPO/exports" "$SB/exports" 2>/dev/null || mkdir -p "$SB/exports"

echo "运行: ${SCRIPT} ${*}（THREEC_ROOT=${SB}）"
echo "--------------------------------------------------------------------"
set +e
THREEC_ROOT="$SB" python3 "$SB/research/scripts/$SCRIPT" "$@"
RC=$?
set -e
echo "--------------------------------------------------------------------"
echo "脚本退出码: ${RC}"

echo
echo "=== 沙箱 vs 仓库：产物差异（有差异 = 这次试跑会改动这些文件）==="
diff -rq "$REPO/research/research/reports" "$SB/research/research/reports" 2>/dev/null \
  | sed -e "s|$SB|<sandbox>|g" -e "s|$REPO|<repo>|g" || true
diff -rq "$REPO/research/current" "$SB/research/current" 2>/dev/null \
  | sed -e "s|$SB|<sandbox>|g" -e "s|$REPO|<repo>|g" || true

echo
echo "★ 仓库未被改动。若要采纳，请人工审阅差异后**显式**把沙箱产物拷回仓库。"
echo "  沙箱保留在: ${SB}"
