#!/usr/bin/env bash
# 安装小红书违禁词 skills 到 Claude Code / Codex / 任意目录
#
#   ./install.sh                      # 全部 skill → ~/.claude/skills（Claude Code 个人级）
#   ./install.sh codex                # 全部 skill → ~/.codex/skills（Codex CLI）
#   ./install.sh project              # 全部 skill → ./.claude/skills（当前项目）
#   ./install.sh all                  # 同时安装到 Claude Code 和 Codex
#   ./install.sh claude beauty food   # 只装 美妆、食品 两个行业 skill
#   ./install.sh claude overall       # 只装总 skill（xhs-banned-words）
#   ./install.sh /path/to/skills      # 安装到自定义目录
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO_DIR/skills"

target="${1:-claude}"
shift || true

case "$target" in
  claude)  dests=("$HOME/.claude/skills") ;;
  codex)   dests=("${CODEX_HOME:-$HOME/.codex}/skills") ;;
  project) dests=("$PWD/.claude/skills") ;;
  all)     dests=("$HOME/.claude/skills" "${CODEX_HOME:-$HOME/.codex}/skills") ;;
  -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
  *)       dests=("$target") ;;
esac

skills=()
if [ $# -eq 0 ]; then
  for d in "$SRC"/*/; do skills+=("$(basename "$d")"); done
else
  for s in "$@"; do
    if [ "$s" = "overall" ]; then skills+=("xhs-banned-words")
    elif [ -d "$SRC/$s" ]; then skills+=("$s")
    elif [ -d "$SRC/xhs-banned-words-$s" ]; then skills+=("xhs-banned-words-$s")
    else echo "未知 skill：$s" >&2; ls "$SRC" >&2; exit 1
    fi
  done
fi

for dest in "${dests[@]}"; do
  mkdir -p "$dest"
  for s in "${skills[@]}"; do
    rm -rf "${dest:?}/$s"
    cp -R "$SRC/$s" "$dest/$s"
    echo "✓ $s → $dest/$s"
  done
done
echo "完成。重启 Claude Code / Codex 后生效。"
