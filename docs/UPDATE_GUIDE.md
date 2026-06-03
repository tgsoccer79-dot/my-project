# 更新ガイド（ランブック＋カレンダー）

ふるさと納税知識ベースを「鮮度の高い状態」に保つための更新手順書。
人間が手で更新するときも、AIに「UPDATE_GUIDEに従って更新して」と頼むときも、ここを起点にする。

> 最終更新: 2026-06-02

---

## 基本原則

1. **時点を必ず残す** — 数値には `（YYYY年度／YYYY-MM-DD取得）` を付ける。
2. **行を上書きせず追記** — CSVは新年度・新期間を別行で追加。古いデータは消さない（推移が価値）。
3. **出典をセットで** — 「媒体名・URL・取得日」を必ず残す。一次情報（総務省・国税庁）を優先。
4. **更新したらコミット** — 1つの更新＝1コミット。メッセージ例: `update: 2025年度 現況調査データを反映`
5. **要約とデータの二層** — `data/*.csv` に生データ、`docs/**/*.md` に要約・解説。両方を更新する。

---

## 更新カレンダー（年間スケジュール）

| 時期 | やること | 主な情報源 | 反映先 |
|------|---------|-----------|--------|
| **毎年 7〜8月** | 総務省「現況調査結果」の最新年度を反映（最重要・年1回の幹） | 総務省 | market_trends_annual.csv / kifu_ranking_by_year.csv / keihi_data.md |
| **毎年 7月** | 東京都・主要都市の税収流出額（前年度分）を更新 | 日経・東洋経済 | keihi_data.md |
| **毎年 12〜1月** | 各ポータルの「年間人気返礼品ランキング」を反映 | 楽天・さとふる・チョイス・ふるなび | henreihin_ranking.csv / ranking_henreihin.md |
| **毎年 春（税制改正後）** | 控除上限・制度改正があれば反映 | 総務省・国税庁 | gaiyo.md / kokuji.md / horei.md |
| **随時（月1目安）** | 制度改定の告示・主要報道をニュース追跡 | 総務省報道資料・各紙 | 02_news/timeline.md + archive/ |
| **告示改正のたび** | 告示原文を読み込み、基準の変更を反映 | 総務省告示・e-Gov | kokuji.md → rekishi.md にも追記 |

### 直近で待っているイベント（ウォッチリスト）

- [ ] **2026年7〜8月**: 2025年度（令和8年度実施）現況調査の公表 → 年次データ追加
- [ ] **2026年8月末**: ポータル手数料引き下げ要請への大手4社の回答期限 → ニュース追跡
- [ ] **2026年10月**: 地場産品基準の厳格化・「6割ルール」の確定告示 → kokuji.md / rekishi.md 更新
- [ ] **楽天 vs 総務省 訴訟**: 判決・続報（時期未定） → archive更新

---

## ランブック（更新タスク別の手順）

### A. 年次データ更新（総務省 現況調査）★最重要

**トリガー**: 毎年7〜8月、総務省が現況調査結果を公表したとき。

1. 総務省ポータル（[archive](https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/)）で最新年度のPDFを確認。
2. 全国の受入総額・件数・控除適用者数・住民税控除額を取得。
3. `data/market_trends_annual.csv` に**新しい年度の行を1行追加**。
4. `docs/03_market/market_trends.md` の年次推移表に同じ行を追加し、前年比・特記事項を記入。
5. 自治体別ランキング上位を取得し、`data/kifu_ranking_by_year.csv` に追加（年度・順位・自治体・寄附額・主力返礼品）。
6. `docs/03_market/ranking_kifu.md` の最新年度ランキングを更新。
7. 経費率・経費内訳が公表されていれば `docs/04_keihi/keihi_data.md` を更新。
8. コミット: `update: YYYY年度 現況調査データを反映`

### B. ポータル年間ランキング更新

**トリガー**: 毎年12〜1月、各ポータルが年間ランキングを発表したとき。

1. 楽天・さとふる・ふるさとチョイス・ふるなびの年間ランキングを確認。
2. `data/henreihin_ranking.csv` に**ポータル・期間ごとに新しい行を追加**（古い年は残す）。
3. `docs/03_market/ranking_henreihin.md` の各ポータル表とカテゴリ別傾向を更新。
4. カテゴリ動向（米・肉・海産物等）の変化があれば文章を追記。
5. コミット: `update: YYYY年 ポータル別人気返礼品ランキングを反映`

### C. ニュース・制度改定の追跡

**トリガー**: 随時（月1回チェック推奨）。告示・主要報道・統計発表を見つけたとき。

1. `docs/02_news/archive/YYYY-MM-DD_見出し.md` を新規作成（テンプレは [02_news/README.md](02_news/README.md)）。
2. 要点3行・背景・解釈/影響・出典URL・取得日を記入。
3. `docs/02_news/timeline.md` に1行サマリ＋archiveへのリンクを追加（上に新しいものを足す）。
4. 制度本体に関わる改定なら `docs/01_seido/` の該当ファイル（kokuji.md/rekishi.md等）にも反映。
5. コミット: `news: ◯◯（見出し）を追記`

### D. 告示改正の反映

**トリガー**: 総務省が指定基準・告示を改正したとき。

1. 総務省報道資料・e-Govで改正内容を確認。
2. `docs/01_seido/kokuji.md` の該当基準（5割/3割/地場産品）を更新。改正日・改正内容を明記。
3. `docs/01_seido/rekishi.md` の年表にも改正を1行追加。
4. 関連するニュースメモ（C）も作成。
5. コミット: `update: YYYY年◯月 告示改正（◯◯）を反映`

---

## AIに更新を頼むときのプロンプト例

```
docs/UPDATE_GUIDE.md のランブックAに従って、最新の総務省現況調査データを
調査して反映してください。出典と取得日を必ず付けて、CSVとMarkdownの両方を
更新し、コミットまでお願いします。
```

```
直近1か月のふるさと納税の制度改定・主要ニュースを調査して、
UPDATE_GUIDEのランブックCに従ってtimelineとarchiveに追記してください。
```

---

## 情報源クイックリンク

詳細は [docs/sources.md](sources.md) 参照。よく使うものだけ再掲：

- 総務省 現況調査アーカイブ: https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/
- 総務省 報道資料（制度改定）: https://www.soumu.go.jp/menu_news/
- 楽天ランキング: https://event.rakuten.co.jp/furusato/ranking/
- さとふるランキング: https://www.satofull.jp/static/ranking/
- ふるさとチョイス トレンド: https://www.furusato-tax.jp/
- RIETI（研究）: https://www.rieti.go.jp/jp/
