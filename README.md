# 📊 財務分析アプリ（Django版）

企業名・ティッカー・株式コードから財務データを取得し、主要KPI・収益性・トレンド・財務三表を可視化する分析アプリ。
**Streamlit版 `app.py` を Django に移植したもの。**

---

## 1. Streamlit版との対応関係

| Streamlit版 (`app.py`)          | Django版                                   | 役割 |
|---------------------------------|--------------------------------------------|------|
| `resolve_ticker` / `translate_item` / `find_row` / `get_*` / `format_*` / `statement_to_display` / `build_trend_df` / `fetch_data` | `analyzer/services/finance.py` | 純粋ロジック（**ほぼそのまま移植**） |
| `st.text_input` + `st.button`   | `analyzer/forms.py`（`TickerForm`）          | 入力フォーム |
| スクリプト全体の再実行           | `analyzer/views.py`（`index`）              | リクエスト処理 |
| `st.metric` / `st.dataframe`    | `analyzer/templates/analyzer/index.html`    | 画面描画 |
| `st.line_chart`                 | **Chart.js**（CDN）                          | 折れ線グラフ |
| `st.tabs`（年次/四半期, PL/BS/CF）| HTML + 素のJSタブ                           | タブ切替 |
| `@st.cache_data`                | （未実装：拡張ポイント参照）                  | キャッシュ |

ロジック層（`finance.py`）は Django 非依存の純関数なので、単体テストや再利用が容易。

---

## 2. ディレクトリ構成

```
financial_analysis/
├── manage.py
├── requirements.txt
├── config/                 # プロジェクト設定
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
├── analyzer/               # 財務分析アプリ
│   ├── forms.py            # 入力フォーム
│   ├── views.py            # ビュー（1画面）
│   ├── urls.py             # ルーティング (app_name='analyzer')
│   ├── services/
│   │   └── finance.py      # ★ app.py から移植したロジック本体
│   └── templates/analyzer/
│       └── index.html      # 画面（Chart.js + タブ）
```

---

## 3. セットアップ手順

```powershell
# 1. 仮想環境（任意）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. 依存インストール
pip install -r requirements.txt

# 3. 起動（このアプリはDB不要。マイグレーションは任意）
python manage.py runserver
```

ブラウザで `http://127.0.0.1:8000/` を開く。
入力例：`Apple` / `AAPL` / `トヨタ` / `7203` / `ソーファイ` / `SOFI`

> **Windows + Django の注意**：`TIME_ZONE = "Asia/Tokyo"` を使うため `tzdata` が必要。
> `requirements.txt` に Windows 限定で含めてある。

---

## 4. 設計上のポイント

- **DBレス**：yfinance から都度取得するだけなので、永続化モデルは持たない（`models.py` は空）。
- **入力 → 結果が1画面**：StreamlitのUXに合わせ、`GET ?query=...` で同一ページに結果を表示。URLで結果を共有・リロードできる利点もある。
- **グラフは Chart.js**：`st.line_chart` の代替。トレンドデータを `json_script` で安全にテンプレートへ渡し、JS側でパースして描画。
- **エラー処理**：ティッカー未入力・データ取得失敗・yfinance未インストールを `AnalysisError` に集約し、画面上に日本語で表示。

---

## 5. 動作検証（移植時に実施済み）

- `manage.py check`：問題なし
- ロジック単体テスト：`resolve_ticker` / `build_trend`（ROE等の計算）/ `statement_to_table` / フォーマッタ／エラーハンドリングを確認
- ビュー+テンプレートのE2E（ダミーデータ）：HTTP 200、会社名・KPI・グラフcanvas・財務三表・トレンド表が描画されることを確認

---

## 6. 今後の拡張ポイント

- **キャッシュ**：`@st.cache_data` 相当。Djangoの `cache.get_or_set(ticker, ...)`（LocMem/Redis）で同一ティッカーの再取得を抑制。
- **入力候補**：`COMPANY_ALIASES` を使ったオートコンプリート（JS）。
- **公開時**：`DEBUG=False`、`SECRET_KEY` を環境変数化、`ALLOWED_HOSTS` 設定、`collectstatic`。
- **ウォッチリスト**：ログイン＋お気に入り銘柄を保存する場合に `models.py` を活用。
