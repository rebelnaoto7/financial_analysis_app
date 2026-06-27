"""
財務データ取得・整形のロジック層。

Streamlit版 app.py の純粋ロジック（resolve_ticker / fetch_data / 各種整形）を
そのまま移植し、Django のビューから呼び出せる関数 `analyze()` に集約した。
yfinance は遅延インポート（fetch_data 内）にして、未インストール環境でも
モジュール自体のインポートは失敗しないようにしている。
"""
from __future__ import annotations

import pandas as pd

# ------------------------------------------------------------------
# 定数（app.py からそのまま移植）
# ------------------------------------------------------------------
COMPANY_ALIASES = {
    "apple": "AAPL",
    "アップル": "AAPL",
    "microsoft": "MSFT",
    "マイクロソフト": "MSFT",
    "nvidia": "NVDA",
    "エヌビディア": "NVDA",
    "amazon": "AMZN",
    "アマゾン": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "グーグル": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "メタ": "META",
    "tesla": "TSLA",
    "テスラ": "TSLA",
    "sofi": "SOFI",
    "sofi technologies": "SOFI",
    "ソーファイ": "SOFI",
    "トヨタ": "7203.T",
    "トヨタ自動車": "7203.T",
    "toyota": "7203.T",
    "toyota motor": "7203.T",
    "ソニー": "6758.T",
    "ソニーグループ": "6758.T",
    "sony": "6758.T",
    "任天堂": "7974.T",
    "nintendo": "7974.T",
    "ソフトバンク": "9984.T",
    "ソフトバンクグループ": "9984.T",
    "softbank": "9984.T",
    "キーエンス": "6861.T",
    "keyence": "6861.T",
    "三菱ufj": "8306.T",
    "mufg": "8306.T",
    "ntt": "9432.T",
    "日本電信電話": "9432.T",
}

FINANCIAL_ITEM_JA = {
    "Total Revenue": "売上高",
    "Operating Revenue": "営業収益",
    "Cost Of Revenue": "売上原価",
    "Gross Profit": "売上総利益",
    "Operating Income": "営業利益",
    "Net Income": "純利益",
    "Net Income Common Stockholders": "普通株主に帰属する純利益",
    "Basic EPS": "基本EPS",
    "Diluted EPS": "希薄化後EPS",
    "Total Assets": "総資産",
    "Current Assets": "流動資産",
    "Cash And Cash Equivalents": "現金及び現金同等物",
    "Inventory": "棚卸資産",
    "Total Liabilities Net Minority Interest": "負債合計",
    "Current Liabilities": "流動負債",
    "Long Term Debt": "長期借入金・社債",
    "Total Debt": "有利子負債",
    "Stockholders Equity": "株主資本",
    "Common Stock Equity": "自己資本",
    "Total Equity Gross Minority Interest": "自己資本合計",
    "Retained Earnings": "利益剰余金",
    "Operating Cash Flow": "営業キャッシュフロー",
    "Cash Flow From Continuing Operating Activities": "継続事業からの営業CF",
    "Investing Cash Flow": "投資キャッシュフロー",
    "Financing Cash Flow": "財務キャッシュフロー",
    "Capital Expenditure": "設備投資",
    "Free Cash Flow": "フリーキャッシュフロー",
}


# ------------------------------------------------------------------
# ティッカー解決・翻訳
# ------------------------------------------------------------------
def resolve_ticker(user_input: str) -> str:
    text = (user_input or "").strip()
    key = text.lower()
    if not text:
        return ""
    if key in COMPANY_ALIASES:
        return COMPANY_ALIASES[key]
    # 4桁の数字 → 日本株コード (例: 7203 → 7203.T)
    if text.isdigit() and len(text) == 4:
        return f"{text}.T"
    return text.upper()


def translate_item(item) -> str:
    item = str(item)
    return FINANCIAL_ITEM_JA.get(item, item)


# ------------------------------------------------------------------
# DataFrame ユーティリティ
# ------------------------------------------------------------------
def find_row(df, names):
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            row = df.loc[name]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            return row
    lower_map = {str(idx).lower(): idx for idx in df.index}
    for name in names:
        if name.lower() in lower_map:
            row = df.loc[lower_map[name.lower()]]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            return row
    return None


def get_latest_value(df, names):
    row = find_row(df, names)
    if row is None:
        return None
    row = pd.to_numeric(row, errors="coerce").dropna()
    if row.empty:
        return None
    try:
        row.index = pd.to_datetime(row.index)
        row = row.sort_index()
    except Exception:
        pass
    return row.iloc[-1]


def get_series(df, names) -> pd.Series:
    row = find_row(df, names)
    if row is None:
        return pd.Series(dtype="float64")
    series = pd.to_numeric(row, errors="coerce").dropna()
    try:
        series.index = pd.to_datetime(series.index)
        series = series.sort_index()
    except Exception:
        pass
    return series


# ------------------------------------------------------------------
# 表示用フォーマッタ
# ------------------------------------------------------------------
def format_number(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{value:,.0f}"
    except Exception:
        return str(value)


def format_percent(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{value:.2%}"
    except Exception:
        return str(value)


# ------------------------------------------------------------------
# 財務諸表 → テンプレート描画用の辞書（columns / rows）
# ------------------------------------------------------------------
def statement_to_table(df):
    """財務諸表 DataFrame を {"columns": [...], "rows": [...]} に変換。

    Streamlit版の statement_to_display() に相当。行=項目（日本語訳）、列=決算日。
    """
    if df is None or df.empty:
        return {"columns": [], "rows": []}

    out = df.copy()
    out.index = [translate_item(idx) for idx in out.index]

    new_cols = []
    for col in out.columns:
        if hasattr(col, "strftime"):
            new_cols.append(col.strftime("%Y-%m-%d"))
        else:
            new_cols.append(str(col))
    out.columns = new_cols

    columns = ["項目"] + list(out.columns)
    rows = []
    for idx, series in out.iterrows():
        cells = [format_number(v) for v in series.tolist()]
        rows.append([str(idx)] + cells)
    return {"columns": columns, "rows": rows}


# ------------------------------------------------------------------
# トレンドデータの構築
# ------------------------------------------------------------------
def build_trend(income_df, bs_df):
    """売上・営業利益・純利益・自己資本と各種比率をまとめた辞書を返す。

    返り値:
      {
        "labels": ["2022", "2023", ...],          # 決算年(西暦)
        "revenue": [...], "operating_income": [...], "net_income": [...],
        "operating_margin": [...], "net_margin": [...], "roe": [...],  # 単位%
        "table": [ {year, revenue, ...}, ... ],    # テーブル描画用（整形済み文字列）
      }
    """
    revenue = get_series(income_df, ["Total Revenue", "Revenue", "Operating Revenue"])
    operating_income = get_series(income_df, ["Operating Income"])
    net_income = get_series(income_df, ["Net Income", "Net Income Common Stockholders"])
    equity = get_series(
        bs_df,
        ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"],
    )

    trend = pd.DataFrame(
        {
            "revenue": revenue,
            "operating_income": operating_income,
            "net_income": net_income,
            "equity": equity,
        }
    ).sort_index()

    empty = {
        "labels": [],
        "revenue": [],
        "operating_income": [],
        "net_income": [],
        "operating_margin": [],
        "net_margin": [],
        "roe": [],
        "table": [],
    }
    if trend.empty:
        return empty

    trend["operating_margin"] = trend["operating_income"] / trend["revenue"]
    trend["net_margin"] = trend["net_income"] / trend["revenue"]
    trend["roe"] = trend["net_income"] / trend["equity"]
    trend = trend.replace([float("inf"), float("-inf")], pd.NA)

    # ラベル（西暦年）。datetime に変換できれば年だけ取り出す。
    labels = []
    for idx in trend.index:
        if hasattr(idx, "strftime"):
            labels.append(idx.strftime("%Y"))
        else:
            labels.append(str(idx))

    def num_list(col):
        return [None if pd.isna(v) else float(v) for v in trend[col].tolist()]

    def pct_list(col):
        return [None if pd.isna(v) else round(float(v) * 100, 2) for v in trend[col].tolist()]

    table = []
    for i, label in enumerate(labels):
        table.append(
            {
                "year": label,
                "revenue": format_number(trend["revenue"].iloc[i]),
                "operating_income": format_number(trend["operating_income"].iloc[i]),
                "net_income": format_number(trend["net_income"].iloc[i]),
                "equity": format_number(trend["equity"].iloc[i]),
                "operating_margin": format_percent(trend["operating_margin"].iloc[i]),
                "net_margin": format_percent(trend["net_margin"].iloc[i]),
                "roe": format_percent(trend["roe"].iloc[i]),
            }
        )

    return {
        "labels": labels,
        "revenue": num_list("revenue"),
        "operating_income": num_list("operating_income"),
        "net_income": num_list("net_income"),
        "operating_margin": pct_list("operating_margin"),
        "net_margin": pct_list("net_margin"),
        "roe": pct_list("roe"),
        "table": table,
    }


# ------------------------------------------------------------------
# yfinance によるデータ取得（遅延インポート）
# ------------------------------------------------------------------
def fetch_data(ticker_symbol: str) -> dict:
    """yfinance から財務データを取得。Streamlit版 fetch_data() に相当。"""
    import yfinance as yf  # 遅延インポート

    ticker = yf.Ticker(ticker_symbol)
    try:
        info = ticker.info
    except Exception:
        info = {}
    return {
        "info": info,
        "annual_income": ticker.income_stmt,
        "quarterly_income": ticker.quarterly_income_stmt,
        "annual_bs": ticker.balance_sheet,
        "quarterly_bs": ticker.quarterly_balance_sheet,
        "annual_cf": ticker.cashflow,
        "quarterly_cf": ticker.quarterly_cashflow,
    }


# ------------------------------------------------------------------
# 高レベルAPI：ビューから呼ぶエントリポイント
# ------------------------------------------------------------------
class AnalysisError(Exception):
    """財務分析中に利用者へ表示すべきエラー。"""


def analyze(user_input: str) -> dict:
    """企業名/コード/ティッカー文字列を受け取り、テンプレート用の context を返す。

    例外は AnalysisError に丸めて投げる（ビュー側でメッセージ表示）。
    """
    ticker_symbol = resolve_ticker(user_input)
    if not ticker_symbol:
        raise AnalysisError("企業名・株式コード・ティッカーを入力してください。")

    try:
        data = fetch_data(ticker_symbol)
    except ModuleNotFoundError as exc:
        raise AnalysisError(
            "yfinance がインストールされていません。`pip install yfinance` を実行してください。"
        ) from exc
    except Exception as exc:  # 通信エラー等
        raise AnalysisError(f"データ取得中にエラーが発生しました: {exc}") from exc

    info = data["info"]
    annual_income = data["annual_income"]
    annual_bs = data["annual_bs"]
    annual_cf = data["annual_cf"]

    if (
        (annual_income is None or annual_income.empty)
        and (annual_bs is None or annual_bs.empty)
        and (annual_cf is None or annual_cf.empty)
    ):
        raise AnalysisError(
            "財務データを取得できませんでした。ティッカーが正しいか確認してください。"
        )

    company_name = info.get("longName") or info.get("shortName") or ticker_symbol

    # 最新値
    latest_revenue = get_latest_value(annual_income, ["Total Revenue", "Revenue", "Operating Revenue"])
    latest_operating_income = get_latest_value(annual_income, ["Operating Income"])
    latest_net_income = get_latest_value(annual_income, ["Net Income", "Net Income Common Stockholders"])
    latest_total_assets = get_latest_value(annual_bs, ["Total Assets"])
    latest_equity = get_latest_value(
        annual_bs,
        ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"],
    )
    latest_operating_cf = get_latest_value(
        annual_cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]
    )

    # 収益性指標
    latest_operating_margin = None
    latest_net_margin = None
    latest_roe = None
    if latest_revenue is not None and latest_revenue != 0:
        if latest_operating_income is not None:
            latest_operating_margin = latest_operating_income / latest_revenue
        if latest_net_income is not None:
            latest_net_margin = latest_net_income / latest_revenue
    if latest_equity is not None and latest_equity != 0:
        if latest_net_income is not None:
            latest_roe = latest_net_income / latest_equity

    trend = build_trend(annual_income, annual_bs)

    return {
        "ticker_symbol": ticker_symbol,
        "company_name": company_name,
        "currency": info.get("currency", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "metrics": {
            "revenue": format_number(latest_revenue),
            "operating_income": format_number(latest_operating_income),
            "net_income": format_number(latest_net_income),
            "total_assets": format_number(latest_total_assets),
            "equity": format_number(latest_equity),
            "operating_cf": format_number(latest_operating_cf),
        },
        "profitability": {
            "operating_margin": format_percent(latest_operating_margin),
            "net_margin": format_percent(latest_net_margin),
            "roe": format_percent(latest_roe),
        },
        "trend": trend,
        "statements": {
            "annual": {
                "pl": statement_to_table(annual_income),
                "bs": statement_to_table(annual_bs),
                "cf": statement_to_table(annual_cf),
            },
            "quarterly": {
                "pl": statement_to_table(data["quarterly_income"]),
                "bs": statement_to_table(data["quarterly_bs"]),
                "cf": statement_to_table(data["quarterly_cf"]),
            },
        },
    }
