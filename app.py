import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Single Firm Financial Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Single Firm Financial Analysis")
st.caption("RUNNING: SINGLE_FIRM_APP_V1")
st.write("1社の財務データを時系列で分析します。")

# =========================
# Sample Data
# Microsoft FY2021-FY2024 style sample data
# Unit: USD millions / Shares: millions
# =========================
sample_rows = [
    {
        "Year": 2021,
        "Revenue": 168088,
        "Operating_Income": 69916,
        "Net_Income": 61271,
        "Total_Assets": 333779,
        "Equity": 141988,
        "Debt": 67775,
        "Cash": 130334,
        "Operating_CF": 76740,
        "Capex": 20622,
        "Shares_Outstanding": 7519,
        "Stock_Price": 281.92,
        "Tax_Rate": 0.14,
    },
    {
        "Year": 2022,
        "Revenue": 198270,
        "Operating_Income": 83383,
        "Net_Income": 72738,
        "Total_Assets": 364840,
        "Equity": 166542,
        "Debt": 47032,
        "Cash": 104749,
        "Operating_CF": 89035,
        "Capex": 23886,
        "Shares_Outstanding": 7464,
        "Stock_Price": 239.82,
        "Tax_Rate": 0.13,
    },
    {
        "Year": 2023,
        "Revenue": 211915,
        "Operating_Income": 88523,
        "Net_Income": 72361,
        "Total_Assets": 411976,
        "Equity": 206223,
        "Debt": 47237,
        "Cash": 111262,
        "Operating_CF": 87582,
        "Capex": 28107,
        "Shares_Outstanding": 7432,
        "Stock_Price": 340.54,
        "Tax_Rate": 0.19,
    },
    {
        "Year": 2024,
        "Revenue": 245122,
        "Operating_Income": 109433,
        "Net_Income": 88136,
        "Total_Assets": 512163,
        "Equity": 268477,
        "Debt": 51630,
        "Cash": 75543,
        "Operating_CF": 118548,
        "Capex": 44477,
        "Shares_Outstanding": 7433,
        "Stock_Price": 446.95,
        "Tax_Rate": 0.18,
    },
]

df = pd.DataFrame(sample_rows)

# =========================
# Sidebar
# =========================
st.sidebar.header("データ入力")

uploaded_file = st.sidebar.file_uploader(
    "CSVファイルをアップロードしてください",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("CSVファイルを読み込みました。")
else:
    st.sidebar.info("サンプルデータを使用しています。")

# =========================
# Required Columns
# =========================
required_columns = [
    "Year",
    "Revenue",
    "Operating_Income",
    "Net_Income",
    "Total_Assets",
    "Equity",
    "Debt",
    "Cash",
    "Operating_CF",
    "Capex",
    "Shares_Outstanding",
    "Stock_Price",
    "Tax_Rate",
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("以下の列が不足しています。CSVを確認してください。")
    st.write(missing_columns)
    st.stop()

df = df.sort_values("Year").reset_index(drop=True)

for col in required_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df[required_columns].isnull().any().any():
    st.warning("数値に変換できないデータがあります。CSVの中身を確認してください。")

# =========================
# Financial Calculations
# =========================
df["Revenue_Growth"] = df["Revenue"].pct_change()

df["Operating_Margin"] = df["Operating_Income"] / df["Revenue"]
df["Net_Margin"] = df["Net_Income"] / df["Revenue"]

df["Equity_Ratio"] = df["Equity"] / df["Total_Assets"]
df["Debt_to_Equity"] = df["Debt"] / df["Equity"]

df["FCF"] = df["Operating_CF"] - df["Capex"]
df["FCF_Margin"] = df["FCF"] / df["Revenue"]

df["EPS"] = df["Net_Income"] / df["Shares_Outstanding"]
df["BPS"] = df["Equity"] / df["Shares_Outstanding"]

df["PER"] = df["Stock_Price"] / df["EPS"]
df["PBR"] = df["Stock_Price"] / df["BPS"]

df["ROE"] = df["Net_Income"] / df["Equity"]

df["NOPAT"] = df["Operating_Income"] * (1 - df["Tax_Rate"])
df["Invested_Capital"] = df["Debt"] + df["Equity"] - df["Cash"]
df["ROIC"] = df["NOPAT"] / df["Invested_Capital"]

df["Market_Cap"] = df["Stock_Price"] * df["Shares_Outstanding"]
df["Enterprise_Value"] = df["Market_Cap"] + df["Debt"] - df["Cash"]

# =========================
# Display Data
# =========================
st.subheader("1. 財務データ・計算結果")
display_df = df.copy()

float_format_map = {
    "Year": "{:,.0f}",
    "Revenue": "{:,.2f}",
    "Operating_Income": "{:,.2f}",
    "Net_Income": "{:,.2f}",
    "Total_Assets": "{:,.2f}",
    "Equity": "{:,.2f}",
    "Debt": "{:,.2f}",
    "Cash": "{:,.2f}",
    "Operating_CF": "{:,.2f}",
    "Capex": "{:,.2f}",
    "Shares_Outstanding": "{:,.2f}",
    "Stock_Price": "{:,.2f}",
    "Tax_Rate": "{:,.2%}",
    "Revenue_Growth": "{:,.2%}",
    "Operating_Margin": "{:,.2%}",
    "Net_Margin": "{:,.2%}",
    "Equity_Ratio": "{:,.2%}",
    "Debt_to_Equity": "{:,.2f}",
    "FCF": "{:,.2f}",
    "FCF_Margin": "{:,.2%}",
    "EPS": "{:,.2f}",
    "BPS": "{:,.2f}",
    "PER": "{:,.2f}",
    "PBR": "{:,.2f}",
    "ROE": "{:,.2%}",
    "NOPAT": "{:,.2f}",
    "Invested_Capital": "{:,.2f}",
    "ROIC": "{:,.2%}",
    "Market_Cap": "{:,.2f}",
    "Enterprise_Value": "{:,.2f}",
}

st.dataframe(display_df.style.format(float_format_map), width="stretch")

latest = df.iloc[-1]

# =========================
# Latest Summary
# =========================
st.subheader("2. 最新年度サマリー")

col1, col2, col3, col4 = st.columns(4)

col1.metric("売上高", f"{latest['Revenue']:,.2f}")
col2.metric("営業利益率", f"{latest['Operating_Margin']:.2%}")
col3.metric("ROE", f"{latest['ROE']:.2%}")
col4.metric("ROIC", f"{latest['ROIC']:.2%}")

col5, col6, col7, col8 = st.columns(4)

revenue_growth_text = "-" if pd.isna(latest["Revenue_Growth"]) else f"{latest['Revenue_Growth']:.2%}"

col5.metric("売上成長率", revenue_growth_text)
col6.metric("FCF", f"{latest['FCF']:,.2f}")
col7.metric("PER", f"{latest['PER']:,.2f} 倍")
col8.metric("PBR", f"{latest['PBR']:,.2f} 倍")

# =========================
# Charts
# =========================
st.subheader("3. 財務推移グラフ")

chart_option = st.selectbox(
    "表示するグラフを選択してください",
    [
        "売上・利益・FCF",
        "利益率",
        "ROE・ROIC",
        "PER・PBR",
        "キャッシュフロー",
        "企業価値",
    ]
)

fig, ax = plt.subplots(figsize=(10, 5))

if chart_option == "売上・利益・FCF":
    ax.plot(df["Year"], df["Revenue"], marker="o", label="Revenue")
    ax.plot(df["Year"], df["Operating_Income"], marker="o", label="Operating Income")
    ax.plot(df["Year"], df["Net_Income"], marker="o", label="Net Income")
    ax.plot(df["Year"], df["FCF"], marker="o", label="FCF")
    ax.set_ylabel("Amount")

elif chart_option == "利益率":
    ax.plot(df["Year"], df["Operating_Margin"], marker="o", label="Operating Margin")
    ax.plot(df["Year"], df["Net_Margin"], marker="o", label="Net Margin")
    ax.plot(df["Year"], df["FCF_Margin"], marker="o", label="FCF Margin")
    ax.set_ylabel("Ratio")

elif chart_option == "ROE・ROIC":
    ax.plot(df["Year"], df["ROE"], marker="o", label="ROE")
    ax.plot(df["Year"], df["ROIC"], marker="o", label="ROIC")
    ax.set_ylabel("Ratio")

elif chart_option == "PER・PBR":
    ax.plot(df["Year"], df["PER"], marker="o", label="PER")
    ax.plot(df["Year"], df["PBR"], marker="o", label="PBR")
    ax.set_ylabel("Multiple")

elif chart_option == "キャッシュフロー":
    ax.plot(df["Year"], df["Operating_CF"], marker="o", label="Operating CF")
    ax.plot(df["Year"], df["Capex"], marker="o", label="Capex")
    ax.plot(df["Year"], df["FCF"], marker="o", label="FCF")
    ax.set_ylabel("Amount")

elif chart_option == "企業価値":
    ax.plot(df["Year"], df["Market_Cap"], marker="o", label="Market Cap")
    ax.plot(df["Year"], df["Enterprise_Value"], marker="o", label="Enterprise Value")
    ax.set_ylabel("Amount")

ax.set_xlabel("Year")
ax.set_title(chart_option)
ax.legend()
ax.grid(True)

st.pyplot(fig)

# =========================
# DCF
# =========================
st.subheader("4. 簡易DCFモデル")

dcf_col1, dcf_col2, dcf_col3, dcf_col4 = st.columns(4)

base_fcf = dcf_col1.number_input(
    "基準FCF",
    value=float(latest["FCF"]),
    step=100.0,
    format="%.2f"
)

growth_rate = dcf_col2.number_input(
    "FCF成長率",
    value=0.05,
    step=0.01,
    format="%.2f"
)

discount_rate = dcf_col3.number_input(
    "割引率 / WACC",
    value=0.08,
    step=0.01,
    format="%.2f"
)

terminal_growth = dcf_col4.number_input(
    "永続成長率",
    value=0.02,
    step=0.01,
    format="%.2f"
)

projection_years = 5

if discount_rate <= terminal_growth:
    st.error("割引率は永続成長率より大きくする必要があります。")
else:
    dcf_rows = []

    for year in range(1, projection_years + 1):
        future_fcf = base_fcf * (1 + growth_rate) ** year
        present_value = future_fcf / (1 + discount_rate) ** year

        dcf_rows.append({
            "Year": year,
            "Future_FCF": future_fcf,
            "Present_Value": present_value,
        })

    dcf_df = pd.DataFrame(dcf_rows)

    terminal_fcf = base_fcf * (1 + growth_rate) ** projection_years * (1 + terminal_growth)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth)
    terminal_value_pv = terminal_value / (1 + discount_rate) ** projection_years

    enterprise_value_dcf = dcf_df["Present_Value"].sum() + terminal_value_pv
    equity_value_dcf = enterprise_value_dcf - latest["Debt"] + latest["Cash"]
    intrinsic_value_per_share = equity_value_dcf / latest["Shares_Outstanding"]

    result_col1, result_col2, result_col3, result_col4 = st.columns(4)

    result_col1.metric("DCF企業価値", f"{enterprise_value_dcf:,.2f}")
    result_col2.metric("DCF株主価値", f"{equity_value_dcf:,.2f}")
    result_col3.metric("理論株価", f"{intrinsic_value_per_share:,.2f}")
    result_col4.metric("現在株価", f"{latest['Stock_Price']:,.2f}")

    st.write("DCF詳細")

    dcf_display = dcf_df.copy()
    dcf_display["Future_FCF"] = dcf_display["Future_FCF"] / 1000
    dcf_display["Present_Value"] = dcf_display["Present_Value"] / 1000

    dcf_display = dcf_display.rename(columns={
        "Year": "年",
        "Future_FCF": "将来FCF（千単位）",
        "Present_Value": "現在価値（千単位）"
    })

    st.dataframe(
        dcf_display.style.format({
            "年": "{:,.0f}",
            "将来FCF（千単位）": "{:,.2f}",
            "現在価値（千単位）": "{:,.2f}",
        }),
        width="stretch"
    )

# =========================
# Download
# =========================
st.subheader("5. 分析結果ダウンロード")

csv = df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="分析結果CSVをダウンロード",
    data=csv,
    file_name="single_firm_financial_analysis_result.csv",
    mime="text/csv"
)