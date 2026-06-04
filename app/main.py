import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import subprocess, sys

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"

st.set_page_config(
    page_title="ふるさと納税ダッシュボード",
    page_icon="🏡",
    layout="wide",
)

st.title("🏡 ふるさと納税 分析ダッシュボード")
st.caption("出典: 総務省現況調査・日経新聞・東洋経済ほか ／ 知識ベース最終更新: 2026-06-03")


@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_detail():
    return load_csv("jichitai_detail.csv")


@st.cache_data
def load_timeseries():
    return load_csv("jichitai_timeseries.csv")


# ── サイドバー ────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 データ更新")
    st.caption("総務省からダウンロードしたExcelをアップロードすると自動でパースします")

    up_detail = st.file_uploader(
        "費目別明細 Excel（例: 001022818_2024detail.xlsx）",
        type=["xlsx"], key="detail"
    )
    up_ts = st.file_uploader(
        "時系列 Excel（例: 001022819_timeseries.xlsx）",
        type=["xlsx"], key="ts"
    )

    if up_detail or up_ts:
        if st.button("🔄 パース実行", type="primary"):
            with st.spinner("Excelを解析中..."):
                if up_detail:
                    save_path = RAW_DIR / "001022818_2024detail.xlsx"
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_bytes(up_detail.read())
                if up_ts:
                    save_path = RAW_DIR / "001022819_timeseries.xlsx"
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_bytes(up_ts.read())
                script = Path(__file__).parent.parent / "scripts" / "parse_soumu_excel.py"
                result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("パース完了！")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"エラー:\n{result.stderr}")

    st.divider()
    st.markdown("[📖 知識ベース（GitHub）](https://github.com/tgsoccer79-dot/my-project)")
    st.markdown("[📁 総務省 現況調査](https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/)")


# ── データ読み込み ────────────────────────────────────────────
df_market = load_csv("market_trends_annual.csv")
df_ranking = load_csv("kifu_ranking_by_year.csv")
df_keihi = load_csv("keihi_annual.csv")
df_ryushutsu = load_csv("toshi_ryushutsu.csv")
df_detail = load_detail()
df_ts = load_timeseries()

# ── タブ ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 市場トレンド",
    "🏆 自治体ランキング",
    "🔍 自治体詳細・比較",
    "💰 経費・収支",
    "🏙️ 都市流出",
])


# ═══════════════════════════════════════════════════════════════
# Tab 1: 市場トレンド
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.subheader("全国 寄附総額の推移（2008〜2024年度）")

    df_m = df_market.copy()
    df_m["year"] = df_m["year"].astype(str)

    col1, col2, col3 = st.columns(3)
    latest = df_m.iloc[-1]
    prev = df_m.iloc[-2]
    col1.metric(
        "2024年度 受入総額",
        f"{int(latest['kifu_total_oku']):,} 億円",
        f"+{int(latest['kifu_total_oku']) - int(prev['kifu_total_oku']):,} 億円（前年比）",
    )
    col2.metric("2024年度 受入件数", f"{int(latest['cases_man']):,} 万件")
    col3.metric("2024年度 経費率", f"{latest['keihi_rate_pct']}%", delta_color="inverse")

    fig = px.bar(
        df_m, x="year", y="kifu_total_oku",
        labels={"year": "年度", "kifu_total_oku": "受入総額（億円）"},
        color_discrete_sequence=["#2ecc71"], text="kifu_total_oku",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont_size=10)
    fig.update_layout(height=420, margin=dict(t=20, b=20), xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("出典: 総務省「ふるさと納税に関する現況調査結果」各年度版")

    with st.expander("📋 生データ"):
        st.dataframe(df_m, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Tab 2: 自治体ランキング
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.subheader("自治体別 寄附額ランキング")

    col_l, col_r = st.columns([1, 3])
    with col_l:
        if not df_detail.empty:
            years_available = [2024]
        else:
            years_available = sorted(df_ranking["year"].unique(), reverse=True)
        selected_year = st.selectbox("年度", years_available)
        top_n = st.slider("表示件数", 5, 50, 20)

    # 詳細データがあれば使う（全1788自治体）
    if not df_detail.empty and selected_year == 2024:
        df_yr = (
            df_detail[["都道府県", "市区町村", "受入額_億円", "経費率合計", "ポータル費_億円"]]
            .copy()
            .sort_values("受入額_億円", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        df_yr.index += 1
        df_yr["自治体"] = df_yr["都道府県"] + " " + df_yr["市区町村"]
        df_yr["経費率"] = (df_yr["経費率合計"] * 100).round(1).astype(str) + "%"

        with col_r:
            fig = px.bar(
                df_yr, x="受入額_億円", y="自治体", orientation="h",
                color="受入額_億円", color_continuous_scale="Greens",
                text="受入額_億円",
            )
            fig.update_traces(texttemplate="%{text:.1f} 億円", textposition="outside")
            fig.update_layout(
                height=max(400, top_n * 22),
                margin=dict(t=10, b=10),
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_yr[["自治体", "受入額_億円", "経費率", "ポータル費_億円"]].rename(
                columns={"受入額_億円": "受入額（億円）", "ポータル費_億円": "ポータル費（億円）"}
            ),
            use_container_width=True,
        )
    else:
        df_yr = df_ranking[df_ranking["year"] == selected_year].copy().sort_values("rank")
        df_yr["自治体"] = df_yr["prefecture"] + " " + df_yr["municipality"]
        with col_r:
            fig = px.bar(
                df_yr.head(top_n), x="kifu_oku", y="自治体", orientation="h",
                color="kifu_oku", color_continuous_scale="Greens", text="kifu_oku",
            )
            fig.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
            fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    if selected_year == 2024:
        st.info("⚠️ 1位の宝塚市（約257億円）は市立病院への大口個人寄附254億円を含む特殊事例。通常の返礼品目的では白糠町（約212億円）が実質1位。")


# ═══════════════════════════════════════════════════════════════
# Tab 3: 自治体詳細・比較
# ═══════════════════════════════════════════════════════════════
with tab3:
    if df_ts.empty or df_detail.empty:
        st.info("総務省Excelをサイドバーからアップロードしてパースするとこのタブが使えます。")
    else:
        st.subheader("自治体の寄附額推移を比較する")

        prefs = sorted(df_ts["都道府県"].unique())
        col1, col2 = st.columns([1, 2])

        with col1:
            sel_prefs = st.multiselect(
                "都道府県を選択（複数可）",
                prefs,
                default=["北海道", "宮崎県"],
            )
            if sel_prefs:
                munis_in_pref = sorted(
                    df_ts[df_ts["都道府県"].isin(sel_prefs)]["市区町村"].unique()
                )
                sel_munis = st.multiselect(
                    "自治体を選択（複数可）",
                    munis_in_pref,
                    default=[m for m in ["白糠町", "都城市", "別海町", "紋別市"] if m in munis_in_pref][:4],
                )
            else:
                sel_munis = []

        with col2:
            if sel_munis:
                df_plot = df_ts[df_ts["市区町村"].isin(sel_munis)].copy()
                fig = px.line(
                    df_plot, x="年度", y="受入額_億円", color="市区町村",
                    markers=True,
                    labels={"年度": "年度", "受入額_億円": "受入額（億円）"},
                )
                fig.update_layout(height=380, margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("自治体を選択してください")

        st.divider()
        st.subheader("自治体の経費構造を分析する（2024年度）")

        all_munis = sorted(df_detail["市区町村"].unique())
        sel_muni2 = st.selectbox("自治体を選択", all_munis, index=all_munis.index("白糠町") if "白糠町" in all_munis else 0)

        row = df_detail[df_detail["市区町村"] == sel_muni2]
        if not row.empty:
            row = row.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("受入額", f"{row['受入額_億円']:.1f} 億円")
            c2.metric("経費率", f"{row['経費率合計']*100:.1f}%")
            c3.metric("ポータル費", f"{row['ポータル費_億円']:.1f} 億円")
            c4.metric("ポータル費率", f"{row['ポータル費_億円']/row['受入額_億円']*100:.1f}%" if row['受入額_億円'] > 0 else "—")

            費目 = {
                "返礼品調達費": row.get("返礼品調達費_円", 0) or 0,
                "送付費": row.get("送付費_円", 0) or 0,
                "広報費": row.get("広報費_円", 0) or 0,
                "決済費": row.get("決済費_円", 0) or 0,
                "事務費": row.get("事務費_円", 0) or 0,
                "その他": row.get("その他費_円", 0) or 0,
            }
            df_pie = pd.DataFrame({"費目": 費目.keys(), "金額": 費目.values()})
            df_pie = df_pie[df_pie["金額"] > 0]

            fig_pie = px.pie(
                df_pie, names="費目", values="金額",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_pie.update_layout(height=320, margin=dict(t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Tab 4: 経費・収支
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.subheader("費目別 経費内訳（全国集計）")

    df_k = df_keihi.copy()
    df_k["year"] = df_k["year"].astype(str)

    cost_cols = {
        "henreihin_oku": "返礼品調達費",
        "soryo_oku": "送料",
        "jimu_oku": "事務費等",
        "kessai_oku": "決済費用",
        "koho_oku": "広報費",
    }
    df_melt = df_k[["year"] + list(cost_cols.keys())].melt(
        id_vars="year", var_name="費目コード", value_name="金額（億円）"
    )
    df_melt["費目"] = df_melt["費目コード"].map(cost_cols)

    fig = px.bar(
        df_melt, x="year", y="金額（億円）", color="費目", barmode="stack",
        color_discrete_map={
            "返礼品調達費": "#e74c3c", "送料": "#e67e22",
            "事務費等": "#3498db", "決済費用": "#9b59b6", "広報費": "#95a5a6",
        },
    )
    fig.update_layout(height=380, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    latest_k = df_k.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("2024年度 経費率", f"{latest_k['keihi_rate_pct']}%")
    c2.metric("返礼品調達費率", f"{latest_k['henreihin_rate_pct']}%")
    c3.metric("ポータル手数料", f"{int(latest_k['portal_fee_oku']):,} 億円", f"{latest_k['portal_fee_rate_pct']}%")
    c4.metric("自治体の手残り", f"{int(latest_k['jiyu_zaisgen_oku']):,} 億円")

    st.caption("注: ポータル手数料（13.0%）は全受入額比。仲介サイト経由額比では11.5%（別調査・2026年5月）")

    # 都道府県別経費率（2024詳細データがあれば）
    if not df_detail.empty:
        st.divider()
        st.subheader("都道府県別 平均経費率（2024年度）")
        df_pref = (
            df_detail.groupby("都道府県")
            .agg(受入額合計=("受入額_億円", "sum"), 経費合計=("経費合計_億円", "sum"))
            .reset_index()
        )
        df_pref["経費率"] = (df_pref["経費合計"] / df_pref["受入額合計"] * 100).round(1)
        df_pref = df_pref.sort_values("経費率", ascending=False)

        fig2 = px.bar(
            df_pref, x="都道府県", y="経費率",
            color="経費率", color_continuous_scale="RdYlGn_r",
            labels={"経費率": "経費率（%）"},
            text="経費率",
        )
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50%上限ライン")
        fig2.update_layout(height=420, margin=dict(t=20, b=20), xaxis_tickangle=-45, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("50%を超える自治体は総務省の指定基準（5割ルール）違反の可能性あり")


# ═══════════════════════════════════════════════════════════════
# Tab 5: 都市流出
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.subheader("都市部の住民税流出・収支損失")

    df_r = df_ryushutsu.copy()

    df_tokyo = df_r[df_r["jichitai"] == "東京都"].sort_values("year")
    if not df_tokyo.empty:
        fig = px.line(
            df_tokyo, x="year", y="ryushutsu_oku", markers=True,
            labels={"year": "年度", "ryushutsu_oku": "流出額（億円）"},
            title="東京都 住民税流出額の推移",
        )
        fig.update_traces(line_color="#e74c3c", marker_size=10)
        fig.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("#### 主要自治体の収支損失（最新年度）")

    df_latest = (
        df_r[df_r["jichitai"] != "東京都"]
        .sort_values("year", ascending=False)
        .drop_duplicates("jichitai")
        .sort_values("ryushutsu_oku", ascending=False)
    )

    fig2 = px.bar(
        df_latest, x="jichitai", y="ryushutsu_oku",
        color="kofu_hokan",
        labels={"jichitai": "自治体", "ryushutsu_oku": "損失額（億円）", "kofu_hokan": "地方交付税補填"},
        color_discrete_map={
            "なし（不交付団体）": "#e74c3c",
            "あり（交付団体・75%補填）": "#f39c12",
        },
        text="ryushutsu_oku",
    )
    fig2.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
    fig2.update_layout(height=360, margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    st.info("🔴 不交付団体（東京23区・川崎市等）は補填ゼロ → 流出額の全額が実質減収\n\n🟡 交付団体（横浜・名古屋・大阪等）は75%が地方交付税で補填")
