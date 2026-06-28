import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent.parent / "data"

st.set_page_config(
    page_title="ふるさと納税ダッシュボード",
    page_icon="🏡",
    layout="wide",
)

st.title("🏡 ふるさと納税 分析ダッシュボード")
st.caption("出典: 総務省現況調査 ／ 対象: 2008〜2024年度")


# ── ユーティリティ ──────────────────────────────────────────────
@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data
def load_timeseries():
    df = load_csv("jichitai_timeseries.csv")
    if df.empty:
        return df
    exclude = ["全国合計", "合計", "市町村合計"]
    return df[~df["市区町村"].isin(exclude) & ~df["都道府県"].isin(exclude)].copy()


@st.cache_data
def calc_ranking(df_ts: pd.DataFrame) -> pd.DataFrame:
    df = df_ts.copy()
    df["順位"] = df.groupby("年度")["受入額_億円"].rank(ascending=False, method="min").astype(int)
    return df


def signal(value, low, high, inverse=False):
    if inverse:
        return "🟢" if value <= low else ("🟡" if value <= high else "🔴")
    return "🟢" if value >= high else ("🟡" if value >= low else "🔴")


def fmt_oku(value: float) -> str:
    """億円表記。1兆（10,000億）以上は「X兆Y,ZZZ億円」形式で表示"""
    v = int(round(value))
    if v >= 10000:
        cho = v // 10000
        oku = v % 10000
        return f"{cho}兆{oku:,}億円" if oku else f"{cho}兆円"
    return f"{v:,}億円"


DB_TAX      = "lhcloud_tax_data"
DB_DELIVERY = "lhcloud_deli_data"
DB_NOTE     = "※ 本DBはふるさと納税市場全体の約48%をカバー。総務省公開値との比較時は市場シェアを考慮すること。"


def detect_db_result_type(df: pd.DataFrame) -> str:
    """CSVの列名からどのクエリの結果かを自動判別する"""
    cols = set(df.columns)
    if "ポータル区分" in cols:
        return "portal"
    if "解析用カテゴリ" in cols or "カテゴリ" in cols:
        return "category"
    if "年月" in cols:
        return "monthly"
    if "種別" in cols and ("件数比率" in cols or "件数" in cols):
        return "subscription"
    if "寄附者都道府県" in cols:
        return "demographics"
    if "年度" in cols and "受付件数" in cols:
        return "yearly"
    return "unknown"


DB_RESULT_LABELS = {
    "portal":       "ポータル別内訳",
    "category":     "返礼品カテゴリ別",
    "monthly":      "月別トレンド",
    "subscription": "定期便比率",
    "demographics": "寄附者属性",
    "yearly":       "年度別推移",
    "unknown":      "不明（列名を確認してください）",
}


def generate_integrated_md(
    pref: str, muni: str, muni_code: str,
    public_metrics: dict,
    db_results: dict,
) -> str:
    """公開データ + 内部DBデータを統合した分析レポートを生成"""
    today = date.today().strftime("%Y年%m月%d日")
    kifu   = public_metrics.get("受入額_億円", "N/A")
    rank   = public_metrics.get("全国順位", "N/A")
    growth = public_metrics.get("3年成長率", "N/A")
    keihi  = public_metrics.get("経費率", "N/A")

    kifu_str   = f"{kifu:.1f} 億円" if isinstance(kifu, float) else str(kifu)
    growth_str = f"{growth:+.1f}% / 年" if isinstance(growth, float) else str(growth)
    keihi_str  = f"{keihi:.1f}%" if isinstance(keihi, float) else str(keihi)

    # 内部DBセクション生成
    db_sections = []

    # 年度別推移 → 公開データとのカバー率照合
    if "yearly" in db_results:
        df_y = db_results["yearly"]
        # 最新年度のDB件数を公開データと照合してカバー率を推定
        db_section = "### 内部DB — 年度別推移\n\n"
        db_section += df_y.to_markdown(index=False) + "\n\n"
        if not df_y.empty and "寄附金額合計" in df_y.columns:
            latest_db = df_y.sort_values("年度").iloc[-1]
            db_kifu_oku = latest_db["寄附金額合計"] / 1e8 if latest_db["寄附金額合計"] > 1000 else latest_db["寄附金額合計"]
            if isinstance(kifu, float) and kifu > 0:
                coverage = db_kifu_oku / kifu * 100
                db_section += f"> DB実績 {db_kifu_oku:.1f} 億円 ÷ 総務省公開値 {kifu:.1f} 億円 ＝ **当自治体のDB捕捉率 {coverage:.1f}%**\n"
        db_sections.append(db_section)

    # ポータル別内訳
    if "portal" in db_results:
        df_p = db_results["portal"]
        db_sections.append("### 内部DB — ポータル別内訳\n\n" + df_p.to_markdown(index=False) + "\n")

    # 返礼品カテゴリ別
    if "category" in db_results:
        df_c = db_results["category"]
        db_sections.append("### 内部DB — 返礼品カテゴリ別実績\n\n" + df_c.to_markdown(index=False) + "\n")

    # 月別トレンド
    if "monthly" in db_results:
        df_m = db_results["monthly"]
        db_sections.append("### 内部DB — 月別受付トレンド\n\n" + df_m.to_markdown(index=False) + "\n")

    # 定期便比率
    if "subscription" in db_results:
        df_s = db_results["subscription"]
        db_sections.append("### 内部DB — 定期便比率\n\n" + df_s.to_markdown(index=False) + "\n")

    # 寄附者属性
    if "demographics" in db_results:
        df_d = db_results["demographics"]
        db_sections.append("### 内部DB — 寄附者属性（上位20件）\n\n" + df_d.head(20).to_markdown(index=False) + "\n")

    db_block = "\n".join(db_sections) if db_sections else "_（内部DBデータ未取り込み）_"

    # 統合仮説
    hypotheses = []
    if "portal" in db_results:
        df_p = db_results["portal"]
        if not df_p.empty and "ポータル区分" in df_p.columns:
            top_portal = df_p.sort_values("件数", ascending=False).iloc[0]["ポータル区分"] if "件数" in df_p.columns else "不明"
            hypotheses.append(f"ポータル構成: 最大シェアは **{top_portal}**。集中リスクと2025年10月以降のポータル変化を追跡すること")
    if "category" in db_results:
        df_c = db_results["category"]
        if not df_c.empty:
            ctg_col = "解析用カテゴリ" if "解析用カテゴリ" in df_c.columns else "カテゴリ"
            amt_col = "寄附金額合計" if "寄附金額合計" in df_c.columns else "金額合計"
            if ctg_col in df_c.columns and amt_col in df_c.columns:
                top_ctg = df_c.sort_values(amt_col, ascending=False).iloc[0][ctg_col]
                hypotheses.append(f"返礼品カテゴリ: 最大カテゴリは **{top_ctg}**。全国人気カテゴリ（米・牛肉・日用品）との重複・差別化を検討")
    if "subscription" in db_results:
        df_s = db_results["subscription"]
        if not df_s.empty and "種別" in df_s.columns and "件数比率" in df_s.columns:
            teiki = df_s[df_s["種別"] == "定期便"]["件数比率"].values
            if len(teiki) > 0:
                hypotheses.append(f"定期便比率: **{teiki[0]:.1f}%**。全国平均と比較してリピーター施策の余地を評価")
    if isinstance(growth, float) and growth > 10:
        hypotheses.append(f"成長率 {growth:+.1f}%/年 — 公開データで確認済み。内部DBのポータル別・月別で牽引要因を特定すること")
    if not hypotheses:
        hypotheses.append("内部DB取り込みデータから特段の異常値なし。詳細分析を追加で実施推奨")
    hyp_text = "\n".join(f"{i+1}. {h}" for i, h in enumerate(hypotheses))

    has_db = bool(db_sections)
    db_count = len(db_results)

    return f"""# ふるさと納税 統合分析レポート
> 生成日: {today}　／　対象: {pref} {muni}（自治体コード: `{muni_code}`）
> **公開データ（総務省）＋ 内部DBデータ（{db_count}クエリ）の統合レポート**

---

## 1. 公開データによる観察（総務省現況調査）

| 指標 | 値 |
|---|---|
| 受入額（2024年度） | {kifu_str} |
| 全国順位（2024年度） | {rank} 位 |
| 3年平均成長率 | {growth_str} |
| 経費率（2024年度） | {keihi_str} |

> {DB_NOTE}

---

## 2. 内部DBデータによる観察

{db_block}

---

## 3. 統合仮説（公開データ × 内部DB）

{hyp_text}

---

## 4. 次のアクション候補

- [ ] ポータル別シェアと総務省「ポータル費率」を突合して費用対効果を算出
- [ ] 返礼品カテゴリの伸び率を公開データの成長率と比較
- [ ] 定期便比率が低い場合はリピーター施策の余地を検討
- [ ] 月別トレンドで2025年10月ポイント禁止後の影響を定量化
- [ ] 類似自治体（ベンチマーク）の内部DB実績と横並び比較

---
*このレポートはふるさと納税分析ダッシュボードにより自動生成されました。*
*公開データ出典: 総務省現況調査 ／ 内部DB: {DB_TAX} / {DB_DELIVERY}*
"""


def generate_municipality_md(
    pref: str, muni: str, muni_code: str,
    metrics: dict,
) -> str:
    """自治体プロファイルのMDレポートを生成（内部DBクエリ付き）"""
    today = date.today().strftime("%Y年%m月%d日")
    kifu   = metrics.get("受入額_億円", "N/A")
    rank   = metrics.get("全国順位", "N/A")
    growth = metrics.get("3年成長率", "N/A")
    keihi  = metrics.get("経費率", "N/A")
    portal = metrics.get("ポータル費率", "N/A")

    hypotheses = []
    if isinstance(keihi, float) and keihi < 40:
        hypotheses.append("経費率が全国中央値より低い → 返礼品調達コスト抑制またはポータル依存度が低い可能性。`apply_name`別シェアで確認推奨")
    elif isinstance(keihi, float) and keihi > 50:
        hypotheses.append("経費率が5割ルールに接近 → 費目別の削減余地を精査。ポータル手数料・広報費の内訳を確認すること")
    if isinstance(growth, float) and growth > 10:
        hypotheses.append(f"3年成長率 {growth:+.1f}%/年 → 新規ポータル開拓か返礼品カテゴリ拡充が牽引している可能性。`apply_name`・`goods_ana_ctg_name`の年度別推移で検証")
    elif isinstance(growth, float) and growth < 0:
        hypotheses.append(f"3年成長率 {growth:+.1f}%/年 → ポータル集中リスクまたは返礼品鮮度低下が懸念。競合自治体の返礼品カテゴリと比較")
    if isinstance(portal, float) and portal > 15:
        hypotheses.append(f"ポータル費率 {portal:.1f}% → 手数料負担が高い。2025年10月制度改正後のポータル構成変化を追跡すること")
    if not hypotheses:
        hypotheses.append("特段の異常値なし。類似自治体との比較および返礼品カテゴリの詳細分析でさらなる仮説を検討")
    hyp_text = "\n".join(f"{i+1}. {h}" for i, h in enumerate(hypotheses))

    kifu_str   = f"{kifu:.1f} 億円" if isinstance(kifu, float) else str(kifu)
    growth_str = f"{growth:+.1f}% / 年" if isinstance(growth, float) else str(growth)
    keihi_str  = f"{keihi:.1f}%" if isinstance(keihi, float) else str(keihi)
    portal_str = f"{portal:.1f}%" if isinstance(portal, float) else str(portal)

    return f"""# ふるさと納税 分析レポート
> 生成日: {today}　／　対象: {pref} {muni}（自治体コード: `{muni_code}`）

---

## 1. 公開データによる観察（総務省現況調査）

| 指標 | 値 |
|---|---|
| 受入額（2024年度） | {kifu_str} |
| 全国順位（2024年度） | {rank} 位 |
| 3年平均成長率 | {growth_str} |
| 経費率（2024年度） | {keihi_str} |
| ポータル費率（2024年度） | {portal_str} |

> {DB_NOTE}

---

## 2. 仮説

{hyp_text}

---

## 3. 内部DBへのクエリ提案

> **DB:** `dev` / **スキーマ:** `public` / **ワークグループ:** `wg-ledghome-bigdata`
> **必須フィルタ:** `tax_st_id = 2`（寄附完了）、`delete_flg = 0`

### 3-1. 年度別 受付件数・金額推移
```sql
SELECT
    tax_year                                            AS 年度,
    COUNT(*)                                            AS 受付件数,
    SUM(tax_amount)                                     AS 寄附金額合計,
    ROUND(AVG(tax_amount))                              AS 平均寄附金額
FROM {DB_TAX}
WHERE municipality_code = '{muni_code}'
  AND tax_st_id  = 2
  AND delete_flg = 0
GROUP BY tax_year
ORDER BY tax_year;
```

### 3-2. ポータルサイト別 内訳（表記ゆれ吸収）
```sql
SELECT
    CASE
        WHEN apply_name ILIKE '%楽天%' OR apply_name ILIKE '%Rakuten%'
             THEN '楽天'
        WHEN apply_name ILIKE '%さとふる%' OR apply_name ILIKE '%チョイス%'
             THEN 'さとふる／ふるさとチョイス'
        WHEN apply_name ILIKE '%ふるなび%'
             THEN 'ふるなび'
        WHEN apply_name ILIKE '%Yahoo%' OR apply_name ILIKE '%ヤフー%'
             THEN 'Yahoo!ふるさと納税'
        WHEN apply_name ILIKE '%ANA%' OR apply_name ILIKE '%ＡＮＡ%'
             THEN 'ANA'
        WHEN apply_name ILIKE '%JAL%'
             THEN 'JAL'
        WHEN apply_name ILIKE '%au PAY%' OR apply_name ILIKE '%auPAY%'
             THEN 'au PAY'
        ELSE COALESCE(NULLIF(apply_name, ''), '直接受付・その他')
    END                                                 AS ポータル区分,
    COUNT(*)                                            AS 件数,
    SUM(tax_amount)                                     AS 金額合計,
    ROUND(AVG(tax_amount))                              AS 平均金額,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1)  AS 件数シェア率
FROM {DB_TAX}
WHERE municipality_code = '{muni_code}'
  AND tax_st_id  = 2
  AND delete_flg = 0
  AND tax_year   = 2024
GROUP BY ポータル区分
ORDER BY 金額合計 DESC;
```

### 3-3. 返礼品カテゴリ別 実績
```sql
SELECT
    d.goods_ana_ctg_name                                AS 解析用カテゴリ,
    COUNT(*)                                            AS 件数,
    SUM(d.g_tax_amount)                                 AS 寄附金額合計,
    ROUND(AVG(d.g_tax_amount))                          AS 平均単価,
    ROUND(100.0 * SUM(d.g_tax_amount)
          / SUM(SUM(d.g_tax_amount)) OVER(), 1)         AS 金額シェア率
FROM {DB_DELIVERY} d
WHERE d.municipality_code = '{muni_code}'
  AND d.tax_st_id  = 2
  AND d.tax_year   = 2024
GROUP BY d.goods_ana_ctg_name
ORDER BY 寄附金額合計 DESC;
```

### 3-4. 寄附者の地域・属性分析
```sql
SELECT
    t.tax_pref                                          AS 寄附者都道府県,
    t.tax_sex                                           AS 性別,
    FLOOR(
        DATEDIFF('year', t.tax_birthday::DATE, CURRENT_DATE) / 10
    ) * 10                                              AS 年代,
    COUNT(*)                                            AS 件数,
    SUM(t.tax_amount)                                   AS 金額合計
FROM {DB_TAX} t
WHERE t.municipality_code = '{muni_code}'
  AND t.tax_st_id  = 2
  AND t.delete_flg = 0
  AND t.tax_year   = 2024
  AND t.tax_birthday IS NOT NULL
GROUP BY t.tax_pref, t.tax_sex, 年代
ORDER BY 金額合計 DESC
LIMIT 30;
```

### 3-5. 定期便（リピーター）比率
```sql
SELECT
    CASE WHEN d.set_flg = 1 THEN '定期便' ELSE '通常便' END AS 種別,
    COUNT(*)                                            AS 件数,
    SUM(d.g_tax_amount)                                 AS 金額合計,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1)  AS 件数比率
FROM {DB_DELIVERY} d
WHERE d.municipality_code = '{muni_code}'
  AND d.tax_st_id = 2
  AND d.tax_year  = 2024
GROUP BY d.set_flg;
```

### 3-6. 月別受付トレンド（季節性・キャンペーン影響確認）
```sql
SELECT
    TO_CHAR(DATE_TRUNC('month', t.uketsuke_date), 'YYYY年MM月') AS 年月,
    COUNT(*)                                            AS 件数,
    SUM(t.tax_amount)                                   AS 金額合計
FROM {DB_TAX} t
WHERE t.municipality_code = '{muni_code}'
  AND t.tax_st_id  = 2
  AND t.delete_flg = 0
  AND t.tax_year   = 2024
GROUP BY DATE_TRUNC('month', t.uketsuke_date)
ORDER BY DATE_TRUNC('month', t.uketsuke_date);
-- ※ 2023年9月・2025年9月は制度改正前駆け込みにより異常伸長の可能性あり
-- ※ 5・10・15・20・25・30日は楽天・Yahoo!キャンペーンによる件数増加傾向あり
```

---

## 4. 分析時の留意事項（7つの観点）

以下の観点でクエリ結果を検証・コメントすること：

1. **データの正確性** — 件数・金額の総務省公開値との整合性（DB市場シェア約48%を考慮）
2. **トレンドの解釈** — 増減の要因仮説（ポータル変更・返礼品改廃・競合自治体の影響）
3. **異常値・外れ値** — 突出した月・カテゴリの有無
4. **季節性・時期的特徴** — 2023年9月・2025年9月の駆け込み需要、5と0のつく日キャンペーン効果
5. **比較対象との文脈** — 昨対比・同規模自治体との比較
6. **ビジネス上のインサイト** — ポータル最適化・返礼品カテゴリ戦略への示唆
7. **注意事項・データの限界** — 直近1ヶ月のNULL多発時はデータ欠損の可能性あり

---

## 5. 次のアクション候補

- [ ] 上記クエリを社内DB（Claude Code経由）で実行し、仮説を検証
- [ ] ポータル別シェアと総務省「ポータル費率」を突合
- [ ] 返礼品カテゴリ構成比を全国平均・類似自治体と比較
- [ ] 定期便比率が低い場合はリピーター施策の余地を検討
- [ ] 2025年10月以降のポータル戦略変化を月別トレンドで確認

---
*このレポートはふるさと納税分析ダッシュボードにより自動生成されました。*
*公開データ出典: 総務省現況調査 ／ 内部DB: {DB_TAX} / {DB_DELIVERY}*
"""


def generate_list_md(df_list: pd.DataFrame, conditions: str) -> str:
    """抽出自治体リストのMDレポートを生成"""
    today = date.today().strftime("%Y年%m月%d日")
    codes = df_list["団体コード"].dropna().astype(str).unique().tolist() if "団体コード" in df_list.columns else []
    codes_sql = ", ".join(f"'{c}'" for c in codes[:50])

    table_rows = []
    for _, r in df_list.head(30).iterrows():
        yr   = str(r.get("年度", ""))
        pref = r.get("都道府県", "")
        muni = r.get("市区町村", "")
        kifu = f"{r['受入額_億円']:.1f}" if pd.notna(r.get("受入額_億円")) else ""
        rate = f"{r['経費率（%）']:.1f}%" if pd.notna(r.get("経費率（%）")) else ""
        table_rows.append(f"| {yr} | {pref} | {muni} | {kifu} | {rate} |")
    table_str = "\n".join(table_rows)

    return f"""# ふるさと納税 自治体抽出レポート
> 生成日: {today}

---

## 1. 抽出条件

{conditions}

**抽出件数: {len(df_list)} 件**

> {DB_NOTE}

---

## 2. 抽出自治体リスト（上位30件）

| 年度 | 都道府県 | 市区町村 | 受入額（億円） | 経費率 |
|---|---|---|---|---|
{table_str}

---

## 3. 内部DBへの一括クエリ

> **DB:** `dev` / **スキーマ:** `public` / **ワークグループ:** `wg-ledghome-bigdata`
> **必須フィルタ:** `tax_st_id = 2`（寄附完了）、`delete_flg = 0`

### 3-1. 対象自治体の年度別受付サマリー
```sql
SELECT
    t.municipality_name                                 AS 自治体名,
    t.municipality_code                                 AS 自治体コード,
    t.tax_year                                          AS 年度,
    COUNT(*)                                            AS 受付件数,
    SUM(t.tax_amount)                                   AS 寄附金額合計,
    ROUND(AVG(t.tax_amount))                            AS 平均寄附金額
FROM {DB_TAX} t
WHERE t.municipality_code IN ({codes_sql or "'（コードが見つかりません）'"})
  AND t.tax_st_id  = 2
  AND t.delete_flg = 0
GROUP BY t.municipality_name, t.municipality_code, t.tax_year
ORDER BY t.municipality_code, t.tax_year;
```

### 3-2. 対象自治体のポータル別シェア（2024年度）
```sql
SELECT
    t.municipality_name                                 AS 自治体名,
    CASE
        WHEN t.apply_name ILIKE '%楽天%' OR t.apply_name ILIKE '%Rakuten%'
             THEN '楽天'
        WHEN t.apply_name ILIKE '%さとふる%' OR t.apply_name ILIKE '%チョイス%'
             THEN 'さとふる／ふるさとチョイス'
        WHEN t.apply_name ILIKE '%ふるなび%'    THEN 'ふるなび'
        WHEN t.apply_name ILIKE '%Yahoo%'       THEN 'Yahoo!ふるさと納税'
        WHEN t.apply_name ILIKE '%ANA%'         THEN 'ANA'
        WHEN t.apply_name ILIKE '%JAL%'         THEN 'JAL'
        WHEN t.apply_name ILIKE '%au PAY%'      THEN 'au PAY'
        ELSE COALESCE(NULLIF(t.apply_name, ''), '直接受付・その他')
    END                                                 AS ポータル区分,
    COUNT(*)                                            AS 件数,
    SUM(t.tax_amount)                                   AS 金額合計
FROM {DB_TAX} t
WHERE t.municipality_code IN ({codes_sql or "'（コードが見つかりません）'"})
  AND t.tax_st_id  = 2
  AND t.delete_flg = 0
  AND t.tax_year   = 2024
GROUP BY t.municipality_name, ポータル区分
ORDER BY t.municipality_name, 金額合計 DESC;
```

### 3-3. 対象自治体の返礼品カテゴリ別実績（2024年度）
```sql
SELECT
    d.municipality_name                                 AS 自治体名,
    d.goods_ana_ctg_name                                AS カテゴリ,
    COUNT(*)                                            AS 件数,
    SUM(d.g_tax_amount)                                 AS 金額合計
FROM {DB_DELIVERY} d
WHERE d.municipality_code IN ({codes_sql or "'（コードが見つかりません）'"})
  AND d.tax_st_id = 2
  AND d.tax_year  = 2024
GROUP BY d.municipality_name, d.goods_ana_ctg_name
ORDER BY d.municipality_name, 金額合計 DESC;
```

---

## 4. 次のアクション候補

- [ ] 上記クエリを社内DB（Claude Code経由）で実行
- [ ] ポータル構成比を総務省経費データと突合し、費用対効果を算出
- [ ] 返礼品カテゴリの伸び率を公開データの成長率と比較
- [ ] 2025年10月以降のポータル戦略変化を月別トレンドで確認

---
*このレポートはふるさと納税分析ダッシュボードにより自動生成されました。*
*公開データ出典: 総務省現況調査 ／ 内部DB: {DB_TAX} / {DB_DELIVERY}*
"""


# ── データ読み込み ──────────────────────────────────────────────
df_market       = load_csv("market_trends_annual.csv")
df_ranking      = load_csv("kifu_ranking_by_year.csv")
df_keihi        = load_csv("keihi_annual.csv")
df_ryushutsu    = load_csv("toshi_ryushutsu.csv")
df_detail       = load_csv("jichitai_detail.csv")
df_detail_multi = load_csv("jichitai_detail_multi.csv")
df_ts           = load_timeseries()


# ── サイドバー ──────────────────────────────────────────────────
with st.sidebar:
    st.header("📎 リンク")
    st.markdown("[📁 総務省 現況調査](https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/)")
    st.markdown("[📖 GitHubリポジトリ](https://github.com/tgsoccer79-dot/my-project)")
    st.divider()
    st.caption("データ対象期間: 2008〜2024年度\n費目別詳細: 2019〜2024年度")


# ── タブ ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 市場全体を知る",
    "🏆 ランキングを見る",
    "🏘️ 自治体を深掘りする",
    "⚔️ 自治体を比較する",
    "🗾 地域の動きを見る",
    "🔬 経費・効率を分析する",
    "📤 データを抽出する",
])


# ═══════════════════════════════════════════════════════════════
# Tab 1: 市場全体を知る
# ═══════════════════════════════════════════════════════════════
with tab1:
    df_m = df_market.copy()
    df_m["year"] = df_m["year"].astype(int)

    year_min, year_max = int(df_m["year"].min()), int(df_m["year"].max())
    year_range = st.slider("表示年度", year_min, year_max, (year_min, year_max), key="trend_slider")
    df_m = df_m[(df_m["year"] >= year_range[0]) & (df_m["year"] <= year_range[1])].copy()

    latest = df_m.iloc[-1]
    prev   = df_m.iloc[-2] if len(df_m) > 1 else latest
    c1, c2, c3 = st.columns(3)
    delta_oku = int(latest['kifu_total_oku']) - int(prev['kifu_total_oku'])
    c1.metric("受入総額", fmt_oku(latest['kifu_total_oku']),
              f"{'+' if delta_oku >= 0 else ''}{fmt_oku(abs(delta_oku))}（前年度比）")
    c2.metric("受入件数", f"{int(latest['cases_man']):,} 万件")
    c3.metric("経費率", f"{latest['keihi_rate_pct']}%", delta_color="inverse")

    df_m["年度"] = df_m["year"].astype(str) + "年度"
    fig = px.bar(df_m, x="年度", y="kifu_total_oku",
                 labels={"kifu_total_oku": "受入総額（億円）"},
                 color_discrete_sequence=["#2ecc71"], text="kifu_total_oku")
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont_size=10)

    events = {"2015": "ワンストップ特例・控除上限2倍", "2019": "3割・地場産品規制", "2023": "ポータルサイト規制予告"}
    for yr, label in events.items():
        if year_range[0] <= int(yr) <= year_range[1]:
            fig.add_vline(x=f"{yr}年度", line_dash="dot", line_color="gray", opacity=0.6)
            fig.add_annotation(x=f"{yr}年度", y=df_m["kifu_total_oku"].max() * 0.85,
                               text=label, showarrow=False, font_size=10,
                               textangle=-90, xshift=10)

    fig.update_layout(height=440, margin=dict(t=20, b=20), xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("点線: 主要制度改正年度 ／ 出典: 総務省「ふるさと納税に関する現況調査結果」")

    with st.expander("生データを見る"):
        st.dataframe(df_m[["年度", "kifu_total_oku", "cases_man", "keihi_rate_pct"]]
                     .rename(columns={"kifu_total_oku": "受入総額（億円）", "cases_man": "受入件数（万件）",
                                      "keihi_rate_pct": "経費率（%）"}),
                     use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Tab 2: ランキングを見る（年間ランキング ＋ 順位変動バンプチャート）
# ═══════════════════════════════════════════════════════════════
with tab2:
    rank_menu = st.radio("表示モード", ["年間ランキング", "順位変動（バンプチャート）"], horizontal=True)

    if rank_menu == "年間ランキング":
        st.subheader("自治体別 寄附額ランキング")
        col_l, col_r = st.columns([1, 3])
        with col_l:
            top_n = st.slider("表示件数", 5, 50, 20)

        df_yr = (df_detail[["都道府県", "市区町村", "受入額_億円", "経費率合計", "ポータル費_億円"]]
                 .sort_values("受入額_億円", ascending=False).head(top_n).reset_index(drop=True))
        df_yr.index += 1
        df_yr["自治体"] = df_yr["都道府県"] + " " + df_yr["市区町村"]
        df_yr["経費率"] = (df_yr["経費率合計"] * 100).round(1).astype(str) + "%"

        with col_r:
            fig = px.bar(df_yr, x="受入額_億円", y="自治体", orientation="h",
                         color="受入額_億円", color_continuous_scale="Greens", text="受入額_億円",
                         labels={"受入額_億円": "受入額（億円）"})
            fig.update_traces(texttemplate="%{text:.1f} 億円", textposition="outside")
            fig.update_layout(height=max(400, top_n * 22), margin=dict(t=10, b=10),
                              yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_yr[["自治体", "受入額_億円", "経費率", "ポータル費_億円"]]
                     .rename(columns={"受入額_億円": "受入額（億円）", "ポータル費_億円": "ポータル費（億円）"}),
                     use_container_width=True)
        st.info("⚠️ 2024年度1位の宝塚市（約257億円）は市立病院への大口個人寄附254億円を含む特殊事例。通常の返礼品目的では白糠町（約212億円）が実質1位。")

    else:
        st.subheader("順位変動バンプチャート")
        st.caption("上位自治体の順位がどう変化したかを追います。")

        if df_ts.empty:
            st.info("時系列データが見つかりません。")
        else:
            df_ranked2 = calc_ranking(df_ts)
            years_avail2 = sorted(df_ranked2["年度"].unique())

            col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
            with col_b1:
                bump_start = st.selectbox("開始年度", years_avail2, index=0, key="bump_start")
            with col_b2:
                bump_end = st.selectbox("終了年度", [y for y in years_avail2 if y >= bump_start],
                                        index=len([y for y in years_avail2 if y >= bump_start]) - 1,
                                        key="bump_end")
            with col_b3:
                bump_n = st.slider("追跡する自治体数（直近順位上位）", 10, 40, 20)

            df_bump_base = df_ranked2[df_ranked2["年度"].between(bump_start, bump_end)]
            top_munis = (df_ranked2[df_ranked2["年度"] == bump_end]
                         .nsmallest(bump_n, "順位")["市区町村"].tolist())
            df_bump = df_bump_base[df_bump_base["市区町村"].isin(top_munis)].copy()
            df_bump["年度ラベル"] = df_bump["年度"].astype(str) + "年度"

            fig_bump = px.line(df_bump, x="年度ラベル", y="順位", color="市区町村",
                               markers=True, line_shape="spline",
                               hover_data={"受入額_億円": True, "都道府県": True, "年度ラベル": False})
            fig_bump.update_yaxes(autorange="reversed", title="全国順位（上位ほど上）")
            fig_bump.update_xaxes(title="年度")
            fig_bump.update_traces(line_width=2, marker_size=7)
            fig_bump.update_layout(height=520, margin=dict(t=20, b=20),
                                   legend=dict(orientation="v", x=1.02, y=1))
            st.plotly_chart(fig_bump, use_container_width=True)
            st.caption("線が上に向かう＝順位上昇。同名自治体は都道府県で区別しています。")

            col_u, col_d = st.columns(2)
            df_bump_c = df_ranked2[df_ranked2["年度"] == bump_end][["市区町村", "都道府県", "順位", "受入額_億円"]].rename(
                columns={"順位": f"順位_{bump_end}年度", "受入額_億円": f"受入額_{bump_end}年度（億円）"})
            df_bump_p = df_ranked2[df_ranked2["年度"] == bump_start][["市区町村", "都道府県", "順位"]].rename(
                columns={"順位": f"順位_{bump_start}年度"})
            df_bump_diff = df_bump_c.merge(df_bump_p, on=["市区町村", "都道府県"])
            df_bump_diff["順位変動"] = df_bump_diff[f"順位_{bump_start}年度"] - df_bump_diff[f"順位_{bump_end}年度"]
            df_bump_diff = df_bump_diff[df_bump_diff["市区町村"].isin(top_munis)]

            with col_u:
                st.markdown(f"#### 📈 上昇した自治体（{bump_start}→{bump_end}年度）")
                up = df_bump_diff[df_bump_diff["順位変動"] > 0].sort_values("順位変動", ascending=False).head(10)
                up["順位変動"] = up["順位変動"].apply(lambda x: f"▲{int(x)}")
                st.dataframe(up[["市区町村", "都道府県", "順位変動", f"受入額_{bump_end}年度（億円）"]],
                             use_container_width=True, hide_index=True)
            with col_d:
                st.markdown(f"#### 📉 下降した自治体（{bump_start}→{bump_end}年度）")
                dn = df_bump_diff[df_bump_diff["順位変動"] < 0].sort_values("順位変動").head(10)
                dn["順位変動"] = dn["順位変動"].apply(lambda x: f"▼{abs(int(x))}")
                st.dataframe(dn[["市区町村", "都道府県", "順位変動", f"受入額_{bump_end}年度（億円）"]],
                             use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 3: 自治体を深掘りする
# ═══════════════════════════════════════════════════════════════
with tab3:
    if df_ts.empty:
        st.info("時系列データが見つかりません。")
    else:
        df_ranked3 = calc_ranking(df_ts)

        prefs = sorted(df_ts["都道府県"].unique())
        col_s1, col_s2, col_s3 = st.columns([1, 1, 2])
        with col_s1:
            sel_pref = st.selectbox("都道府県", prefs,
                                    index=prefs.index("北海道") if "北海道" in prefs else 0,
                                    key="prof_pref")
        with col_s2:
            munis = sorted(df_ts[df_ts["都道府県"] == sel_pref]["市区町村"].unique())
            default = "白糠町" if "白糠町" in munis else munis[0]
            sel_muni = st.selectbox("市区町村", munis, index=munis.index(default), key="prof_muni")
        with col_s3:
            search = st.text_input("🔍 自治体名で検索", placeholder="例: 都城市")
            if search:
                hits = df_ts[df_ts["市区町村"].str.contains(search, na=False)]["市区町村"].unique()
                if len(hits) == 1:
                    sel_muni = hits[0]
                    st.success(f"→ {sel_muni} に切り替えました")
                elif len(hits) > 1:
                    sel_muni = st.selectbox("候補", sorted(hits), key="search_result")

        df_muni_ts = df_ranked3[df_ranked3["市区町村"] == sel_muni].sort_values("年度")
        df_muni_d  = df_detail[df_detail["市区町村"] == sel_muni] if not df_detail.empty else pd.DataFrame()

        if df_muni_ts.empty:
            st.warning(f"{sel_muni} のデータが見つかりません。")
        else:
            latest_r = df_muni_ts.iloc[-1]
            prev_r   = df_muni_ts.iloc[-2] if len(df_muni_ts) > 1 else latest_r

            st.markdown("---")
            st.markdown(f"### 🩺 {sel_pref} {sel_muni} 診断カード")
            st.caption("※ 全指標は参考値です。行政判断の根拠には使用しないでください。")

            df_all_latest = df_ranked3[df_ranked3["年度"] == df_ranked3["年度"].max()]
            mean_kifu = df_all_latest["受入額_億円"].mean()
            std_kifu  = df_all_latest["受入額_億円"].std()
            mean_rank = df_all_latest["順位"].mean()
            std_rank  = df_all_latest["順位"].std()

            kifu_hensachi = int(50 + (latest_r["受入額_億円"] - mean_kifu) / std_kifu * 10) if std_kifu > 0 else 50
            rank_hensachi = int(50 + (mean_rank - latest_r["順位"]) / std_rank * 10) if std_rank > 0 else 50

            if len(df_muni_ts) >= 4:
                growth_3y = ((latest_r["受入額_億円"] / df_muni_ts.iloc[-4]["受入額_億円"]) ** (1/3) - 1) * 100
            else:
                growth_3y = 0.0

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("受入額（2024年度）", f"{latest_r['受入額_億円']:.1f} 億円",
                      f"{latest_r['受入額_億円'] - prev_r['受入額_億円']:+.1f}（前年度比）")
            d2.metric("全国順位（2024年度）", f"{int(latest_r['順位'])} 位",
                      f"{int(prev_r['順位']) - int(latest_r['順位']):+d} 位")
            d3.metric("3年平均成長率", f"{growth_3y:+.1f}% / 年")
            if not df_muni_d.empty:
                dr = df_muni_d.iloc[0]
                d4.metric("経費率（2024年度）", f"{dr['経費率合計']*100:.1f}%", delta_color="inverse")

            st.markdown("#### 信号機チェック")
            sig_cols = st.columns(5)
            sig_items = [
                ("受入額 偏差値", kifu_hensachi, signal(kifu_hensachi, 45, 55)),
                ("順位 偏差値",   rank_hensachi, signal(rank_hensachi, 45, 55)),
                ("3年成長率",     growth_3y,     signal(growth_3y, 0, 10)),
            ]
            if not df_muni_d.empty:
                dr = df_muni_d.iloc[0]
                keihi_pct  = dr["経費率合計"] * 100
                portal_pct = dr["ポータル費_億円"] / dr["受入額_億円"] * 100 if dr["受入額_億円"] > 0 else 0
                sig_items += [
                    ("経費率",     keihi_pct,  signal(keihi_pct, 40, 50, inverse=True)),
                    ("ポータル費率", portal_pct, signal(portal_pct, 10, 15, inverse=True)),
                ]
            for i, (label, val, sig) in enumerate(sig_items):
                with sig_cols[i]:
                    st.markdown(f"**{sig} {label}**")
                    st.write(f"{val:.1f}" if isinstance(val, float) else val)

            st.divider()

            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 📈 寄附額の推移")
                df_muni_ts["年度ラベル"] = df_muni_ts["年度"].astype(str) + "年度"
                fig_g = px.area(df_muni_ts, x="年度ラベル", y="受入額_億円",
                                labels={"年度ラベル": "年度", "受入額_億円": "受入額（億円）"},
                                color_discrete_sequence=["#2ecc71"])
                fig_g.update_layout(height=300, margin=dict(t=10, b=10))
                st.plotly_chart(fig_g, use_container_width=True)
            with g2:
                st.markdown("#### 🏅 全国順位の推移")
                fig_r = px.line(df_muni_ts, x="年度ラベル", y="順位", markers=True,
                                labels={"年度ラベル": "年度"},
                                color_discrete_sequence=["#e74c3c"])
                fig_r.update_yaxes(autorange="reversed")
                fig_r.update_layout(height=300, margin=dict(t=10, b=10))
                st.plotly_chart(fig_r, use_container_width=True)

            # 経費内訳（多年度）
            df_muni_multi = (df_detail_multi[df_detail_multi["市区町村"] == sel_muni]
                             if not df_detail_multi.empty else pd.DataFrame())
            if not df_muni_multi.empty:
                st.markdown("#### 💰 経費構造の推移（2019〜2024年度）")
                cost_cols = {"返礼品調達費_円": "返礼品調達費", "送付費_円": "送付費",
                             "広報費_円": "広報費", "決済費_円": "決済費",
                             "事務費_円": "事務費", "その他費_円": "その他"}
                rows_trend = []
                for _, row_t in df_muni_multi.iterrows():
                    total_yen = row_t["受入額_億円"] * 1e8 if row_t["受入額_億円"] > 0 else None
                    for col_k, label_k in cost_cols.items():
                        val = row_t.get(col_k) or 0
                        rows_trend.append({
                            "年度": f"{int(row_t['年度'])}年度",
                            "費目": label_k,
                            "金額（億円）": round(val / 1e8, 2),
                            "比率（%）": round(val / total_yen * 100, 1) if total_yen else None,
                        })
                df_trend = pd.DataFrame(rows_trend)
                color_map = {"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                             "事務費": "#3498db", "決済費": "#9b59b6",
                             "広報費": "#95a5a6", "その他": "#bdc3c7"}
                t1, t2 = st.columns(2)
                with t1:
                    fig_trend = px.bar(df_trend, x="年度", y="金額（億円）", color="費目",
                                       barmode="stack", color_discrete_map=color_map,
                                       labels={"金額（億円）": "経費（億円）"})
                    fig_trend.update_layout(height=300, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_trend, use_container_width=True)
                with t2:
                    fig_rate = px.bar(df_trend, x="年度", y="比率（%）", color="費目",
                                      barmode="stack", color_discrete_map=color_map)
                    fig_rate.add_hline(y=50, line_dash="dash", line_color="red",
                                       annotation_text="5割ルール上限")
                    fig_rate.update_layout(height=300, margin=dict(t=10, b=10),
                                           yaxis_title="経費率（%）")
                    st.plotly_chart(fig_rate, use_container_width=True)
                if not df_muni_d.empty:
                    dr = df_muni_d.iloc[0]
                    portal_pct = dr["ポータル費_億円"] / dr["受入額_億円"] * 100 if dr["受入額_億円"] > 0 else 0
                    st.metric("2024年度 ポータル費", f"{dr['ポータル費_億円']:.2f} 億円",
                              f"受入額の {portal_pct:.1f}%")

            st.divider()

            # ベンチマーク推薦
            if not df_detail.empty and not df_muni_d.empty:
                st.markdown("#### 🎯 似た自治体ベンチマーク TOP5")
                st.caption("受入額・経費率・ポータル費率が近い自治体を自動推薦")
                dr = df_muni_d.iloc[0]
                df_bench = df_detail[(df_detail["市区町村"] != sel_muni) & (df_detail["受入額_億円"] > 0)].copy()
                for col in ["受入額_億円", "経費率合計", "ポータル費_億円"]:
                    col_std = df_bench[col].std()
                    df_bench[f"_d_{col}"] = ((df_bench[col] - dr[col]) / col_std) ** 2 if col_std > 0 else 0
                df_bench["類似スコア"] = df_bench["_d_受入額_億円"] + df_bench["_d_経費率合計"] + df_bench["_d_ポータル費_億円"]
                top5 = df_bench.nsmallest(5, "類似スコア")[["都道府県", "市区町村", "受入額_億円", "経費率合計", "ポータル費_億円"]].copy()
                top5["経費率"] = (top5["経費率合計"] * 100).round(1).astype(str) + "%"
                top5["推薦理由"] = top5.apply(
                    lambda r: f"受入額 {r['受入額_億円']:.1f}億円・経費率 {r['経費率合計']*100:.1f}%が近似", axis=1)
                st.dataframe(top5[["都道府県", "市区町村", "受入額_億円", "経費率", "推薦理由"]]
                             .rename(columns={"受入額_億円": "受入額（億円）"}),
                             use_container_width=True, hide_index=True)
                st.caption("※ 産業構造・人口・地域特性の類似性は考慮していません。参考情報としてご利用ください。")

            # MDレポート出力
            st.divider()
            st.markdown("#### 📄 分析レポートをMDで出力")
            st.caption("観察・仮説・内部DBクエリをまとめたMarkdownを生成します。Claude Codeへそのまま貼り付けて使えます。")

            muni_code_val = ""
            if not df_detail.empty:
                row_code = df_detail[df_detail["市区町村"] == sel_muni]
                if not row_code.empty and "団体コード" in row_code.columns:
                    muni_code_val = str(row_code.iloc[0]["団体コード"])

            md_metrics = {
                "受入額_億円": float(latest_r["受入額_億円"]) if pd.notna(latest_r["受入額_億円"]) else "N/A",
                "全国順位":   int(latest_r["順位"]),
                "3年成長率":  growth_3y,
                "経費率":     float(df_muni_d.iloc[0]["経費率合計"] * 100) if not df_muni_d.empty else "N/A",
                "ポータル費率": portal_pct if not df_muni_d.empty else "N/A",
            }
            md_content = generate_municipality_md(
                sel_pref, sel_muni, muni_code_val,
                md_metrics,
            )
            col_md1, col_md2 = st.columns([1, 3])
            with col_md1:
                st.download_button(
                    label="📥 MDをダウンロード",
                    data=md_content,
                    file_name=f"report_{sel_pref}_{sel_muni}.md",
                    mime="text/markdown",
                )
            with col_md2:
                if st.toggle("プレビューを表示", key="md_preview"):
                    st.markdown(md_content)

            # ─── 内部DBデータ取り込み ────────────────────────────────
            st.divider()
            st.markdown("#### 🔄 内部DBデータを取り込んで統合分析する")
            st.caption(
                "上のMDレポートのSQLを社内DBで実行し、結果CSVをここにアップロードすると"
                "公開データと統合して可視化・統合レポートを出力できます。"
            )

            uploaded_files = st.file_uploader(
                "内部DBのクエリ結果CSVをアップロード（複数同時可）",
                type=["csv"],
                accept_multiple_files=True,
                key=f"db_upload_{sel_muni}",
            )

            db_results: dict = {}
            if uploaded_files:
                for uf in uploaded_files:
                    try:
                        df_up = pd.read_csv(uf)
                        dtype = detect_db_result_type(df_up)
                        db_results[dtype] = df_up
                        label = DB_RESULT_LABELS.get(dtype, dtype)
                        if dtype == "unknown":
                            st.warning(f"⚠️ {uf.name}: 列名を認識できませんでした（{list(df_up.columns)[:5]}…）")
                        else:
                            st.success(f"✅ {uf.name} → **{label}** として取り込みました")
                    except Exception as e:
                        st.error(f"❌ {uf.name}: {e}")

            if db_results:
                st.markdown("---")

                # ── ポータル別内訳
                if "portal" in db_results:
                    st.markdown("##### 📡 ポータル別内訳（内部DB）")
                    df_p = db_results["portal"]
                    amt_col = "金額合計" if "金額合計" in df_p.columns else df_p.select_dtypes("number").columns[0]
                    fig_p = px.bar(
                        df_p.sort_values(amt_col, ascending=True),
                        x=amt_col, y="ポータル区分", orientation="h",
                        color=amt_col, color_continuous_scale="Blues",
                        text=amt_col, labels={amt_col: "金額合計（円）"},
                    )
                    fig_p.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                    fig_p.update_layout(height=320, margin=dict(t=10, b=10), coloraxis_showscale=False)
                    st.plotly_chart(fig_p, use_container_width=True)

                # ── 返礼品カテゴリ別
                if "category" in db_results:
                    st.markdown("##### 🎁 返礼品カテゴリ別実績（内部DB）")
                    df_c = db_results["category"]
                    ctg_col = "解析用カテゴリ" if "解析用カテゴリ" in df_c.columns else "カテゴリ"
                    amt_col = "寄附金額合計" if "寄附金額合計" in df_c.columns else "金額合計"
                    if ctg_col in df_c.columns and amt_col in df_c.columns:
                        fig_c = px.bar(
                            df_c.sort_values(amt_col, ascending=True).head(15),
                            x=amt_col, y=ctg_col, orientation="h",
                            color=amt_col, color_continuous_scale="Greens",
                            text=amt_col,
                        )
                        fig_c.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                        fig_c.update_layout(height=380, margin=dict(t=10, b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig_c, use_container_width=True)

                # ── 月別トレンド（公開データの寄附額推移と並列）
                if "monthly" in db_results:
                    st.markdown("##### 📅 月別受付トレンド（内部DB）")
                    df_mo = db_results["monthly"]
                    if "年月" in df_mo.columns and "件数" in df_mo.columns:
                        fig_mo = go.Figure()
                        fig_mo.add_trace(go.Bar(
                            x=df_mo["年月"], y=df_mo["件数"],
                            name="受付件数", marker_color="#3498db", opacity=0.7,
                        ))
                        if "金額合計" in df_mo.columns:
                            fig_mo.add_trace(go.Scatter(
                                x=df_mo["年月"], y=df_mo["金額合計"],
                                name="金額合計（円）", yaxis="y2",
                                line=dict(color="#e74c3c", width=2), mode="lines+markers",
                            ))
                            fig_mo.update_layout(
                                yaxis2=dict(overlaying="y", side="right", title="金額合計（円）"),
                            )
                        # キャンペーン日注記
                        fig_mo.add_annotation(
                            x=df_mo["年月"].iloc[-1], y=0,
                            text="5・10・15・20・25・30日は楽天キャンペーン多",
                            showarrow=False, font_size=9, yref="paper", yanchor="bottom",
                        )
                        fig_mo.update_layout(height=320, margin=dict(t=10, b=30),
                                             xaxis_tickangle=-45, barmode="overlay")
                        st.plotly_chart(fig_mo, use_container_width=True)

                # ── 定期便比率
                if "subscription" in db_results:
                    st.markdown("##### 🔁 定期便比率（内部DB）")
                    df_s = db_results["subscription"]
                    amt_col = "金額合計" if "金額合計" in df_s.columns else df_s.select_dtypes("number").columns[0]
                    fig_s = px.pie(df_s, names="種別", values=amt_col, hole=0.45,
                                   color_discrete_sequence=["#2ecc71", "#bdc3c7"])
                    fig_s.update_layout(height=280, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_s, use_container_width=True)

                # ── 年度別推移 × 公開データ照合
                if "yearly" in db_results:
                    st.markdown("##### 📈 年度別推移 — 内部DB vs 公開データ（DB捕捉率）")
                    df_yr_db = db_results["yearly"].copy()
                    if "年度" in df_yr_db.columns and "寄附金額合計" in df_yr_db.columns:
                        df_yr_db["DB金額（億円）"] = df_yr_db["寄附金額合計"] / 1e8
                        fig_yr = go.Figure()
                        # 公開データ
                        fig_yr.add_trace(go.Bar(
                            x=[f"{int(y)}年度" for y in df_muni_ts["年度"]],
                            y=df_muni_ts["受入額_億円"],
                            name="総務省公開値（億円）", marker_color="#95a5a6", opacity=0.6,
                        ))
                        # 内部DB
                        fig_yr.add_trace(go.Bar(
                            x=[f"{int(y)}年度" for y in df_yr_db["年度"]],
                            y=df_yr_db["DB金額（億円）"],
                            name="内部DB実績（億円）", marker_color="#2ecc71", opacity=0.9,
                        ))
                        fig_yr.update_layout(
                            barmode="overlay", height=300, margin=dict(t=10, b=10),
                            legend=dict(orientation="h", y=1.1),
                        )
                        st.plotly_chart(fig_yr, use_container_width=True)
                        # 捕捉率計算
                        common_yrs = set(df_yr_db["年度"]) & set(df_muni_ts["年度"])
                        if common_yrs:
                            latest_yr_common = max(common_yrs)
                            db_oku = df_yr_db[df_yr_db["年度"] == latest_yr_common]["DB金額（億円）"].values[0]
                            pub_oku = df_muni_ts[df_muni_ts["年度"] == latest_yr_common]["受入額_億円"].values[0]
                            coverage = db_oku / pub_oku * 100 if pub_oku > 0 else 0
                            st.info(
                                f"📊 {int(latest_yr_common)}年度の当自治体DBカバー率: "
                                f"**{coverage:.1f}%**"
                                f"（DB {db_oku:.1f}億円 ÷ 総務省 {pub_oku:.1f}億円）"
                                f" ／ 全国平均は約48%"
                            )

                # ── 寄附者属性
                if "demographics" in db_results:
                    st.markdown("##### 👥 寄附者属性（内部DB）")
                    df_dem = db_results["demographics"]
                    if "寄附者都道府県" in df_dem.columns and "金額合計" in df_dem.columns:
                        df_pref_dem = (df_dem.groupby("寄附者都道府県")["金額合計"]
                                       .sum().reset_index().sort_values("金額合計", ascending=False).head(15))
                        fig_dem = px.bar(df_pref_dem, x="寄附者都道府県", y="金額合計",
                                         color="金額合計", color_continuous_scale="Blues",
                                         labels={"金額合計": "金額合計（円）"})
                        fig_dem.update_layout(height=300, margin=dict(t=10, b=10),
                                              xaxis_tickangle=-45, coloraxis_showscale=False)
                        st.plotly_chart(fig_dem, use_container_width=True)

                # ── 統合レポート出力
                st.divider()
                st.markdown("##### 📋 統合レポートを出力（公開データ＋内部DB）")
                integrated_md = generate_integrated_md(
                    sel_pref, sel_muni, muni_code_val,
                    md_metrics, db_results,
                )
                col_int1, col_int2 = st.columns([1, 3])
                with col_int1:
                    st.download_button(
                        label="📥 統合MDをダウンロード",
                        data=integrated_md,
                        file_name=f"integrated_{sel_pref}_{sel_muni}.md",
                        mime="text/markdown",
                    )
                with col_int2:
                    if st.toggle("統合レポートをプレビュー", key="int_preview"):
                        st.markdown(integrated_md)
            else:
                st.info(
                    "💡 MDレポートのSQL（クエリ3-1〜3-6）を社内DBで実行し、"
                    "結果CSVをここにアップロードすると統合分析が始まります。"
                )

            with st.expander("年度別データ（全年度）"):
                st.dataframe(df_muni_ts[["年度ラベル", "受入額_億円", "受入件数", "順位"]]
                             .rename(columns={"年度ラベル": "年度"})
                             .sort_values("年度", ascending=False),
                             use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 4: 自治体を比較する
# ═══════════════════════════════════════════════════════════════
with tab4:
    if df_ts.empty:
        st.info("時系列データが見つかりません。")
    else:
        st.subheader("最大4自治体を並べて比較する")
        df_ranked4 = calc_ranking(df_ts)
        all_munis_sorted = (df_ranked4[df_ranked4["年度"] == df_ranked4["年度"].max()]
                            .sort_values("順位")["市区町村"].tolist())
        defaults = [m for m in ["白糠町", "都城市", "泉佐野市", "別海町"] if m in all_munis_sorted]
        sel_compare = st.multiselect("自治体を選択（最大4つ）", all_munis_sorted,
                                     default=defaults[:4], max_selections=4)

        if not sel_compare:
            st.info("自治体を選択してください。")
        else:
            df_comp = df_ranked4[df_ranked4["市区町村"].isin(sel_compare)].copy()
            df_comp["年度ラベル"] = df_comp["年度"].astype(str) + "年度"

            st.markdown("#### 📈 寄附額の推移")
            fig_line = px.line(df_comp, x="年度ラベル", y="受入額_億円", color="市区町村",
                               markers=True, color_discrete_sequence=px.colors.qualitative.Set1,
                               labels={"年度ラベル": "年度", "受入額_億円": "受入額（億円）"})
            fig_line.update_layout(height=340, margin=dict(t=10, b=10))
            st.plotly_chart(fig_line, use_container_width=True)

            st.markdown("#### 🏅 全国順位の推移")
            fig_rk = px.line(df_comp, x="年度ラベル", y="順位", color="市区町村",
                             markers=True, color_discrete_sequence=px.colors.qualitative.Set1,
                             labels={"年度ラベル": "年度"})
            fig_rk.update_yaxes(autorange="reversed")
            fig_rk.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_rk, use_container_width=True)

            if not df_detail.empty:
                st.markdown("#### 💰 経費率比較（2024年度）")
                df_cc = df_detail[df_detail["市区町村"].isin(sel_compare)].copy()
                if not df_cc.empty:
                    cost_items = {"返礼品調達費_円": "返礼品調達費", "送付費_円": "送付費",
                                  "広報費_円": "広報費", "決済費_円": "決済費",
                                  "事務費_円": "事務費", "その他費_円": "その他"}
                    rows = []
                    for _, r in df_cc.iterrows():
                        total = r["受入額_億円"] * 1e8
                        for col, label in cost_items.items():
                            rows.append({"市区町村": r["市区町村"], "費目": label,
                                         "比率（%）": round((r.get(col) or 0) / total * 100, 1) if total > 0 else 0})
                    df_cm = pd.DataFrame(rows)
                    fig_c = px.bar(df_cm, x="市区町村", y="比率（%）", color="費目", barmode="stack",
                                   color_discrete_map={"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                                                       "事務費": "#3498db", "決済費": "#9b59b6",
                                                       "広報費": "#95a5a6", "その他": "#bdc3c7"})
                    fig_c.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="5割ルール上限")
                    fig_c.update_layout(height=340, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_c, use_container_width=True)

            st.markdown("#### 2024年度 サマリー")
            df_sum = df_comp[df_comp["年度"] == df_comp["年度"].max()][["市区町村", "受入額_億円", "受入件数", "順位"]].copy()
            if not df_detail.empty:
                df_sum = df_sum.merge(df_detail[["市区町村", "経費率合計", "ポータル費_億円"]], on="市区町村", how="left")
                df_sum["経費率"] = (df_sum["経費率合計"] * 100).round(1).astype(str) + "%"
                df_sum = df_sum.drop(columns=["経費率合計"])
            st.dataframe(df_sum, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 5: 地域の動きを見る
# ═══════════════════════════════════════════════════════════════
with tab5:
    if df_ts.empty:
        st.info("時系列データが見つかりません。")
    else:
        st.subheader("都道府県の勢力図と県内の突出自治体")
        df_pref_ts = (df_ts.groupby(["都道府県", "年度"])["受入額_億円"]
                      .sum().reset_index().sort_values(["都道府県", "年度"]))
        latest_yr5 = int(df_pref_ts["年度"].max())
        top_prefs5 = (df_pref_ts[df_pref_ts["年度"] == latest_yr5]
                      .sort_values("受入額_億円", ascending=False).head(15)["都道府県"].tolist())

        st.markdown("#### 都道府県別 受入額の推移")
        sel_prefs5 = st.multiselect("都道府県を選択", sorted(df_pref_ts["都道府県"].unique()),
                                    default=top_prefs5, key="pref_map_sel")
        df_pref_plot = df_pref_ts[df_pref_ts["都道府県"].isin(sel_prefs5)].copy()
        df_pref_plot["年度ラベル"] = df_pref_plot["年度"].astype(str) + "年度"
        fig_p = px.line(df_pref_plot, x="年度ラベル", y="受入額_億円", color="都道府県",
                        markers=True, labels={"年度ラベル": "年度", "受入額_億円": "受入額（億円）"})
        fig_p.update_layout(height=400, margin=dict(t=10, b=10))
        st.plotly_chart(fig_p, use_container_width=True)

        st.divider()
        st.markdown("#### 県内の突出自治体を探す")
        years_avail5 = sorted(df_ts["年度"].unique())
        sel_pref_d5 = st.selectbox("都道府県", sorted(df_ts["都道府県"].unique()),
                                   index=sorted(df_ts["都道府県"].unique()).index("北海道"),
                                   key="pref_drill")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dc5 = st.selectbox("比較年度（新）", years_avail5[::-1], index=0, key="drill_c")
        with col_d2:
            dp5 = st.selectbox("比較年度（旧）", [y for y in years_avail5[::-1] if y < dc5], index=0, key="drill_p")

        df_drill5 = df_ts[df_ts["都道府県"] == sel_pref_d5].copy()
        pc5 = df_drill5[df_drill5["年度"] == dc5]["受入額_億円"].sum()
        pp5 = df_drill5[df_drill5["年度"] == dp5]["受入額_億円"].sum()
        pref_growth5 = (pc5 - pp5) / pp5 * 100 if pp5 > 0 else 0
        st.metric(f"{sel_pref_d5} 全体成長率（{dp5}→{dc5}年度）", f"{pref_growth5:+.1f}%")

        dm_c5 = df_drill5[df_drill5["年度"] == dc5][["市区町村", "受入額_億円"]].rename(columns={"受入額_億円": "new"})
        dm_p5 = df_drill5[df_drill5["年度"] == dp5][["市区町村", "受入額_億円"]].rename(columns={"受入額_億円": "old"})
        dm5 = dm_c5.merge(dm_p5, on="市区町村")
        dm5["成長率（%）"] = ((dm5["new"] - dm5["old"]) / dm5["old"] * 100).round(1)
        dm5["vs県平均"] = (dm5["成長率（%）"] - pref_growth5).round(1)
        dm5 = dm5.sort_values("成長率（%）", ascending=False)

        fig_d5 = px.bar(dm5, x="市区町村", y="成長率（%）", color="vs県平均",
                        color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                        text="成長率（%）",
                        labels={"成長率（%）": f"成長率（%）/ {dp5}→{dc5}年度"})
        fig_d5.add_hline(y=pref_growth5, line_dash="dash", line_color="navy",
                         annotation_text=f"県平均 {pref_growth5:+.1f}%")
        fig_d5.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_d5.update_layout(height=max(380, len(dm5) * 18), margin=dict(t=20, b=10),
                             xaxis_tickangle=-45, coloraxis_showscale=False)
        st.plotly_chart(fig_d5, use_container_width=True)

        outliers5 = dm5[dm5["vs県平均"] > 20].sort_values("vs県平均", ascending=False)
        if not outliers5.empty:
            st.success(f"🔍 県平均を20%以上上回る自治体: {', '.join(outliers5['市区町村'].tolist())}")

        with st.expander("全自治体データを見る"):
            st.dataframe(dm5.rename(columns={"new": f"{dc5}年度 受入額（億円）", "old": f"{dp5}年度 受入額（億円）"}),
                         use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 6: 経費・効率を分析する
# ═══════════════════════════════════════════════════════════════
with tab6:
    if df_detail.empty:
        st.info("費目別データが見つかりません。")
    else:
        analysis_tab = st.radio("分析メニュー",
                                ["都道府県ヒートマップ", "経費率分布（箱ひげ図）", "急成長自治体の経費解剖", "経費・収支サマリー"],
                                horizontal=True)

        # ── 都道府県ヒートマップ ────────────────────────────
        if analysis_tab == "都道府県ヒートマップ":
            st.markdown("### 🗺️ 都道府県 × 年度 受入額ヒートマップ")
            st.caption("47都道府県の受入額合計を年度×都道府県で俯瞰します。")

            if not df_ts.empty:
                df_heat = (df_ts.groupby(["都道府県", "年度"])["受入額_億円"].sum().reset_index())
                df_pivot = df_heat.pivot(index="都道府県", columns="年度", values="受入額_億円").fillna(0)
                df_pivot.columns = [f"{int(c)}年度" for c in df_pivot.columns]
                df_pivot = df_pivot.loc[df_pivot.sum(axis=1).sort_values(ascending=False).index]

                fig_heat = px.imshow(df_pivot, color_continuous_scale="Greens",
                                     labels={"color": "受入額（億円）", "x": "年度", "y": "都道府県"},
                                     aspect="auto", text_auto=".0f")
                fig_heat.update_layout(height=900, margin=dict(t=20, b=20),
                                       coloraxis_colorbar=dict(title="受入額（億円）"))
                st.plotly_chart(fig_heat, use_container_width=True)
                st.caption("数値は各都道府県内全自治体の合計（億円）。受入額大ほど濃い緑。")

        # ── 経費率分布（箱ひげ図） ───────────────────────────
        elif analysis_tab == "経費率分布（箱ひげ図）":
            st.markdown("### 📦 都道府県別 経費率の分布（2019〜2024年度）")
            st.caption("都道府県ごとに経費率のばらつきを確認します。外れ値として表示される点が特徴的な自治体です。")

            if not df_detail_multi.empty:
                df_box = df_detail_multi.copy()
                df_box["経費率（%）"] = df_box["経費率合計"] * 100
                df_box["年度ラベル"] = df_box["年度"].astype(str) + "年度"

                # 都道府県を直近の受入額合計順にソート
                pref_order = (df_detail.groupby("都道府県")["受入額_億円"].sum()
                              .sort_values(ascending=False).index.tolist())

                col_b1, col_b2 = st.columns([2, 1])
                with col_b1:
                    sel_years_box = st.multiselect(
                        "年度を選択",
                        sorted(df_box["年度ラベル"].unique()),
                        default=[f"{y}年度" for y in [2022, 2023, 2024]],
                        key="box_years"
                    )
                with col_b2:
                    show_points = st.checkbox("外れ値を表示", value=True)

                df_box_filt = df_box[df_box["年度ラベル"].isin(sel_years_box)]
                fig_box = px.box(df_box_filt, x="都道府県", y="経費率（%）",
                                 color="年度ラベル", points="outliers" if show_points else False,
                                 category_orders={"都道府県": pref_order},
                                 labels={"年度ラベル": "年度"},
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                fig_box.add_hline(y=50, line_dash="dash", line_color="red",
                                  annotation_text="5割ルール上限")
                fig_box.update_layout(height=500, margin=dict(t=20, b=20),
                                      xaxis_tickangle=-45, boxmode="group")
                st.plotly_chart(fig_box, use_container_width=True)
                st.caption("箱の中央線＝中央値。外れ値の点にカーソルを当てると自治体名が表示されます。")

        # ── 急成長自治体の経費解剖 ───────────────────────────
        elif analysis_tab == "急成長自治体の経費解剖":
            st.markdown("### 🔬 急成長自治体の経費構造解剖")
            st.caption("前年度比 +50% 以上を「急成長」と定義。経費配分のパターンを分析します。")

            # 全国費目別経費率の年度推移
            if not df_detail_multi.empty:
                st.markdown("#### 費目別経費率の年度推移（全国合計ベース）")
                cost_cols6 = {"返礼品調達費_円": "返礼品調達費", "送付費_円": "送付費",
                              "広報費_円": "広報費", "決済費_円": "決済費",
                              "事務費_円": "事務費", "その他費_円": "その他"}
                rows6 = []
                for yr6, grp6 in df_detail_multi.groupby("年度"):
                    total_yen6 = (grp6["受入額_億円"] * 1e8).sum()
                    if total_yen6 <= 0:
                        continue
                    for col6, lbl6 in cost_cols6.items():
                        rows6.append({"年度": f"{int(yr6)}年度", "費目": lbl6,
                                      "比率（%）": round(grp6[col6].fillna(0).sum() / total_yen6 * 100, 2)})
                df_trend6 = pd.DataFrame(rows6)
                color_map6 = {"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                              "事務費": "#3498db", "決済費": "#9b59b6",
                              "広報費": "#95a5a6", "その他": "#bdc3c7"}
                fig_t6 = px.bar(df_trend6, x="年度", y="比率（%）", color="費目",
                                barmode="stack", color_discrete_map=color_map6,
                                labels={"比率（%）": "経費率（全国合計比・%）"})
                fig_t6.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="5割ルール上限")
                fig_t6.update_layout(height=320, margin=dict(t=20, b=10))
                st.plotly_chart(fig_t6, use_container_width=True)
                st.divider()

            if not df_ts.empty:
                df_ranked6 = calc_ranking(df_ts)
                rc6 = df_ranked6[df_ranked6["年度"] == 2024][["市区町村", "都道府県", "受入額_億円"]].rename(
                    columns={"受入額_億円": "受入額_2024年度"})
                rp6 = df_ranked6[df_ranked6["年度"] == 2023][["市区町村", "都道府県", "受入額_億円"]].rename(
                    columns={"受入額_億円": "受入額_2023年度"})
                df_gr6 = rc6.merge(rp6, on=["市区町村", "都道府県"])
                df_gr6 = df_gr6[df_gr6["受入額_2023年度"] >= 1]
                df_gr6["成長率（%）"] = ((df_gr6["受入額_2024年度"] - df_gr6["受入額_2023年度"]) / df_gr6["受入額_2023年度"] * 100).round(1)
                df_rapid6 = df_gr6[df_gr6["成長率（%）"] >= 50].sort_values("成長率（%）", ascending=False)
                df_rapid6 = df_rapid6.merge(
                    df_detail[["市区町村", "受入額_億円", "経費率合計", "返礼品調達費_円", "送付費_円", "広報費_円", "ポータル費_億円"]],
                    on="市区町村", how="inner")

                st.metric("急成長自治体数（前年度比 +50% 以上）", f"{len(df_rapid6)} 自治体")
                fig_gr6 = px.bar(df_rapid6.head(20), x="市区町村", y="成長率（%）",
                                 color="経費率合計", color_continuous_scale="RdYlGn_r",
                                 text="成長率（%）", hover_data={"都道府県": True})
                fig_gr6.add_hline(y=50, line_dash="dot", line_color="blue")
                fig_gr6.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
                fig_gr6.update_layout(height=380, margin=dict(t=10, b=10),
                                      xaxis_tickangle=-45, coloraxis_showscale=False)
                st.plotly_chart(fig_gr6, use_container_width=True)

                df_rapid6["広告費比率（%）"]  = (df_rapid6["広報費_円"] / (df_rapid6["受入額_億円"] * 1e8) * 100).round(1)
                df_rapid6["返礼品比率（%）"] = (df_rapid6["返礼品調達費_円"] / (df_rapid6["受入額_億円"] * 1e8) * 100).round(1)
                st.dataframe(df_rapid6[["市区町村", "都道府県", "成長率（%）", "受入額_2024年度", "経費率合計",
                                        "返礼品比率（%）", "広告費比率（%）", "ポータル費_億円"]].rename(
                    columns={"受入額_2024年度": "受入額（億円）", "経費率合計": "経費率", "ポータル費_億円": "ポータル費（億円）"}
                ).head(20), use_container_width=True, hide_index=True)

        # ── 経費・収支サマリー ───────────────────────────────
        else:
            st.markdown("### 💰 費目別 経費内訳（全国集計）")
            df_k = df_keihi.copy()
            df_k["年度"] = df_k["year"].astype(str) + "年度"
            cost_map = {"henreihin_oku": "返礼品調達費", "soryo_oku": "送料",
                        "jimu_oku": "事務費等", "kessai_oku": "決済費用", "koho_oku": "広報費"}
            df_mk = df_k[["年度"] + list(cost_map.keys())].melt(id_vars="年度", var_name="c", value_name="億円")
            df_mk["費目"] = df_mk["c"].map(cost_map)
            fig_k = px.bar(df_mk, x="年度", y="億円", color="費目", barmode="stack",
                           labels={"億円": "金額（億円）"},
                           color_discrete_map={"返礼品調達費": "#e74c3c", "送料": "#e67e22",
                                               "事務費等": "#3498db", "決済費用": "#9b59b6", "広報費": "#95a5a6"})
            fig_k.update_layout(height=360, margin=dict(t=10, b=10))
            st.plotly_chart(fig_k, use_container_width=True)

            lk = df_keihi.iloc[-1]
            ck1, ck2, ck3, ck4 = st.columns(4)
            ck1.metric("2024年度 経費率", f"{lk['keihi_rate_pct']}%")
            ck2.metric("返礼品調達費率", f"{lk['henreihin_rate_pct']}%")
            ck3.metric("ポータル手数料", fmt_oku(lk['portal_fee_oku']), f"{lk['portal_fee_rate_pct']}%")
            ck4.metric("自治体の手残り", fmt_oku(lk['jiyu_zaisgen_oku']))
            st.caption("注: ポータル手数料（13.0%）は全受入額比。仲介サイト経由額比では11.5%（別調査）")

            if not df_detail.empty:
                st.divider()
                st.markdown("#### 都道府県別 平均経費率（2024年度）")
                df_pref6 = (df_detail.groupby("都道府県")
                            .agg(受入額合計=("受入額_億円", "sum"), 経費合計=("経費合計_億円", "sum"))
                            .reset_index())
                df_pref6["経費率（%）"] = (df_pref6["経費合計"] / df_pref6["受入額合計"] * 100).round(1)
                fig_pref6 = px.bar(df_pref6.sort_values("経費率（%）", ascending=False),
                                   x="都道府県", y="経費率（%）", color="経費率（%）",
                                   color_continuous_scale="RdYlGn_r", text="経費率（%）")
                fig_pref6.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig_pref6.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50%上限")
                fig_pref6.update_layout(height=400, margin=dict(t=20, b=20),
                                        xaxis_tickangle=-45, coloraxis_showscale=False)
                st.plotly_chart(fig_pref6, use_container_width=True)

            st.divider()
            st.markdown("#### 🏙️ 都市部の住民税流出・収支損失")
            df_r6 = df_ryushutsu.copy()
            df_tok6 = df_r6[df_r6["jichitai"] == "東京都"].sort_values("year")
            if not df_tok6.empty:
                df_tok6["年度ラベル"] = df_tok6["year"].astype(str) + "年度"
                fig_t6b = px.line(df_tok6, x="年度ラベル", y="ryushutsu_oku", markers=True,
                                  title="東京都 住民税流出額の推移",
                                  labels={"年度ラベル": "年度", "ryushutsu_oku": "流出額（億円）"})
                fig_t6b.update_traces(line_color="#e74c3c", marker_size=10)
                fig_t6b.update_layout(height=250, margin=dict(t=40, b=10))
                st.plotly_chart(fig_t6b, use_container_width=True)
            df_lat6 = (df_r6[df_r6["jichitai"] != "東京都"].sort_values("year", ascending=False)
                       .drop_duplicates("jichitai").sort_values("ryushutsu_oku", ascending=False))
            fig_l6 = px.bar(df_lat6, x="jichitai", y="ryushutsu_oku", color="kofu_hokan",
                            labels={"jichitai": "自治体", "ryushutsu_oku": "損失額（億円）",
                                    "kofu_hokan": "交付税補填"},
                            color_discrete_map={"なし（不交付団体）": "#e74c3c",
                                                "あり（交付団体・75%補填）": "#f39c12"},
                            text="ryushutsu_oku")
            fig_l6.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
            fig_l6.update_layout(height=320, margin=dict(t=10, b=10))
            st.plotly_chart(fig_l6, use_container_width=True)
            st.info("🔴 不交付団体（東京23区・川崎市等）は補填ゼロ\n\n🟡 交付団体（横浜・名古屋・大阪等）は75%が地方交付税で補填")


# ═══════════════════════════════════════════════════════════════
# Tab 7: データを抽出する
# ═══════════════════════════════════════════════════════════════
with tab7:
    st.subheader("条件を指定して自治体リストを抽出する")
    st.caption("絞り込んだ結果をCSVでダウンロードして、社内ツールや追加分析に活用できます。")

    if df_detail_multi.empty and df_detail.empty:
        st.info("費目別データが見つかりません。")
    else:
        base_df = df_detail_multi.copy() if not df_detail_multi.empty else df_detail.copy()

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            years_avail7 = sorted(base_df["年度"].unique(), reverse=True)
            sel_years7 = st.multiselect("年度", [f"{y}年度" for y in years_avail7],
                                        default=[f"{years_avail7[0]}年度"], key="ext_year")
            sel_years_int = [int(y.replace("年度", "")) for y in sel_years7]

        with col_f2:
            all_prefs7 = sorted(base_df["都道府県"].unique())
            sel_prefs7 = st.multiselect("都道府県（空欄＝全国）", all_prefs7, key="ext_pref")

        with col_f3:
            kifu_range = st.slider("受入額（億円）",
                                   0.0, float(base_df["受入額_億円"].max()),
                                   (0.0, float(base_df["受入額_億円"].max())),
                                   step=1.0, key="ext_kifu")

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            keihi_range = st.slider("経費率（%）", 0, 100, (0, 100), key="ext_keihi")
        with col_f5:
            sort_col = st.selectbox("並び替え",
                                    ["受入額_億円（降順）", "受入額_億円（昇順）",
                                     "経費率合計（降順）", "経費率合計（昇順）"],
                                    key="ext_sort")

        df_ext = base_df[base_df["年度"].isin(sel_years_int)].copy()
        if sel_prefs7:
            df_ext = df_ext[df_ext["都道府県"].isin(sel_prefs7)]
        df_ext = df_ext[(df_ext["受入額_億円"] >= kifu_range[0]) & (df_ext["受入額_億円"] <= kifu_range[1])]
        df_ext["経費率（%）"] = (df_ext["経費率合計"] * 100).round(1)
        df_ext = df_ext[(df_ext["経費率（%）"] >= keihi_range[0]) & (df_ext["経費率（%）"] <= keihi_range[1])]

        sort_map = {
            "受入額_億円（降順）": ("受入額_億円", False),
            "受入額_億円（昇順）": ("受入額_億円", True),
            "経費率合計（降順）": ("経費率合計", False),
            "経費率合計（昇順）": ("経費率合計", True),
        }
        scol, sasc = sort_map[sort_col]
        df_ext = df_ext.sort_values(scol, ascending=sasc)

        st.metric("抽出件数", f"{len(df_ext):,} 件")

        display_cols = ["年度", "都道府県", "市区町村", "受入額_億円", "受入件数",
                        "経費率（%）", "返礼品調達費_円", "送付費_円", "広報費_円",
                        "決済費_円", "事務費_円", "ポータル費_億円"]
        display_cols = [c for c in display_cols if c in df_ext.columns]
        df_show = df_ext[display_cols].copy()
        df_show["年度"] = df_show["年度"].astype(int).astype(str) + "年度"
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        year_label = "_".join([str(y) for y in sorted(sel_years_int)])
        csv = df_show.to_csv(index=False, encoding="utf-8-sig")

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 CSVをダウンロード",
                data=csv,
                file_name=f"furusato_extract_{year_label}.csv",
                mime="text/csv",
            )
        with col_dl2:
            conditions_text = "\n".join([
                f"- 年度: {', '.join(sel_years7) if sel_years7 else '全年度'}",
                f"- 都道府県: {', '.join(sel_prefs7) if sel_prefs7 else '全国'}",
                f"- 受入額: {kifu_range[0]:.0f}〜{kifu_range[1]:.0f} 億円",
                f"- 経費率: {keihi_range[0]}〜{keihi_range[1]}%",
                f"- 並び替え: {sort_col}",
            ])
            md_list = generate_list_md(df_ext, conditions_text)
            st.download_button(
                label="📄 MDレポートをダウンロード",
                data=md_list,
                file_name=f"furusato_report_{year_label}.md",
                mime="text/markdown",
            )

        st.caption("CSVは表計算ソフトへ、MDレポートはClaude Codeへそのまま貼り付けて活用できます。")
