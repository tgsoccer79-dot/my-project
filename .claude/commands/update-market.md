# ふるさと納税 市場データ更新コマンド

docs/UPDATE_GUIDE.md のランブックA（年次データ）とランブックB（ポータルランキング）を実行します。

## 実行内容

以下を順番に行ってください：

### ステップ1: 総務省 現況調査の最新データを確認

WebSearchで「総務省 ふるさと納税 現況調査結果 最新」を検索し、`data/market_trends_annual.csv` の最終行の年度より新しいデータが公表されていれば取得してください。

取得したら：
- `data/market_trends_annual.csv` に新しい年度の行を追記（既存行は絶対に上書きしない）
- `data/kifu_ranking_by_year.csv` に上位自治体のデータを追記
- `docs/03_market/market_trends.md` の年次推移表を更新
- `docs/03_market/ranking_kifu.md` の最新年度ランキングを更新
- 経費率・経費内訳が公表されていれば `docs/04_keihi/keihi_data.md` を更新

### ステップ2: 各ポータルの最新人気ランキングを確認

WebSearchで楽天・さとふる・ふるさとチョイス・ふるなびの最新ランキングを調査し、`data/henreihin_ranking.csv` の最終記録より新しいデータがあれば追記してください。

- `docs/03_market/ranking_henreihin.md` の各ポータル表も更新
- カテゴリ別傾向に変化があれば文章を追記

### ステップ3: コミット

更新があった場合は以下のコミットメッセージで：
```
update: YYYY年度 市場データを更新（現況調査・ポータルランキング）
```

新しいデータがなかった場合は「現時点では新しいデータなし。次回確認推奨時期: YYYY年MM月」と報告してください。
