# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and others) working in this repository.

## プロジェクト概要

**ふるさと納税 分析ダッシュボード** — 総務省現況調査データをベースにした自治体向け分析ツール。

- **本番URL**: https://my-project-t4lf9jtladg669yhnb5m38.streamlit.app/
- **デプロイ先**: Streamlit Community Cloud（`main`ブランチを自動デプロイ）
- **対象ユーザー**: 業務委託先の自治体職員・社内チーム

## スタック

| 用途 | ライブラリ |
|---|---|
| UIフレームワーク | Streamlit >= 1.35.0 |
| データ処理 | pandas >= 2.0.0 |
| 可視化 | plotly >= 5.20.0 |
| 機械学習 | scikit-learn >= 1.3.0（**必ずクラス内でimport**。トップレベルimportはStreamlit Cloudでクラッシュする） |
| Excel読み込み | openpyxl >= 3.1.0 |

## Git ワークフロー

- **本番ブランチ**: `main`（Streamlit Cloudが自動デプロイ）
- **開発ブランチ**: `claude/<description>-<id>`（AI作業）/ `feat/<description>`（人間作業）
- mainへのマージ後は自動でStreamlit Cloudに反映される
- force-pushは絶対禁止

## ローカル起動

```bash
git clone https://github.com/tgsoccer79-dot/my-project.git
cd my-project
pip install -r requirements.txt
streamlit run app/main.py
```

## データ更新

```bash
# 総務省Excelを data/raw/ に置いてからパース
python scripts/parse_soumu_excel.py
```

Excel取得先: https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/

## プロジェクト構造

```
my-project/
├── app/
│   └── main.py              # Streamlitアプリ本体（7タブ）
├── data/
│   ├── raw/                 # 総務省Excel（.gitignore対象）
│   ├── jichitai_detail.csv          # 2024年度 費目別明細（1,788行）
│   ├── jichitai_detail_multi.csv    # 2019〜2024年度 費目別明細（10,728行）
│   ├── jichitai_timeseries.csv      # 2008〜2024年度 時系列（32,011行）
│   ├── market_trends_annual.csv     # 全国市場トレンド
│   ├── kifu_ranking_by_year.csv     # 自治体別年間ランキング
│   ├── keihi_annual.csv             # 全国経費内訳
│   ├── henreihin_ranking.csv        # ポータル別人気返礼品ランキング
│   └── toshi_ryushutsu.csv          # 都市部住民税流出データ
├── docs/                    # 知識ベース（Markdown）
│   ├── 01_seido/            # 制度情報
│   ├── 02_news/             # ニュース・動向
│   ├── 03_market/           # 市場データ・ランキング
│   └── 04_keihi/            # 経費データ
├── scripts/
│   └── parse_soumu_excel.py # 総務省Excel → CSVパーサー
├── requirements.txt
└── CLAUDE.md
```

## アプリのタブ構成（app/main.py）

| タブ | 内容 |
|---|---|
| 📈 市場全体を知る | 全国受入総額・件数推移・制度改正アノテーション |
| 🏆 ランキングを見る | 年間ランキング＋バンプチャート（順位変動） |
| 🏘️ 自治体を深掘りする | 診断カード・成長曲線・経費推移・ベンチマーク推薦・MDレポート出力 |
| ⚔️ 自治体を比較する | 最大4自治体の寄附額・順位・経費率を並列比較 |
| 🗾 地域の動きを見る | 都道府県別ヒートマップ・県内突出自治体 |
| 🔬 経費・効率を分析する | 都道府県ヒートマップ・箱ひげ図・急成長解剖・収支サマリー |
| 📤 データを抽出する | 条件フィルタ＋CSV／MDレポートダウンロード |

## MDレポート出力機能

Tab 3・Tab 7から、以下を含むMarkdownを生成・ダウンロード可能：
- 総務省公開データによる観察・仮説
- 社内Redshift DBへのSQLクエリ（即実行可能）

**内部DB接続情報（SQLテンプレート）:**
- ワークグループ: `wg-ledghome-bigdata` / DB: `dev` / スキーマ: `public`
- 寄附テーブル: `lhcloud_tax_data`
- 配送テーブル: `lhcloud_deli_data`
- 必須フィルタ: `tax_st_id = 2`（完了のみ）、`delete_flg = 0`
- DB市場カバー率: 約48%（総務省値と比較する際は考慮すること）

## 重要な実装上の注意

- `sklearn` は **`calc_clusters()` 関数の内部でimport** すること（トップレベルimport禁止）
- 金額表示は `fmt_oku()` を使用（1兆以上は「X兆Y,ZZZ億円」形式）
- 年表記は「YYYY年度」に統一（英語混在・数字のみ禁止）
- 総務省ExcelはGit管理外（`data/raw/*.xlsx` は `.gitignore` 対象）

## データ更新スケジュール

| タイミング | 作業 |
|---|---|
| 毎年7月下旬 | 総務省現況調査公表 → `market_trends_annual.csv`・`kifu_ranking_by_year.csv` 更新 |
| 随時 | ポータル別人気ランキング → `henreihin_ranking.csv` 更新 |
| 随時 | 制度改正・ニュース → `docs/` 更新 |

次回の総務省現況調査公表: **2026年7月予定**（2025年度データ）

## AI アシスタント向けガイドライン

- **読んでから編集**: 必ずReadツールで確認してから編集する
- **最小変更**: タスクに必要な変更のみ。投機的なリファクタは行わない
- **sklearnのimport**: 絶対にトップレベルに書かない（Streamlit Cloud起動クラッシュの原因）
- **コミット粒度**: 1コミット1目的
- **確認してから破壊的操作**: ファイル削除・force-pushは必ずユーザーに確認
