"""
総務省現況調査Excelパーサー
使い方: python scripts/parse_soumu_excel.py
出力: data/jichitai_detail.csv, data/jichitai_timeseries.csv
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"


def parse_detail(xlsx_path: Path, year: int) -> pd.DataFrame:
    """
    001022818形式（費目別経費明細）を読み込む。
    ヘッダーは行8〜14の複数行なので、データ行（行15以降）を直接指定して読む。
    """
    df = pd.read_excel(xlsx_path, sheet_name=0, header=None, skiprows=14, dtype=str)

    # 列の定義（0始まり）
    col_map = {
        0:  "団体コード",
        1:  "都道府県",
        2:  "市区町村",
        3:  "受入件数",
        4:  "受入額_円",
        11: "返礼品調達費_円",
        12: "送付費_円",
        13: "広報費_円",
        14: "決済費_円",
        15: "事務費_円",
        16: "その他費_円",
        17: "経費合計_円",
        18: "返礼品率",
        19: "送付費率",
        20: "広報費率",
        21: "決済費率",
        22: "事務費率",
        24: "経費率合計",
        25: "ポータル費_円",
    }

    df = df[list(col_map.keys())].rename(columns=col_map)

    # 団体コードが数字の行だけ残す（ヘッダー残骸・集計行を除外）
    df = df[df["団体コード"].str.match(r"^\d+$", na=False)].copy()

    # 数値変換
    num_cols = [c for c in df.columns if c != "都道府県" and c != "市区町村" and c != "団体コード"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["年度"] = year
    df["受入額_億円"] = (df["受入額_円"] / 1e8).round(2)
    df["経費合計_億円"] = (df["経費合計_円"] / 1e8).round(2)
    df["ポータル費_億円"] = (df["ポータル費_円"] / 1e8).round(2)

    return df


def parse_timeseries(xlsx_path: Path) -> pd.DataFrame:
    """
    001022819形式（各団体一覧・時系列）を読み込む。
    行2: 年度ヘッダー（奇数列=金額・偶数列=件数）
    行5以降: データ
    単位: 千円
    """
    raw = pd.read_excel(xlsx_path, sheet_name="各団体一覧", header=None, dtype=str)

    # 年度ラベルを取得（行2, 3列目以降）
    year_row = raw.iloc[1].tolist()
    years = []
    for v in year_row[2:]:
        if pd.notna(v) and v not in ["None", ""]:
            years.append(str(v).strip())
        else:
            years.append(None)

    # 年度を前方埋め（1年度につき金額・件数の2列）
    filled_years = []
    last = None
    for y in years:
        if y:
            last = y
        filled_years.append(last)

    records = []
    for _, row in raw.iloc[4:].iterrows():
        row = row.tolist()
        pref = str(row[0]).strip() if pd.notna(row[0]) else None
        muni = str(row[1]).strip() if pd.notna(row[1]) and row[1] not in ["None", "nan"] else None

        if not pref or pref in ["None", "nan"]:
            continue

        # 2列ずつ（金額・件数）
        data_vals = row[2:]
        for i in range(0, len(filled_years) - 1, 2):
            if i >= len(data_vals):
                break
            year_label = filled_years[i]
            if not year_label:
                continue
            kinGaku = data_vals[i] if i < len(data_vals) else None
            kenSuu = data_vals[i + 1] if i + 1 < len(data_vals) else None

            try:
                kin = float(kinGaku) if kinGaku not in [None, "None", "nan", ""] else None
                ken = float(kenSuu) if kenSuu not in [None, "None", "nan", ""] else None
            except (ValueError, TypeError):
                kin, ken = None, None

            records.append({
                "都道府県": pref,
                "市区町村": muni if muni else pref,
                "年度ラベル": year_label,
                "受入額_千円": kin,
                "受入件数": ken,
            })

    df = pd.DataFrame(records)

    # 年度ラベル→西暦変換
    def label_to_year(label):
        mapping = {
            "平成20年度": 2008, "平成21年度": 2009, "平成22年度": 2010, "平成23年度": 2011,
            "平成24年度": 2012, "平成25年度": 2013, "平成26年度": 2014, "平成27年度": 2015,
            "平成28年度": 2016, "平成29年度": 2017, "平成30年度": 2018, "令和元年度": 2019,
            "令和２年度": 2020, "令和３年度": 2021, "令和４年度": 2022, "令和５年度": 2023,
            "令和６年度": 2024,
        }
        return mapping.get(label)

    df["年度"] = df["年度ラベル"].apply(label_to_year)
    df["受入額_億円"] = (df["受入額_千円"] / 1e5).round(2)
    df = df.dropna(subset=["年度", "受入額_千円"])
    return df[["都道府県", "市区町村", "年度", "受入額_億円", "受入件数"]].sort_values(
        ["都道府県", "市区町村", "年度"]
    )


if __name__ == "__main__":
    # 費目別明細
    detail_path = RAW_DIR / "001022818_2024detail.xlsx"
    if detail_path.exists():
        print("パース中: 費目別明細...")
        df_detail = parse_detail(detail_path, year=2024)
        out = DATA_DIR / "jichitai_detail.csv"
        df_detail.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"  → {out} ({len(df_detail)}行)")

    # 時系列
    ts_path = RAW_DIR / "001022819_timeseries.xlsx"
    if ts_path.exists():
        print("パース中: 時系列...")
        df_ts = parse_timeseries(ts_path)
        out = DATA_DIR / "jichitai_timeseries.csv"
        df_ts.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"  → {out} ({len(df_ts)}行)")

    print("完了!")
