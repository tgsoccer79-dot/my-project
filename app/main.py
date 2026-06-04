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


# ── ユーティリティ ─────────────────────────────────────────────
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


@st.cache_data
def calc_clusters(df_detail: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
    """2024年度の費目データをクラスタリング"""
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    feats = ["受入額_億円", "経費率合計", "ポータル費_億円"]
    df = df_detail[feats + ["都道府県", "市区町村"]].dropna().copy()
    X = StandardScaler().fit_transform(df[feats])
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["クラスタ"] = km.fit_predict(X)

    # クラスタに直感的な名前をつける
    summary = df.groupby("クラスタ")[feats].mean()
    labels = {}
    for c, row in summary.iterrows():
        growth = row["受入額_億円"]
        cost = row["経費率合計"]
        if growth > summary["受入額_億円"].median() and cost < summary["経費率合計"].median():
            labels[c] = "高収入・低コスト型"
        elif growth > summary["受入額_億円"].median() and cost >= summary["経費率合計"].median():
            labels[c] = "高収入・高コスト型"
        elif growth <= summary["受入額_億円"].median() and cost < summary["経費率合計"].median():
            labels[c] = "中規模・低コスト型"
        else:
            labels[c] = "小規模・標準型"
    # 重複ラベルを番号で区別
    seen = {}
    for c in labels:
        base = labels[c]
        seen[base] = seen.get(base, 0) + 1
        if seen[base] > 1:
            labels[c] = f"{base} {seen[base]}"
    df["クラスタ名"] = df["クラスタ"].map(labels)
    return df


def signal(value, low, high, inverse=False):
    """信号機ラベルを返す"""
    if inverse:
        if value <= low:
            return "🟢"
        elif value <= high:
            return "🟡"
        else:
            return "🔴"
    else:
        if value >= high:
            return "🟢"
        elif value >= low:
            return "🟡"
        else:
            return "🔴"


# ── データ読み込み ────────────────────────────────────────────
df_market  = load_csv("market_trends_annual.csv")
df_ranking = load_csv("kifu_ranking_by_year.csv")
df_keihi   = load_csv("keihi_annual.csv")
df_ryushutsu = load_csv("toshi_ryushutsu.csv")
df_detail       = load_csv("jichitai_detail.csv")
df_detail_multi = load_csv("jichitai_detail_multi.csv")
df_ts      = load_timeseries()


# ── サイドバー ────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 データ更新")
    st.caption("総務省からダウンロードしたExcelをアップロード")
    up_detail = st.file_uploader("費目別明細 Excel", type=["xlsx"], key="detail")
    up_ts     = st.file_uploader("時系列 Excel", type=["xlsx"], key="ts")
    if up_detail or up_ts:
        if st.button("🔄 パース実行", type="primary"):
            with st.spinner("解析中..."):
                if up_detail:
                    p = RAW_DIR / "001022818_2024detail.xlsx"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(up_detail.read())
                if up_ts:
                    p = RAW_DIR / "001022819_timeseries.xlsx"
                    p.write_bytes(up_ts.read())
                script = Path(__file__).parent.parent / "scripts" / "parse_soumu_excel.py"
                r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
                if r.returncode == 0:
                    st.success("完了！")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(r.stderr)
    st.divider()
    st.markdown("[📖 知識ベース（GitHub）](https://github.com/tgsoccer79-dot/my-project)")
    st.markdown("[📁 総務省 現況調査](https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/)")

# ── タブ ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 市場トレンド",
    "🏆 年間ランキング",
    "🏘️ 自治体プロファイル",
    "⚔️ 自治体比較",
    "🚀 ランキング変動",
    "🗾 都道府県勢力図",
    "📊 ROI・分析",
])


# ═══════════════════════════════════════════════════════════════
# Tab 1: 市場トレンド ＋ 年度スライダー
# ═══════════════════════════════════════════════════════════════
with tab1:
    df_m = df_market.copy()
    df_m["year"] = df_m["year"].astype(int)

    # 年度スライダー
    year_min, year_max = int(df_m["year"].min()), int(df_m["year"].max())
    year_range = st.slider(
        "📅 表示年度を絞り込む",
        year_min, year_max, (year_min, year_max),
        key="trend_slider",
    )
    df_m = df_m[(df_m["year"] >= year_range[0]) & (df_m["year"] <= year_range[1])].copy()
    df_m["year"] = df_m["year"].astype(str)

    latest = df_m.iloc[-1]
    prev   = df_m.iloc[-2] if len(df_m) > 1 else latest
    c1, c2, c3 = st.columns(3)
    c1.metric("受入総額", f"{int(latest['kifu_total_oku']):,} 億円",
              f"+{int(latest['kifu_total_oku']) - int(prev['kifu_total_oku']):,} 億円（前年比）")
    c2.metric("受入件数", f"{int(latest['cases_man']):,} 万件")
    c3.metric("経費率", f"{latest['keihi_rate_pct']}%", delta_color="inverse")

    fig = px.bar(df_m, x="year", y="kifu_total_oku",
                 labels={"year": "年度", "kifu_total_oku": "受入総額（億円）"},
                 color_discrete_sequence=["#2ecc71"], text="kifu_total_oku")
    fig.update_traces(texttemplate="%{text:,}", textposition="outside", textfont_size=10)

    # 主要制度改正をアノテーション
    events = {
        "2015": "ワンストップ特例・控除上限2倍",
        "2019": "3割・地場産品規制",
        "2023": "ポイント禁止予告",
    }
    for yr, label in events.items():
        if year_range[0] <= int(yr) <= year_range[1]:
            fig.add_vline(x=yr, line_dash="dot", line_color="gray", opacity=0.6)
            fig.add_annotation(x=yr, y=df_m["kifu_total_oku"].max() * 0.85,
                               text=label, showarrow=False, font_size=10,
                               textangle=-90, xshift=10)

    fig.update_layout(height=440, margin=dict(t=20, b=20), xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("点線: 主要制度改正年 ／ 出典: 総務省「ふるさと納税に関する現況調査結果」")

    with st.expander("📋 生データ"):
        st.dataframe(df_m, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# Tab 2: 年間ランキング
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.subheader("自治体別 寄附額ランキング")

    col_l, col_r = st.columns([1, 3])
    with col_l:
        years_available = [2024] if not df_detail.empty else sorted(df_ranking["year"].unique(), reverse=True)
        selected_year = st.selectbox("年度", years_available)
        top_n = st.slider("表示件数", 5, 50, 20)

    if not df_detail.empty and selected_year == 2024:
        df_yr = (df_detail[["都道府県", "市区町村", "受入額_億円", "経費率合計", "ポータル費_億円"]]
                 .sort_values("受入額_億円", ascending=False).head(top_n).reset_index(drop=True))
        df_yr.index += 1
        df_yr["自治体"] = df_yr["都道府県"] + " " + df_yr["市区町村"]
        df_yr["経費率"] = (df_yr["経費率合計"] * 100).round(1).astype(str) + "%"
        with col_r:
            fig = px.bar(df_yr, x="受入額_億円", y="自治体", orientation="h",
                         color="受入額_億円", color_continuous_scale="Greens", text="受入額_億円")
            fig.update_traces(texttemplate="%{text:.1f} 億円", textposition="outside")
            fig.update_layout(height=max(400, top_n * 22), margin=dict(t=10, b=10),
                              yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_yr[["自治体", "受入額_億円", "経費率", "ポータル費_億円"]]
                     .rename(columns={"受入額_億円": "受入額（億円）", "ポータル費_億円": "ポータル費（億円）"}),
                     use_container_width=True)
    else:
        df_yr = df_ranking[df_ranking["year"] == selected_year].copy().sort_values("rank")
        df_yr["自治体"] = df_yr["prefecture"] + " " + df_yr["municipality"]
        with col_r:
            fig = px.bar(df_yr.head(top_n), x="kifu_oku", y="自治体", orientation="h",
                         color="kifu_oku", color_continuous_scale="Greens", text="kifu_oku")
            fig.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
            fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    if selected_year == 2024:
        st.info("⚠️ 1位の宝塚市（約257億円）は市立病院への大口個人寄附254億円を含む特殊事例。通常の返礼品目的では白糠町（約212億円）が実質1位。")


# ═══════════════════════════════════════════════════════════════
# Tab 3: 自治体プロファイル ＋ 診断カード ＋ ベンチマーク推薦
# ═══════════════════════════════════════════════════════════════
with tab3:
    if df_ts.empty:
        st.info("総務省Excelをサイドバーからアップロードしてパースするとこのタブが使えます。")
    else:
        df_ranked = calc_ranking(df_ts)

        # ── 自治体選択 ─────────────────────────────────────────
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

        df_muni_ts = df_ranked[df_ranked["市区町村"] == sel_muni].sort_values("年度")
        df_muni_d  = df_detail[df_detail["市区町村"] == sel_muni] if not df_detail.empty else pd.DataFrame()

        if df_muni_ts.empty:
            st.warning(f"{sel_muni} のデータが見つかりません")
        else:
            latest_r = df_muni_ts.iloc[-1]
            prev_r   = df_muni_ts.iloc[-2] if len(df_muni_ts) > 1 else latest_r

            # ── 診断カード ──────────────────────────────────────
            st.markdown("---")
            st.markdown(f"### 🩺 {sel_pref} {sel_muni} 診断カード")
            st.caption("※ 全指標は参考値です。行政判断の根拠には使用しないでください。")

            # 全国分布を使って偏差値計算
            df_all_latest = df_ranked[df_ranked["年度"] == df_ranked["年度"].max()]
            mean_kifu  = df_all_latest["受入額_億円"].mean()
            std_kifu   = df_all_latest["受入額_億円"].std()
            mean_rank  = df_all_latest["順位"].mean()
            std_rank   = df_all_latest["順位"].std()

            kifu_hensachi = int(50 + (latest_r["受入額_億円"] - mean_kifu) / std_kifu * 10) if std_kifu > 0 else 50
            rank_hensachi = int(50 + (mean_rank - latest_r["順位"]) / std_rank * 10) if std_rank > 0 else 50

            # 成長率（直近3年）
            if len(df_muni_ts) >= 4:
                growth_3y = ((latest_r["受入額_億円"] / df_muni_ts.iloc[-4]["受入額_億円"]) ** (1/3) - 1) * 100
            else:
                growth_3y = 0.0

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("受入額", f"{latest_r['受入額_億円']:.1f} 億円",
                      f"{latest_r['受入額_億円'] - prev_r['受入額_億円']:+.1f}（前年比）")
            d2.metric("全国順位", f"{int(latest_r['順位'])} 位",
                      f"{int(prev_r['順位']) - int(latest_r['順位']):+d} 位")
            d3.metric("3年平均成長率", f"{growth_3y:+.1f}%/年")

            if not df_muni_d.empty:
                dr = df_muni_d.iloc[0]
                d4.metric("経費率", f"{dr['経費率合計']*100:.1f}%",
                          delta_color="inverse")

            # 信号機カード
            st.markdown("#### 信号機チェック")
            sig_cols = st.columns(5)
            sig_items = [
                ("受入額偏差値", kifu_hensachi, signal(kifu_hensachi, 45, 55)),
                ("順位偏差値", rank_hensachi, signal(rank_hensachi, 45, 55)),
                ("3年成長率", growth_3y, signal(growth_3y, 0, 10)),
            ]
            if not df_muni_d.empty:
                dr = df_muni_d.iloc[0]
                keihi_pct = dr["経費率合計"] * 100
                portal_pct = dr["ポータル費_億円"] / dr["受入額_億円"] * 100 if dr["受入額_億円"] > 0 else 0
                sig_items += [
                    ("経費率", keihi_pct, signal(keihi_pct, 40, 50, inverse=True)),
                    ("ポータル費率", portal_pct, signal(portal_pct, 10, 15, inverse=True)),
                ]
            for i, (label, val, sig) in enumerate(sig_items):
                with sig_cols[i]:
                    st.markdown(f"**{sig} {label}**")
                    if isinstance(val, float):
                        st.write(f"{val:.1f}")
                    else:
                        st.write(val)

            st.divider()

            # ── 成長曲線 ＋ 順位推移 ──────────────────────────
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 📈 寄附額の成長曲線")
                fig_g = px.area(df_muni_ts, x="年度", y="受入額_億円",
                                color_discrete_sequence=["#2ecc71"])
                fig_g.update_layout(height=300, margin=dict(t=10, b=10))
                st.plotly_chart(fig_g, use_container_width=True)
            with g2:
                st.markdown("#### 🏅 全国順位の推移")
                fig_r = px.line(df_muni_ts, x="年度", y="順位", markers=True,
                                color_discrete_sequence=["#e74c3c"])
                fig_r.update_yaxes(autorange="reversed")
                fig_r.update_layout(height=300, margin=dict(t=10, b=10))
                st.plotly_chart(fig_r, use_container_width=True)

            # ── 経費内訳（多年度トレンド） ──────────────────────
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
                            "年度": int(row_t["年度"]), "費目": label_k,
                            "金額（億円）": round(val / 1e8, 2),
                            "比率(%)": round(val / total_yen * 100, 1) if total_yen else None,
                        })
                df_trend = pd.DataFrame(rows_trend)
                t1, t2 = st.columns(2)
                with t1:
                    fig_trend = px.bar(df_trend, x="年度", y="金額（億円）", color="費目",
                                       barmode="stack",
                                       color_discrete_map={"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                                                           "事務費": "#3498db", "決済費": "#9b59b6",
                                                           "広報費": "#95a5a6", "その他": "#bdc3c7"})
                    fig_trend.update_layout(height=300, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_trend, use_container_width=True)
                with t2:
                    fig_rate = px.bar(df_trend, x="年度", y="比率(%)", color="費目",
                                      barmode="stack",
                                      color_discrete_map={"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                                                          "事務費": "#3498db", "決済費": "#9b59b6",
                                                          "広報費": "#95a5a6", "その他": "#bdc3c7"})
                    fig_rate.add_hline(y=50, line_dash="dash", line_color="red",
                                       annotation_text="5割ルール上限")
                    fig_rate.update_layout(height=300, margin=dict(t=10, b=10),
                                           yaxis_title="経費率（%）")
                    st.plotly_chart(fig_rate, use_container_width=True)
                # 2024年度の詳細
                if not df_muni_d.empty:
                    dr = df_muni_d.iloc[0]
                    portal_pct = dr["ポータル費_億円"] / dr["受入額_億円"] * 100 if dr["受入額_億円"] > 0 else 0
                    st.metric("2024年度 ポータル費", f"{dr['ポータル費_億円']:.2f} 億円",
                              f"{portal_pct:.1f}% of 受入額")
            elif not df_muni_d.empty:
                st.markdown("#### 💰 経費内訳（2024年度）")
                dr = df_muni_d.iloc[0]
                費目 = {"返礼品調達費": dr.get("返礼品調達費_円") or 0,
                        "送付費": dr.get("送付費_円") or 0,
                        "広報費": dr.get("広報費_円") or 0,
                        "決済費": dr.get("決済費_円") or 0,
                        "事務費": dr.get("事務費_円") or 0,
                        "その他": dr.get("その他費_円") or 0}
                df_pie = pd.DataFrame({"費目": 費目.keys(), "金額（円）": 費目.values()})
                df_pie = df_pie[df_pie["金額（円）"] > 0]
                df_pie["金額（億円）"] = (df_pie["金額（円）"] / 1e8).round(2)
                p1, p2 = st.columns([1, 1])
                with p1:
                    fig_pie = px.pie(df_pie, names="費目", values="金額（円）",
                                     color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_pie.update_layout(height=280, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_pie, use_container_width=True)
                with p2:
                    st.dataframe(df_pie[["費目", "金額（億円）"]].assign(
                        割合=lambda d: (d["金額（億円）"] / d["金額（億円）"].sum() * 100).round(1).astype(str) + "%"
                    ), use_container_width=True, hide_index=True)
                    portal_pct = dr["ポータル費_億円"] / dr["受入額_億円"] * 100 if dr["受入額_億円"] > 0 else 0
                    st.metric("ポータル費", f"{dr['ポータル費_億円']:.2f} 億円",
                              f"{portal_pct:.1f}% of 受入額")

            st.divider()

            # ── ベンチマーク自動推薦 ─────────────────────────
            if not df_detail.empty:
                st.markdown("#### 🎯 似た自治体ベンチマーク TOP5")
                st.caption("受入額・経費率・ポータル費率が近い自治体を自動推薦")

                if not df_muni_d.empty:
                    dr = df_muni_d.iloc[0]
                    df_bench = df_detail[df_detail["市区町村"] != sel_muni].copy()
                    df_bench = df_bench[df_bench["受入額_億円"] > 0].copy()

                    # コサイン類似度的なスコア（正規化ユークリッド距離）
                    for col in ["受入額_億円", "経費率合計", "ポータル費_億円"]:
                        col_std = df_bench[col].std()
                        if col_std > 0:
                            df_bench[f"_diff_{col}"] = ((df_bench[col] - dr[col]) / col_std) ** 2
                        else:
                            df_bench[f"_diff_{col}"] = 0
                    df_bench["類似度スコア"] = (
                        df_bench["_diff_受入額_億円"] +
                        df_bench["_diff_経費率合計"] +
                        df_bench["_diff_ポータル費_億円"]
                    )
                    top5 = df_bench.nsmallest(5, "類似度スコア")[
                        ["都道府県", "市区町村", "受入額_億円", "経費率合計", "ポータル費_億円"]
                    ].copy()
                    top5["経費率"] = (top5["経費率合計"] * 100).round(1).astype(str) + "%"
                    top5["推薦理由"] = top5.apply(lambda r: (
                        f"受入額{r['受入額_億円']:.1f}億円・経費率{r['経費率合計']*100:.1f}%が近似"
                    ), axis=1)
                    st.dataframe(top5[["都道府県", "市区町村", "受入額_億円", "経費率", "推薦理由"]]
                                 .rename(columns={"受入額_億円": "受入額（億円）"}),
                                 use_container_width=True, hide_index=True)
                    st.caption("※ 推薦は参考情報です。産業構造・人口・地域特性の類似性は考慮していません。")

            with st.expander("📋 年度別データ（全年度）"):
                st.dataframe(df_muni_ts[["年度", "受入額_億円", "受入件数", "順位"]]
                             .sort_values("年度", ascending=False),
                             use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 4: 自治体比較
# ═══════════════════════════════════════════════════════════════
with tab4:
    if df_ts.empty:
        st.info("総務省Excelをサイドバーからアップロードしてパースするとこのタブが使えます。")
    else:
        st.subheader("⚔️ 自治体を並べて比較する（最大4自治体）")
        df_ranked = calc_ranking(df_ts)
        all_munis_sorted = (df_ranked[df_ranked["年度"] == df_ranked["年度"].max()]
                            .sort_values("順位")["市区町村"].tolist())
        defaults = [m for m in ["白糠町", "都城市", "泉佐野市", "別海町"] if m in all_munis_sorted]
        sel_compare = st.multiselect("自治体を選択（最大4つ）", all_munis_sorted,
                                     default=defaults[:4], max_selections=4)

        if not sel_compare:
            st.info("自治体を選択してください")
        else:
            df_comp = df_ranked[df_ranked["市区町村"].isin(sel_compare)].copy()
            st.markdown("#### 📈 寄附額の推移")
            fig_line = px.line(df_comp, x="年度", y="受入額_億円", color="市区町村",
                               markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
            fig_line.update_layout(height=340, margin=dict(t=10, b=10))
            st.plotly_chart(fig_line, use_container_width=True)

            st.markdown("#### 🏅 全国順位の推移")
            fig_rk = px.line(df_comp, x="年度", y="順位", color="市区町村",
                             markers=True, color_discrete_sequence=px.colors.qualitative.Set1)
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
                                         "比率(%)": round((r.get(col) or 0) / total * 100, 1) if total > 0 else 0})
                    df_cm = pd.DataFrame(rows)
                    fig_c = px.bar(df_cm, x="市区町村", y="比率(%)", color="費目", barmode="stack",
                                   color_discrete_map={"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                                                       "事務費": "#3498db", "決済費": "#9b59b6",
                                                       "広報費": "#95a5a6", "その他": "#bdc3c7"})
                    fig_c.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="5割ルール上限")
                    fig_c.update_layout(height=340, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_c, use_container_width=True)

            st.markdown("#### 📊 2024年度サマリー")
            df_sum = df_comp[df_comp["年度"] == df_comp["年度"].max()][["市区町村", "受入額_億円", "受入件数", "順位"]].copy()
            if not df_detail.empty:
                df_sum = df_sum.merge(df_detail[["市区町村", "経費率合計", "ポータル費_億円"]], on="市区町村", how="left")
                df_sum["経費率"] = (df_sum["経費率合計"] * 100).round(1).astype(str) + "%"
                df_sum = df_sum.drop(columns=["経費率合計"])
            st.dataframe(df_sum, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 5: ランキング変動マップ
# ═══════════════════════════════════════════════════════════════
with tab5:
    if df_ts.empty:
        st.info("総務省Excelをサイドバーからアップロードしてパースするとこのタブが使えます。")
    else:
        st.subheader("🚀 急上昇・急降下した自治体を探す")
        df_ranked = calc_ranking(df_ts)
        years_avail = sorted(df_ranked["年度"].unique())

        col_y1, col_y2, col_t = st.columns([1, 1, 1])
        with col_y1:
            year_curr = st.selectbox("比較対象年度（新）", years_avail[::-1], index=0, key="rank_curr")
        with col_y2:
            year_prev = st.selectbox("比較元年度（旧）",
                                     [y for y in years_avail[::-1] if y < year_curr], index=0, key="rank_prev")
        with col_t:
            top_n_c = st.slider("表示件数", 5, 30, 15)

        df_c = df_ranked[df_ranked["年度"] == year_curr][["市区町村", "都道府県", "受入額_億円", "順位"]].rename(
            columns={"受入額_億円": f"受入額_{year_curr}", "順位": f"順位_{year_curr}"})
        df_p = df_ranked[df_ranked["年度"] == year_prev][["市区町村", "都道府県", "受入額_億円", "順位"]].rename(
            columns={"受入額_億円": f"受入額_{year_prev}", "順位": f"順位_{year_prev}"})
        df_ch = df_c.merge(df_p, on=["市区町村", "都道府県"], how="inner")
        df_ch = df_ch[df_ch[f"受入額_{year_prev}"] >= 1]
        df_ch["順位変動"] = df_ch[f"順位_{year_prev}"] - df_ch[f"順位_{year_curr}"]
        df_ch["受入額変動_億円"] = (df_ch[f"受入額_{year_curr}"] - df_ch[f"受入額_{year_prev}"]).round(2)
        df_ch["受入額変動率"] = ((df_ch["受入額変動_億円"] / df_ch[f"受入額_{year_prev}"]) * 100).round(1)

        st.markdown(f"#### 順位変化マップ（{year_prev}→{year_curr}）")
        df_sc = df_ch[df_ch[f"受入額_{year_curr}"] > 1].copy()
        fig_sc = px.scatter(df_sc, x=f"順位_{year_prev}", y=f"順位_{year_curr}",
                            color="都道府県", size=f"受入額_{year_curr}", size_max=30,
                            hover_name="市区町村",
                            hover_data={"受入額変動_億円": True, "受入額変動率": True,
                                        f"受入額_{year_curr}": True, "都道府県": False})
        max_r = int(df_sc[f"順位_{year_prev}"].max())
        fig_sc.add_shape(type="line", x0=1, y0=1, x1=max_r, y1=max_r,
                         line=dict(dash="dash", color="gray", width=1))
        fig_sc.update_yaxes(autorange="reversed")
        fig_sc.update_xaxes(autorange="reversed")
        fig_sc.update_layout(height=480, margin=dict(t=10, b=10))
        st.plotly_chart(fig_sc, use_container_width=True)
        st.caption("対角線より上＝上昇、下＝下落。円の大きさ＝受入額。宝塚市は特殊事例（大口個人寄附含む）")

        col_u, col_d = st.columns(2)
        with col_u:
            st.markdown("#### 📈 急上昇")
            df_up = df_ch.sort_values("順位変動", ascending=False).head(top_n_c).copy()
            df_up["順位変動"] = df_up["順位変動"].apply(lambda x: f"▲{int(x)}")
            df_up["変動率"] = df_up["受入額変動率"].apply(lambda x: f"+{x}%")
            st.dataframe(df_up[["市区町村", "都道府県", "順位変動", "受入額変動_億円", "変動率",
                                  f"受入額_{year_curr}"]].rename(columns={f"受入額_{year_curr}": "受入額（億円）",
                                                                            "受入額変動_億円": "増加（億円）"}),
                         use_container_width=True, hide_index=True)
        with col_d:
            st.markdown("#### 📉 急降下")
            df_dn = df_ch.sort_values("順位変動").head(top_n_c).copy()
            df_dn["順位変動"] = df_dn["順位変動"].apply(lambda x: f"▼{abs(int(x))}")
            df_dn["変動率"] = df_dn["受入額変動率"].apply(lambda x: f"{x}%")
            st.dataframe(df_dn[["市区町村", "都道府県", "順位変動", "受入額変動_億円", "変動率",
                                  f"受入額_{year_curr}"]].rename(columns={f"受入額_{year_curr}": "受入額（億円）",
                                                                            "受入額変動_億円": "増減（億円）"}),
                         use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 6: 都道府県勢力図
# ═══════════════════════════════════════════════════════════════
with tab6:
    if df_ts.empty:
        st.info("総務省Excelをサイドバーからアップロードしてパースするとこのタブが使えます。")
    else:
        st.subheader("🗾 都道府県の勢力図と県内の突出自治体")
        df_ranked6 = calc_ranking(df_ts)
        years_avail6 = sorted(df_ts["年度"].unique())

        df_pref_ts = (df_ts.groupby(["都道府県", "年度"])["受入額_億円"]
                      .sum().reset_index().sort_values(["都道府県", "年度"]))
        latest_yr6 = df_pref_ts["年度"].max()
        top_prefs = (df_pref_ts[df_pref_ts["年度"] == latest_yr6]
                     .sort_values("受入額_億円", ascending=False).head(15)["都道府県"].tolist())

        st.markdown("#### 都道府県別 受入額の推移")
        sel_prefs_map = st.multiselect("都道府県を選択", sorted(df_pref_ts["都道府県"].unique()),
                                       default=top_prefs, key="pref_map_sel")
        fig_p = px.line(df_pref_ts[df_pref_ts["都道府県"].isin(sel_prefs_map)],
                        x="年度", y="受入額_億円", color="都道府県", markers=True)
        fig_p.update_layout(height=380, margin=dict(t=10, b=10))
        st.plotly_chart(fig_p, use_container_width=True)

        st.divider()
        st.markdown("#### 県内の突出自治体を探す")
        sel_pref_d = st.selectbox("都道府県", sorted(df_ts["都道府県"].unique()),
                                   index=sorted(df_ts["都道府県"].unique()).index("北海道"),
                                   key="pref_drill")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dc = st.selectbox("比較年度（新）", years_avail6[::-1], index=0, key="drill_c")
        with col_d2:
            dp = st.selectbox("比較年度（旧）", [y for y in years_avail6[::-1] if y < dc], index=0, key="drill_p")

        df_drill = df_ts[df_ts["都道府県"] == sel_pref_d].copy()
        pc = df_drill[df_drill["年度"] == dc]["受入額_億円"].sum()
        pp = df_drill[df_drill["年度"] == dp]["受入額_億円"].sum()
        pref_growth6 = (pc - pp) / pp * 100 if pp > 0 else 0
        st.metric(f"{sel_pref_d} 全体成長率（{dp}→{dc}）", f"{pref_growth6:+.1f}%")

        dm_c = df_drill[df_drill["年度"] == dc][["市区町村", "受入額_億円"]].rename(columns={"受入額_億円": "new"})
        dm_p = df_drill[df_drill["年度"] == dp][["市区町村", "受入額_億円"]].rename(columns={"受入額_億円": "old"})
        dm = dm_c.merge(dm_p, on="市区町村")
        dm["成長率(%)"] = ((dm["new"] - dm["old"]) / dm["old"] * 100).round(1)
        dm["vs県平均"] = (dm["成長率(%)"] - pref_growth6).round(1)
        dm = dm.sort_values("成長率(%)", ascending=False)

        fig_d = px.bar(dm, x="市区町村", y="成長率(%)", color="vs県平均",
                       color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                       text="成長率(%)")
        fig_d.add_hline(y=pref_growth6, line_dash="dash", line_color="navy",
                        annotation_text=f"県平均 {pref_growth6:+.1f}%")
        fig_d.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_d.update_layout(height=max(380, len(dm) * 18), margin=dict(t=20, b=10),
                            xaxis_tickangle=-45, coloraxis_showscale=False)
        st.plotly_chart(fig_d, use_container_width=True)
        outliers = dm[dm["vs県平均"] > 20].sort_values("vs県平均", ascending=False)
        if not outliers.empty:
            st.success(f"🔍 県平均を20%以上上回る自治体: {', '.join(outliers['市区町村'].tolist())}")
        with st.expander("📋 全自治体データ"):
            st.dataframe(dm.rename(columns={"new": f"受入額_{dc}（億円）", "old": f"受入額_{dp}（億円）"}),
                         use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# Tab 7: ROI・分析（ROIマトリクス ＋ クラスタリング ＋ 経費構造解剖 ＋ 経費収支）
# ═══════════════════════════════════════════════════════════════
with tab7:
    if df_detail.empty:
        st.info("総務省Excelをサイドバーからアップロードしてパースするとこのタブが使えます。")
    else:
        analysis_tab = st.radio("分析メニュー", ["ROIマトリクス", "クラスタリング", "経費構造解剖", "経費・収支サマリー"],
                                horizontal=True)

        # ── ROIマトリクス ─────────────────────────────────────
        if analysis_tab == "ROIマトリクス":
            st.markdown("### 📊 ROIマトリクス（成長率 × 経費効率）")
            st.caption("⚠️ ROI最大化が自治体ふるさと納税の目的ではありません。あくまで参考指標です。")

            if not df_ts.empty:
                df_roi = calc_ranking(df_ts)
                y_curr, y_prev = 2024, 2023
                rc = df_roi[df_roi["年度"] == y_curr][["市区町村", "都道府県", "受入額_億円"]].rename(
                    columns={"受入額_億円": "受入額_new"})
                rp = df_roi[df_roi["年度"] == y_prev][["市区町村", "都道府県", "受入額_億円"]].rename(
                    columns={"受入額_億円": "受入額_old"})
                df_roi2 = rc.merge(rp, on=["市区町村", "都道府県"])
                df_roi2 = df_roi2[df_roi2["受入額_old"] >= 1]
                df_roi2["成長率(%)"] = ((df_roi2["受入額_new"] - df_roi2["受入額_old"]) / df_roi2["受入額_old"] * 100).round(1)
                df_roi2 = df_roi2.merge(df_detail[["市区町村", "経費率合計"]], on="市区町村", how="left")
                df_roi2 = df_roi2.dropna(subset=["経費率合計"])
                df_roi2["経費率(%)"] = (df_roi2["経費率合計"] * 100).round(1)
                df_roi2 = df_roi2[(df_roi2["成長率(%)"].abs() < 500) & (df_roi2["経費率(%)"] < 80)]

                med_growth = df_roi2["成長率(%)"].median()
                med_cost   = df_roi2["経費率(%)"].median()

                fig_roi = px.scatter(df_roi2, x="経費率(%)", y="成長率(%)",
                                     color="都道府県", size="受入額_new", size_max=25,
                                     hover_name="市区町村",
                                     hover_data={"受入額_new": True, "成長率(%)": True, "経費率(%)": True, "都道府県": False},
                                     labels={"経費率(%)": "経費率（%）→低いほど効率的",
                                             "成長率(%)": "前年比成長率（%）→高いほど成長中"})
                fig_roi.add_hline(y=med_growth, line_dash="dash", line_color="gray")
                fig_roi.add_vline(x=med_cost,   line_dash="dash", line_color="gray")
                fig_roi.add_vline(x=50, line_dash="dot", line_color="red", opacity=0.5)
                # 象限ラベル
                for txt, x, y in [
                    ("🌟 高成長・低コスト", med_cost * 0.5, med_growth * 1.5),
                    ("⚠️ 高成長・高コスト", med_cost * 1.3, med_growth * 1.5),
                    ("😴 低成長・低コスト", med_cost * 0.5, med_growth * 0.3),
                    ("🔴 低成長・高コスト", med_cost * 1.3, med_growth * 0.3),
                ]:
                    fig_roi.add_annotation(x=x, y=y, text=txt, showarrow=False,
                                           font_size=11, opacity=0.5)
                fig_roi.update_layout(height=520, margin=dict(t=20, b=20))
                st.plotly_chart(fig_roi, use_container_width=True)
                st.caption("赤点線: 5割ルール（経費50%上限）／ 灰色点線: 中央値")

        # ── クラスタリング ─────────────────────────────────────
        elif analysis_tab == "クラスタリング":
            st.markdown("### 🔵 自治体クラスタリング（2024年度）")
            st.caption("受入額・経費率・ポータル費でグループ分け。ラベルは参考値です。")

            n_c = st.slider("クラスタ数", 3, 7, 5)
            try:
                df_cl = calc_clusters(df_detail, n_clusters=n_c)
                fig_cl = px.scatter(df_cl, x="経費率合計", y="受入額_億円",
                                    color="クラスタ名", size="ポータル費_億円", size_max=25,
                                    hover_name="市区町村",
                                    hover_data={"都道府県": True, "受入額_億円": True,
                                                "経費率合計": True, "クラスタ名": False},
                                    labels={"経費率合計": "経費率", "受入額_億円": "受入額（億円）"})
                fig_cl.add_vline(x=0.5, line_dash="dot", line_color="red",
                                  annotation_text="5割ルール上限")
                fig_cl.update_layout(height=500, margin=dict(t=20, b=20))
                st.plotly_chart(fig_cl, use_container_width=True)

                st.markdown("#### クラスタ別 統計サマリー")
                summary_cl = df_cl.groupby("クラスタ名").agg(
                    自治体数=("市区町村", "count"),
                    平均受入額=("受入額_億円", "mean"),
                    平均経費率=("経費率合計", "mean"),
                    平均ポータル費=("ポータル費_億円", "mean"),
                ).round(2)
                summary_cl["平均経費率"] = (summary_cl["平均経費率"] * 100).round(1).astype(str) + "%"
                st.dataframe(summary_cl, use_container_width=True)
            except Exception as e:
                st.error(f"クラスタリングエラー: {e}\n\nscikit-learnをインストールしてください: pip install scikit-learn")

        # ── 経費構造解剖 ──────────────────────────────────────
        elif analysis_tab == "経費構造解剖":
            st.markdown("### 🔬 急成長自治体の経費構造解剖")
            st.caption("前年比+50%以上を「急成長」と定義。経費配分のパターンを分析します。")

            # 多年度費目別トレンド（全国集計）
            if not df_detail_multi.empty:
                st.markdown("#### 📅 費目別経費率の年度推移（全国中央値）")
                cost_cols7 = {"返礼品調達費_円": "返礼品調達費", "送付費_円": "送付費",
                              "広報費_円": "広報費", "決済費_円": "決済費",
                              "事務費_円": "事務費", "その他費_円": "その他"}
                rows7 = []
                for yr7, grp7 in df_detail_multi.groupby("年度"):
                    total_yen7 = (grp7["受入額_億円"] * 1e8).sum()
                    if total_yen7 <= 0:
                        continue
                    for col7, lbl7 in cost_cols7.items():
                        s = grp7[col7].fillna(0).sum()
                        rows7.append({"年度": int(yr7), "費目": lbl7,
                                      "比率(%)": round(s / total_yen7 * 100, 2)})
                df_trend7 = pd.DataFrame(rows7)
                fig_trend7 = px.bar(df_trend7, x="年度", y="比率(%)", color="費目",
                                    barmode="stack",
                                    color_discrete_map={"返礼品調達費": "#e74c3c", "送付費": "#e67e22",
                                                        "事務費": "#3498db", "決済費": "#9b59b6",
                                                        "広報費": "#95a5a6", "その他": "#bdc3c7"})
                fig_trend7.add_hline(y=50, line_dash="dash", line_color="red",
                                     annotation_text="5割ルール上限")
                fig_trend7.update_layout(height=340, margin=dict(t=20, b=10),
                                         yaxis_title="経費率（全国合計ベース）（%）")
                st.plotly_chart(fig_trend7, use_container_width=True)
                st.divider()

            if not df_ts.empty:
                df_ranked7 = calc_ranking(df_ts)
                rc2 = df_ranked7[df_ranked7["年度"] == 2024][["市区町村", "都道府県", "受入額_億円"]].rename(
                    columns={"受入額_億円": "受入額_2024"})
                rp2 = df_ranked7[df_ranked7["年度"] == 2023][["市区町村", "都道府県", "受入額_億円"]].rename(
                    columns={"受入額_億円": "受入額_2023"})
                df_gr = rc2.merge(rp2, on=["市区町村", "都道府県"])
                df_gr = df_gr[df_gr["受入額_2023"] >= 1]
                df_gr["成長率"] = ((df_gr["受入額_2024"] - df_gr["受入額_2023"]) / df_gr["受入額_2023"] * 100).round(1)
                df_rapid = df_gr[df_gr["成長率"] >= 50].sort_values("成長率", ascending=False)
                df_rapid = df_rapid.merge(df_detail[["市区町村", "受入額_億円", "経費率合計", "返礼品調達費_円",
                                                      "送付費_円", "広報費_円", "ポータル費_億円"]],
                                          on="市区町村", how="inner")

                st.metric("急成長自治体数（前年比+50%以上）", f"{len(df_rapid)} 自治体")

                fig_gr = px.bar(df_rapid.head(20), x="市区町村", y="成長率",
                                color="経費率合計", color_continuous_scale="RdYlGn_r",
                                text="成長率", hover_data={"都道府県": True})
                fig_gr.add_hline(y=50, line_dash="dot", line_color="blue")
                fig_gr.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
                fig_gr.update_layout(height=380, margin=dict(t=10, b=10), xaxis_tickangle=-45,
                                     coloraxis_showscale=False)
                st.plotly_chart(fig_gr, use_container_width=True)

                st.markdown("#### 急成長自治体の経費内訳パターン")
                df_rapid["広告費比率"] = (df_rapid["広報費_円"] / (df_rapid["受入額_億円"] * 1e8) * 100).round(1)
                df_rapid["返礼品比率"] = (df_rapid["返礼品調達費_円"] / (df_rapid["受入額_億円"] * 1e8) * 100).round(1)
                st.dataframe(df_rapid[["市区町村", "都道府県", "成長率", "受入額_2024", "経費率合計",
                                       "返礼品比率", "広告費比率", "ポータル費_億円"]].rename(
                    columns={"受入額_2024": "受入額（億円）", "成長率": "成長率(%)",
                             "経費率合計": "経費率", "ポータル費_億円": "ポータル費（億円）"}
                ).head(20), use_container_width=True, hide_index=True)

        # ── 経費・収支サマリー ────────────────────────────────
        else:
            st.markdown("### 💰 費目別 経費内訳（全国集計）")
            df_k = df_keihi.copy()
            df_k["year"] = df_k["year"].astype(str)
            cost_map = {"henreihin_oku": "返礼品調達費", "soryo_oku": "送料",
                        "jimu_oku": "事務費等", "kessai_oku": "決済費用", "koho_oku": "広報費"}
            df_mk = df_k[["year"] + list(cost_map.keys())].melt(id_vars="year", var_name="c", value_name="億円")
            df_mk["費目"] = df_mk["c"].map(cost_map)
            fig_k = px.bar(df_mk, x="year", y="億円", color="費目", barmode="stack",
                           color_discrete_map={"返礼品調達費": "#e74c3c", "送料": "#e67e22",
                                               "事務費等": "#3498db", "決済費用": "#9b59b6", "広報費": "#95a5a6"})
            fig_k.update_layout(height=360, margin=dict(t=10, b=10))
            st.plotly_chart(fig_k, use_container_width=True)

            lk = df_keihi.iloc[-1]
            ck1, ck2, ck3, ck4 = st.columns(4)
            ck1.metric("2024年度 経費率", f"{lk['keihi_rate_pct']}%")
            ck2.metric("返礼品調達費率", f"{lk['henreihin_rate_pct']}%")
            ck3.metric("ポータル手数料", f"{int(lk['portal_fee_oku']):,} 億円", f"{lk['portal_fee_rate_pct']}%")
            ck4.metric("自治体の手残り", f"{int(lk['jiyu_zaisgen_oku']):,} 億円")
            st.caption("注: ポータル手数料（13.0%）は全受入額比。仲介サイト経由額比では11.5%（別調査）")

            if not df_detail.empty:
                st.divider()
                st.markdown("#### 都道府県別 平均経費率（2024年度）")
                df_pref7 = (df_detail.groupby("都道府県")
                            .agg(受入額合計=("受入額_億円", "sum"), 経費合計=("経費合計_億円", "sum"))
                            .reset_index())
                df_pref7["経費率"] = (df_pref7["経費合計"] / df_pref7["受入額合計"] * 100).round(1)
                fig_pref7 = px.bar(df_pref7.sort_values("経費率", ascending=False),
                                   x="都道府県", y="経費率", color="経費率",
                                   color_continuous_scale="RdYlGn_r", text="経費率")
                fig_pref7.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig_pref7.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50%上限")
                fig_pref7.update_layout(height=400, margin=dict(t=20, b=20), xaxis_tickangle=-45,
                                        coloraxis_showscale=False)
                st.plotly_chart(fig_pref7, use_container_width=True)

            st.divider()
            st.markdown("#### 🏙️ 都市部の住民税流出・収支損失")
            df_r7 = df_ryushutsu.copy()
            df_tok7 = df_r7[df_r7["jichitai"] == "東京都"].sort_values("year")
            if not df_tok7.empty:
                fig_t7 = px.line(df_tok7, x="year", y="ryushutsu_oku", markers=True,
                                  title="東京都 住民税流出額の推移",
                                  labels={"year": "年度", "ryushutsu_oku": "流出額（億円）"})
                fig_t7.update_traces(line_color="#e74c3c", marker_size=10)
                fig_t7.update_layout(height=250, margin=dict(t=40, b=10))
                st.plotly_chart(fig_t7, use_container_width=True)
            df_lat7 = (df_r7[df_r7["jichitai"] != "東京都"].sort_values("year", ascending=False)
                       .drop_duplicates("jichitai").sort_values("ryushutsu_oku", ascending=False))
            fig_l7 = px.bar(df_lat7, x="jichitai", y="ryushutsu_oku", color="kofu_hokan",
                             labels={"jichitai": "自治体", "ryushutsu_oku": "損失額（億円）", "kofu_hokan": "交付税補填"},
                             color_discrete_map={"なし（不交付団体）": "#e74c3c", "あり（交付団体・75%補填）": "#f39c12"},
                             text="ryushutsu_oku")
            fig_l7.update_traces(texttemplate="%{text:,} 億円", textposition="outside")
            fig_l7.update_layout(height=320, margin=dict(t=10, b=10))
            st.plotly_chart(fig_l7, use_container_width=True)
            st.info("🔴 不交付団体（東京23区・川崎市等）は補填ゼロ\n\n🟡 交付団体（横浜・名古屋・大阪等）は75%が地方交付税で補填")
