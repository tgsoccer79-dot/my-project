#!/bin/bash
# ふるさと納税 毎日ニュース自動更新スクリプト
# cron 設定例（ローカルMacで実行）:
#   0 9 * * 1-5 /path/to/my-project/scripts/daily_news_update.sh >> ~/.claude/news-update.log 2>&1
#
# 動作:
#   月曜日 → 金曜〜日曜の3日分をまとめて取得
#   火〜金  → 当日分を取得
#   土日    → cronで除外（1-5指定）しているためスキップ

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SENTINEL_FILE="${HOME}/.claude/furusato-news-last-update"
TODAY=$(date +%Y-%m-%d)
DOW=$(date +%u)  # 1=月, 2=火, ..., 7=日

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ニュース更新チェック開始"

# 当日すでに実行済みなら終了
if [ -f "$SENTINEL_FILE" ] && [ "$(cat "$SENTINEL_FILE")" = "$TODAY" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 本日分は更新済み。スキップします。"
  exit 0
fi

# 月曜日かどうかで対象期間を変える
if [ "$DOW" = "1" ]; then
  FRI=$(date -v-3d +%Y-%m-%d 2>/dev/null || date -d '3 days ago' +%Y-%m-%d)
  SAT=$(date -v-2d +%Y-%m-%d 2>/dev/null || date -d '2 days ago' +%Y-%m-%d)
  SUN=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d '1 day ago' +%Y-%m-%d)
  PERIOD="月曜日のため金曜（${FRI}）〜日曜（${SUN}）の3日分"
else
  PERIOD="本日（${TODAY}）分"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 対象期間: ${PERIOD}"

# claude CLI でニュース更新を実行
cd "$PROJECT_DIR"
claude --print \
  "ふるさと納税の${PERIOD}の最新ニュース・制度改定情報を取得・整理してください。
/update-news スキルの手順（WebSearch → timeline.md確認 → archive作成 → timeline.md更新 → コミット）に厳密に従って実行し、
新しいニュースがあれば docs/02_news/ を更新してコミットまで完了させてください。
新しいニュースがない場合は「新規ニュースなし」と報告してください。" \
  --output-format text

# 完了フラグを保存
echo "$TODAY" > "$SENTINEL_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完了。sentinel更新: $SENTINEL_FILE"
