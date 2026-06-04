import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

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
    return pd.read_csv(path)


def load_uploaded_or_default(uploaded, filename):
    if uploaded:
        return pd.read_csv(uploaded)
    return load_csv(filename)


# ── サイドバー: データ更新 ─────────────────────────────────────
with st.sidebar:
    st.header("📂 データ更新")
    st.caption("最新CSVをアップロードすると即座に反映されます")

    up_market = st.file_uploader("市場トレンド CSV", type="csv", key="market")
    up_ranking = st.file_uploader("自治体ランキング CSV", type="csv", key="ranking")
    up_keihi = st.file_uploader("経費内訳 CSV", type="csv", key="keihi")
    up_ryushutsu = st.file_uploader("都市流出 CSV", type="csv", key="ryushutsu")

    st.divider()
    st.markdown("[📖 知識ベース（GitHub）](https://github.com/tgsoccer79-dot/my-project)")


# ── データ読み込み ─────────────────────────────────────────────
df_market = load_uploaded_or_default(up_market, "market_trends_annual.csv")
df_ranking = load_uploaded_or_default(up_ranking, "kifu_ranking_by_year.csv")
df_keihi = load_uploaded_or_default(up_keihi, "keihi_annual.csv")
df_ryushutsu = load_uploaded_or_default(up_ryushutsu, "toshi_ryushutsu.csv")


# ── タブ構成 ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 市場トレンド",
    "🏆 自治体ランキング",
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
    col3.metric(
        "2024年度 経費率",
        f"{latest['keihi_rate_pct']}%",
        delta_color="inverse",
    )

    fig_trend = px.bar(
        df_m,
        x="year",
        y="kifu_total_oku",
        labels={"year": "年度", "kifu_total_oku": "受入総額（億円）"},
        color_discrete_sequence=["#2ecc71"],
        text="kifu_total_oku",
    )
    fig_trend.update_traces(texttemplate="%{text:,}", textposition="outside", textfont_size=10)
    fig_trend.update_layout(
        height=420,
        margin=dict(t=20, b=20),
        xaxis_tickangle=-45,
        yaxis_title="受入総額（億円）",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.caption("出典: 総務省「ふるさと納税に関する現況調査結果」各年度版")

    with st.expander("📋 生データを見る"):
        st.dataframe(df_m, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Tab 2: 自治体ランキング
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.subheader("自治体別 寄附額ランキング")

    years_available = sorted(df_ranking["year"].unique(), reverse=True)
    selected_year = st.selectbox("年度を選択", years_available, index=0)

    df_yr = df_ranking[df_ranking["year"] == selected_year].copy()
    df_yr = df_yr.sort_values("rank")
    df_yr["自治体"] = df_yr["prefecture"] + " " + df_yr["municipality"]

    fig_rank = px.bar(
        df_yr,
        x="kifu_oku",
        y="自治体",
        orientation="h",
        color="kifu_oku",
        color_continuous_scale="Greens",
        labels={"kifu_oku": "寄附額（億円）", "自治体": ""},
        text="kifu_oku",
        hover_data=["main_henreihin", "notes"],
    )
    fig_rank.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
    fig_rank.update_layout(
        height=420,
        margin=dict(t=20, b=20),
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    st.dataframe(
        df_yr[["rank", "自治体", "kifu_oku", "main_henreihin", "notes"]].rename(
            columns={"rank": "順位", "kifu_oku": "寄附額（億円）", "main_henreihin": "主力返礼品", "notes": "備考"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    if selected_year == 2024:
        st.info("⚠️ 1位の宝塚市（約257億円）は市立病院への大口個人寄附254億円を含む特殊事例。通常の返礼品目的では白糠町（約212億円）が実質1位。")


# ═══════════════════════════════════════════════════════════════
# Tab 3: 経費・収支
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.subheader("費目別 経費内訳（全国集計）")

    df_k = df_keihi.copy()
    df_k["year"] = df_k["year"].astype(str)

    # 費目別積み上げ棒グラフ
    cost_cols = {
        "henreihin_oku": "返礼品調達費",
        "soryo_oku": "送料",
        "jimu_oku": "事務費等（ポータル手数料含む）",
        "kessai_oku": "決済費用",
        "koho_oku": "広報費",
    }

    df_melt = df_k[["year"] + list(cost_cols.keys())].melt(
        id_vars="year", var_name="費目コード", value_name="金額（億円）"
    )
    df_melt["費目"] = df_melt["費目コード"].map(cost_cols)

    fig_cost = px.bar(
        df_melt,
        x="year",
        y="金額（億円）",
        color="費目",
        barmode="stack",
        labels={"year": "年度"},
        color_discrete_map={
            "返礼品調達費": "#e74c3c",
            "送料": "#e67e22",
            "事務費等（ポータル手数料含む）": "#3498db",
            "決済費用": "#9b59b6",
            "広報費": "#95a5a6",
        },
    )
    fig_cost.update_layout(height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig_cost, use_container_width=True)

    # KPI行
    latest_k = df_k.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("2024年度 経費率", f"{latest_k['keihi_rate_pct']}%")
    col2.metric("返礼品調達費率", f"{latest_k['henreihin_rate_pct']}%")
    col3.metric("ポータル手数料", f"{int(latest_k['portal_fee_oku']):,} 億円", f"{latest_k['portal_fee_rate_pct']}%")
    col4.metric("自治体の手残り", f"{int(latest_k['jiyu_zaisgen_oku']):,} 億円")

    st.caption("注: ポータル手数料（13.0%）は全受入額比。仲介サイト経由額比では11.5%（別調査・2026年5月）")
    st.caption("出典: 総務省 令和7年度実施 現況調査（2024年度）")

    with st.expander("📋 生データを見る"):
        st.dataframe(df_k, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Tab 4: 都市流出
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.subheader("都市部の住民税流出・収支損失")

    df_r = df_ryushutsu.copy()

    # 東京都全体の推移
    df_tokyo = df_r[df_r["jichitai"] == "東京都"].sort_values("year")
    if not df_tokyo.empty:
        fig_tokyo = px.line(
            df_tokyo,
            x="year",
            y="ryushutsu_oku",
            markers=True,
            labels={"year": "年度", "ryushutsu_oku": "流出額（億円）"},
            title="東京都 住民税流出額の推移",
        )
        fig_tokyo.update_traces(line_color="#e74c3c", marker_size=10)
        fig_tokyo.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig_tokyo, use_container_width=True)

    st.divider()
    st.markdown("#### 主要自治体の収支損失（最新年度）")

    # 自治体ごとに最新年度のみ抽出
    df_latest = (
        df_r[df_r["jichitai"] != "東京都"]
        .sort_values("year", ascending=False)
        .drop_duplicates("jichitai")
        .sort_values("ryushutsu_oku", ascending=False)
    )

    fig_loss = px.bar(
        df_latest,
        x="jichitai",
        y="ryushutsu_oku",
        color="kofu_hokan",
        labels={
            "jichitai": "自治体",
            "ryushutsu_oku": "流出・損失額（億円）",
            "kofu_hokan": "地方交付税補填",
        },
        color_discrete_map={
            "なし（不交付団体）": "#e74c3c",
            "あり（交付団体・75%補填）": "#f39c12",
        },
        text="ryushutsu_oku",
    )
    fig_loss.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
    fig_loss.update_layout(height=360, margin=dict(t=20, b=20))
    st.plotly_chart(fig_loss, use_container_width=True)

    st.info("🔴 不交付団体（東京23区・川崎市等）は補填ゼロ → 流出額の全額が実質減収\n\n🟡 交付団体（横浜・名古屋・大阪等）は75%が地方交付税で補填")

    with st.expander("📋 生データを見る"):
        st.dataframe(df_r, use_container_width=True)
