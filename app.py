import streamlit as st
import pandas as pd
import yfinance as yf


st.set_page_config(page_title="財務分析アプリ", layout="wide")


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


def resolve_ticker(user_input):
    text = user_input.strip()
    key = text.lower()

    if not text:
        return ""

    if key in COMPANY_ALIASES:
        return COMPANY_ALIASES[key]

    if text.isdigit() and len(text) == 4:
        return f"{text}.T"

    return text.upper()


def translate_item(item):
    item = str(item)
    return FINANCIAL_ITEM_JA.get(item, item)


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


def get_series(df, names):
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


def format_number(value):
    if value is None or pd.isna(value):
        return "N/A"

    try:
        return f"{value:,.0f}"
    except Exception:
        return str(value)


def format_percent(value):
    if value is None or pd.isna(value):
        return "N/A"

    try:
        return f"{value:.2%}"
    except Exception:
        return str(value)


def statement_to_display(df):
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    out.index = [translate_item(idx) for idx in out.index]

    new_cols = []
    for col in out.columns:
        if hasattr(col, "strftime"):
            new_cols.append(col.strftime("%Y-%m-%d"))
        else:
            new_cols.append(str(col))

    out.columns = new_cols
    out = out.T.reset_index().rename(columns={"index": "決算日"})

    return out


def build_trend_df(income_df, bs_df):
    revenue = get_series(income_df, ["Total Revenue", "Revenue", "Operating Revenue"])
    operating_income = get_series(income_df, ["Operating Income"])
    net_income = get_series(income_df, ["Net Income", "Net Income Common Stockholders"])
    equity = get_series(bs_df, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])

    trend_df = pd.DataFrame({
        "売上高": revenue,
        "営業利益": operating_income,
        "純利益": net_income,
        "自己資本": equity,
    })

    trend_df = trend_df.sort_index()

    if not trend_df.empty:
        trend_df["営業利益率"] = trend_df["営業利益"] / trend_df["売上高"]
        trend_df["純利益率"] = trend_df["純利益"] / trend_df["売上高"]
        trend_df["ROE"] = trend_df["純利益"] / trend_df["自己資本"]
        trend_df = trend_df.replace([float("inf"), float("-inf")], pd.NA)

    return trend_df


@st.cache_data(show_spinner=False)
def fetch_data(ticker_symbol):
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


st.title("企業名・株式コード・ティッカーから財務データを取得するアプリ")

st.success("アプリは起動しています。")

st.write("入力例：Apple / AAPL / Microsoft / MSFT / トヨタ / 7203 / ソーファイ / SOFI")

user_input = st.text_input(
    "企業名・株式コード・ティッカーを入力してください",
    placeholder="例：Apple、AAPL、トヨタ、7203"
)

ticker_symbol = resolve_ticker(user_input)

if user_input:
    st.info(f"変換後のティッカー: {ticker_symbol}")

run_button = st.button("財務データを取得する")

if run_button:
    if not ticker_symbol:
        st.error("企業名・株式コード・ティッカーを入力してください。")
        st.stop()

    try:
        with st.spinner("財務データを取得中です。少し待ってください。"):
            data = fetch_data(ticker_symbol)

        info = data["info"]
        annual_income = data["annual_income"]
        quarterly_income = data["quarterly_income"]
        annual_bs = data["annual_bs"]
        quarterly_bs = data["quarterly_bs"]
        annual_cf = data["annual_cf"]
        quarterly_cf = data["quarterly_cf"]

        if (
            (annual_income is None or annual_income.empty)
            and (annual_bs is None or annual_bs.empty)
            and (annual_cf is None or annual_cf.empty)
        ):
            st.error("財務データを取得できませんでした。ティッカーが正しいか確認してください。")
            st.stop()

        company_name = info.get("longName") or info.get("shortName") or ticker_symbol
        currency = info.get("currency", "N/A")
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")

        st.subheader(company_name)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ティッカー", ticker_symbol)
        c2.metric("通貨", currency)
        c3.metric("セクター", sector)
        c4.metric("業種", industry)

        latest_revenue = get_latest_value(annual_income, ["Total Revenue", "Revenue", "Operating Revenue"])
        latest_operating_income = get_latest_value(annual_income, ["Operating Income"])
        latest_net_income = get_latest_value(annual_income, ["Net Income", "Net Income Common Stockholders"])
        latest_total_assets = get_latest_value(annual_bs, ["Total Assets"])
        latest_equity = get_latest_value(annual_bs, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
        latest_operating_cf = get_latest_value(annual_cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])

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

        st.markdown("## 最新年度の主要指標")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("売上高", format_number(latest_revenue))
        m2.metric("営業利益", format_number(latest_operating_income))
        m3.metric("純利益", format_number(latest_net_income))
        m4.metric("総資産", format_number(latest_total_assets))
        m5.metric("自己資本", format_number(latest_equity))
        m6.metric("営業CF", format_number(latest_operating_cf))

        st.markdown("## 収益性指標")

        r1, r2, r3 = st.columns(3)
        r1.metric("営業利益率", format_percent(latest_operating_margin))
        r2.metric("純利益率", format_percent(latest_net_margin))
        r3.metric("ROE", format_percent(latest_roe))

        trend_df = build_trend_df(annual_income, annual_bs)

        st.markdown("## 売上高・営業利益・純利益の推移")

        if trend_df.empty:
            st.info("グラフ表示に必要なデータがありません。")
        else:
            chart_df = trend_df[["売上高", "営業利益", "純利益"]].dropna(how="all")
            if chart_df.empty:
                st.info("売上高・営業利益・純利益のデータが不足しています。")
            else:
                st.line_chart(chart_df)

        st.markdown("## ROE・営業利益率・純利益率の推移")

        if trend_df.empty:
            st.info("収益性指標のグラフ表示に必要なデータがありません。")
        else:
            ratio_df = trend_df[["ROE", "営業利益率", "純利益率"]].copy()
            ratio_df = ratio_df * 100
            ratio_df = ratio_df.dropna(how="all")

            if ratio_df.empty:
                st.info("ROE・営業利益率・純利益率のデータが不足しています。")
            else:
                st.line_chart(ratio_df)

        st.markdown("## 年次トレンドデータ")

        if trend_df.empty:
            st.info("年次トレンドデータがありません。")
        else:
            display_trend_df = trend_df.copy()

            for col in ["営業利益率", "純利益率", "ROE"]:
                if col in display_trend_df.columns:
                    display_trend_df[col] = display_trend_df[col].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                    )

            st.dataframe(display_trend_df, use_container_width=True)

        st.markdown("## 財務三表")

        annual_tab, quarterly_tab = st.tabs(["年次財務諸表", "四半期財務諸表"])

        with annual_tab:
            pl_tab, bs_tab, cf_tab = st.tabs(["損益計算書", "貸借対照表", "キャッシュフロー計算書"])

            with pl_tab:
                df = statement_to_display(annual_income)
                if df.empty:
                    st.info("年次の損益計算書データはありません。")
                else:
                    st.dataframe(df, use_container_width=True)

            with bs_tab:
                df = statement_to_display(annual_bs)
                if df.empty:
                    st.info("年次の貸借対照表データはありません。")
                else:
                    st.dataframe(df, use_container_width=True)

            with cf_tab:
                df = statement_to_display(annual_cf)
                if df.empty:
                    st.info("年次のキャッシュフロー計算書データはありません。")
                else:
                    st.dataframe(df, use_container_width=True)

        with quarterly_tab:
            q_pl_tab, q_bs_tab, q_cf_tab = st.tabs(["損益計算書", "貸借対照表", "キャッシュフロー計算書"])

            with q_pl_tab:
                df = statement_to_display(quarterly_income)
                if df.empty:
                    st.info("四半期の損益計算書データはありません。")
                else:
                    st.dataframe(df, use_container_width=True)

            with q_bs_tab:
                df = statement_to_display(quarterly_bs)
                if df.empty:
                    st.info("四半期の貸借対照表データはありません。")
                else:
                    st.dataframe(df, use_container_width=True)

            with q_cf_tab:
                df = statement_to_display(quarterly_cf)
                if df.empty:
                    st.info("四半期のキャッシュフロー計算書データはありません。")
                else:
                    st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

else:
    st.info("入力後に「財務データを取得する」ボタンを押してください。")