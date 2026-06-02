# data/ — 構造化データ置き場

Markdownは「要約・解説」、こちらは「分析しやすい生データ（CSV等）」を置く場所。

## 想定ファイル（TODO 作成していく）

- `kifu_ranking_YYYY.csv` — 年度別 自治体寄附額ランキング
- `henreihin_ranking_<portal>_YYYY-MM.csv` — ポータル別 人気返礼品
- `keihi_<jichitai>.csv` — 自治体別 経費内訳

## 列設計の方針（例）

### kifu_ranking_YYYY.csv
```
rank,prefecture,municipality,kifu_amount_yen,count,main_henreihin,year,source_url,fetched_at
```

### keihi_YYYY.csv
```
prefecture,municipality,year,kifu_amount,keihi_total,keihi_rate,henreihin_cost,shipping,fee,admin,source_url,fetched_at
```

> データには必ず `source_url` と `fetched_at`（取得日）を残し、出典を辿れるようにする。
