# data/ — 構造化データ置き場

Markdownは「要約・解説・文脈」、こちらは「更新しやすい生データ（CSV）」を置く場所。
数値の時点変化を追うことが主な目的なので、**必ず `fetched_at`（取得日）と `source` を入れる**。

## ファイル一覧

| ファイル | 内容 | 更新頻度 |
|---------|------|---------|
| [market_trends_annual.csv](market_trends_annual.csv) | 全国の寄附総額・件数・経費率の年次推移（2008〜） | 年1回（総務省現況調査公表後：毎年7〜8月） |
| [kifu_ranking_by_year.csv](kifu_ranking_by_year.csv) | 自治体別寄附額ランキング（複数年・上位のみ） | 年1回（同上） |
| [henreihin_ranking.csv](henreihin_ranking.csv) | 人気返礼品ランキング（ポータル別・期間別） | 月次〜随時（ポータル各社のランキング・プレスリリース） |

---

## スキーマ定義

### market_trends_annual.csv

| 列名 | 内容 |
|------|------|
| year | 年度（4桁・4月始まり） |
| kifu_total_oku | 全国受入総額（億円） |
| kifu_total_yen | 全国受入総額（円、空欄可） |
| cases_man | 受入件数（万件） |
| control_users_man | 住民税控除適用者数（万人） |
| keihi_rate_pct | 経費率（%、判明分のみ） |
| portal_fee_oku | ポータル手数料合計（億円） |
| notes | 特記事項 |
| source | 出典 |
| fetched_at | データ取得日（YYYY-MM-DD） |

### kifu_ranking_by_year.csv

| 列名 | 内容 |
|------|------|
| year | 年度 |
| rank | 全国順位 |
| prefecture | 都道府県 |
| municipality | 自治体名 |
| kifu_oku | 受入寄附額（億円） |
| main_henreihin | 主力返礼品 |
| notes | 特記事項（特殊事例等） |
| source | 出典 |
| fetched_at | データ取得日 |

### henreihin_ranking.csv

| 列名 | 内容 |
|------|------|
| portal | ポータル名 |
| period | 対象期間（例: 2025年間・2025年1〜11月） |
| rank | 順位 |
| item_name | 返礼品名 |
| prefecture | 都道府県 |
| municipality | 自治体名 |
| category | カテゴリ（肉・海産物・米・日用品 等） |
| price_range_man | 寄附額帯（万円・目安） |
| notes | 特記 |
| source | 出典 |
| fetched_at | データ取得日 |

---

## 更新ルール

1. 数値を更新するときは**行を上書きせず、新しい行を追加**（年度・期間が違えば別行）。
2. 古いデータは消さない。年次推移として残すことが価値の源泉。
3. 更新したら対応するMarkdown（`docs/03_market/` や `docs/04_keihi/`）にも要約を反映し、コミットする。
4. コミットメッセージ例: `update: 2025年度 総務省現況調査データを追加`

## 次に作る予定のファイル

- `keihi_by_municipality.csv` — 自治体別 経費内訳（総務省現況調査より）
- `portal_fee_survey.csv` — ポータル別手数料調査データ（総務省調査が公表され次第）
