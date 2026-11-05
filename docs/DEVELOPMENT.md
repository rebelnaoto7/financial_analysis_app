# 開発者向けメモ（financial_analysis_app）

[README](../README.md) を補足する、開発者向けの情報です。

## Streamlit 版（app.py）との対応

Django 版は、リポジトリ直下の `app.py`（Streamlit 版）のロジックを関数ごと `analyzer/services/finance.py` に移し、画面を Django テンプレートに置き換えたものです。

| Streamlit 版（`app.py`） | Django 版 | 役割 |
| --- | --- | --- |
| `resolve_ticker`・`translate_item`・`find_row`・`get_latest_value`・`get_series`・`format_number`・`format_percent` | `finance.py` の同じ名前の関数 | ティッカーの解決、項目名の翻訳、値の取り出しと整形 |
| `statement_to_display` | `statement_to_table` | 財務諸表を表示用の表（列と行）に変換 |
| `build_trend_df` | `build_trend` | 年次トレンド（グラフ用の数値と表示用の文字列）を作成 |
| `fetch_data`（`@st.cache_data` 付き） | `fetch_data`（キャッシュなし） | yfinance でデータを取得 |
| 画面のスクリプト本体 | `analyze()` と `analyzer/views.py` の `index` | 指標の計算とテンプレートへの受け渡し |
| `st.text_input` と `st.button` | `analyzer/forms.py` の `TickerForm`（GET） | 入力フォーム |
| `st.metric`・`st.dataframe` | `analyzer/templates/analyzer/index.html` | 画面の描画 |
| `st.line_chart` | Chart.js 4.4.1（`analyzer/static/analyzer/js/chart.umd.min.js` を同梱） | 折れ線グラフ |
| `st.tabs`（年次・四半期、三表） | HTML と素の JavaScript のタブ | タブの切り替え |
| `st.error` | `AnalysisError` のメッセージを画面に表示 | エラー表示 |

## 処理の流れ

1. `analyzer/views.py` の `index` が `GET /?query=...` を受け取り、`TickerForm` で入力を検証します（必須、100 文字以内）。
2. `resolve_ticker` で入力をティッカーに変換し、「変換後のティッカー」として表示します。
3. `analyze()` が `fetch_data()` で yfinance の `Ticker` から会社情報（`info`）と、年次・四半期の損益計算書・貸借対照表・キャッシュフロー計算書を取得します。
4. 年次の三表がすべて空ならエラーにします。そうでなければ、最新値・収益性指標・トレンド・表示用の表を作って辞書で返します。
5. テンプレートは指標と表を描画し、トレンドのデータを `json_script` で埋め込みます。ページ内の JavaScript がそれを読み込み、Chart.js でグラフを描きます。

## 指標の定義

年次データから、次の行（yfinance の項目名）を左から順に探し、最初に見つかった行を使います。英字の大文字・小文字の違いは無視します。

| 指標 | 使う行 |
| --- | --- |
| 売上高 | `Total Revenue`、`Revenue`、`Operating Revenue` |
| 営業利益 | `Operating Income` |
| 純利益 | `Net Income`、`Net Income Common Stockholders` |
| 総資産 | `Total Assets` |
| 自己資本 | `Stockholders Equity`、`Common Stock Equity`、`Total Equity Gross Minority Interest` |
| 営業CF | `Operating Cash Flow`、`Cash Flow From Continuing Operating Activities` |

- 最新値は、行ごとに値がある最も新しい決算期の値です。行によって欠損の年が違う場合、指標ごとに決算期がずれることがあります。
- 営業利益率 ＝ 営業利益 ÷ 売上高、純利益率 ＝ 純利益 ÷ 売上高、ROE ＝ 純利益 ÷ 自己資本（期末）です。分母が 0 か値がない場合は「N/A」です。
- トレンドのラベルは決算期末日の西暦年（`strftime("%Y")`）です。

## エラーの扱い

| 状況 | 画面のメッセージ |
| --- | --- |
| 未入力・空白のみ | 企業名・株式コード・ティッカーを入力してください。 |
| yfinance を読み込めない（`ModuleNotFoundError`） | yfinance がインストールされていません。`pip install yfinance` を実行してください。 |
| 取得中のその他の例外（通信エラーなど） | データ取得中にエラーが発生しました: （例外のメッセージ） |
| 年次の三表がすべて空（存在しないティッカーなど） | 財務データを取得できませんでした。ティッカーが正しいか確認してください。 |

- `info` の取得に失敗した場合は空の辞書として続行し、会社名はティッカー、通貨・セクター・業種は「N/A」になります。
- yfinance の依存パッケージが足りない場合も `ModuleNotFoundError` になるため、「yfinance がインストールされていません」と表示されます。

## 既知の不具合の該当箇所

| 内容 | 場所 |
| --- | --- |
| 小数の値（EPS・税率など）が整数に丸められる | `finance.py` の `format_number`（`{:,.0f}` で整形） |
| 全角数字の株式コードが `７２０３.T` に変換される | `finance.py` の `resolve_ticker`（`str.isdigit()` は全角数字も真になる） |
| 使われていない変数 `trend_json` | `analyzer/views.py` の `index`（テンプレートは `json_script` を使用） |

## 動作確認の手順

自動テストはまだないため、変更したときは次の手順で確認します。

```powershell
python manage.py check
python -c "from analyzer.services.finance import resolve_ticker as r; print(r('トヨタ'), r('7203'), r('aapl'))"
python manage.py runserver
```

2 行目はネットワークを使わずにティッカーの解決を確認するコマンドで、`7203.T 7203.T AAPL` と表示されれば正常です。サーバーを起動したら、次の URL を開いて結果を確認します。

- <http://127.0.0.1:8000/?query=トヨタ>：トヨタ自動車（7203.T）の指標・グラフ・財務三表が表示される
- <http://127.0.0.1:8000/?query=AAPL>：Apple Inc. の結果が表示される
- <http://127.0.0.1:8000/?query=ZZZZZZZZ>：「財務データを取得できませんでした。…」と表示される
- <http://127.0.0.1:8000/?query=>：「企業名・株式コード・ティッカーを入力してください。」と表示される
