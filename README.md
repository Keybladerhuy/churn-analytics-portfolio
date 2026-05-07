# Customer Retention Analytics Dashboard

**[English](#english) · [日本語](#japanese)**

---

<a name="english"></a>
## English

### What problem this solves

Subscription and e-commerce businesses accumulate customer data but rarely have a clear view of **who is about to leave, why, and what to do about it**. This project takes a standard customer transaction export and delivers:

- A **live Streamlit dashboard** with four pages of retention insights
- A **prioritised action list** of at-risk customers with plain-English recommended actions
- A **revenue at risk summary** suitable for executive reporting
- Transparent, auditable SQL logic — every scoring rule is readable

No machine learning. No black box. A non-technical client can read every reason a customer was flagged.

---

### How the scoring logic works

Risk is assigned using a three-tier `CASE WHEN` rule in `sql/03_customer_scoring.sql`:

```sql
-- HIGH RISK (score 3): all three warning signals present
WHEN Contract = 'Month-to-month'
     AND tenure < 12
     AND TechSupport = 'No'
THEN 'High'

-- MEDIUM RISK (score 2): at least one major warning signal
WHEN Contract = 'Month-to-month'
     OR tenure < 6
THEN 'Medium'

-- LOW RISK (score 1): stable customers
ELSE 'Low'
```

These thresholds were derived from `sql/02_churn_drivers.sql`, which shows that:
- Month-to-month customers churn at **42.7%** vs 11.3% for two-year contracts
- Customers in their first 6 months churn at **52.9%**
- Customers without tech support churn at **41.6%**

A client can adjust any threshold (e.g. change `12` to `18` months) and re-run in minutes.

---

### What a client needs to provide

A CSV export or BigQuery table with at minimum these columns:

| Column | Type | Example | Notes |
|---|---|---|---|
| `customerID` | String | `7590-VHVEG` | Unique per customer |
| `Contract` | String | `Month-to-month` | `Month-to-month` / `One year` / `Two year` |
| `tenure` | Integer | `1` | Months as a customer |
| `MonthlyCharges` | Float | `29.85` | Current monthly bill |
| `TechSupport` | String | `No` | `Yes` / `No` / `No internet service` |
| `Churn` | String | `Yes` | `Yes` / `No` — needed for churn rate calculation |

Optional columns used for additional analysis: `InternetService`, `PaymentMethod`.

---

### What the client gets

1. **Dashboard URL** — a Streamlit Cloud link they can open in any browser, no installation
2. **Priority list CSV** — exportable from the dashboard, ready to load into CRM / Salesforce
3. **Revenue at risk summary** — monthly and annual figures by tier, with ROI calculator
4. **The SQL files** — four readable query files they can run in BigQuery against their live data

---

### How to run locally

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd customer-retention-analytics

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run app.py
```

The dataset (`data/telco_customer_churn.csv`) is included in the repo.
The dashboard opens at `http://localhost:8501`.

---

### How to deploy to Streamlit Cloud

1. Fork or push this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. Click **Deploy** — the public URL is ready in ~60 seconds

No secrets or environment variables are required for the demo deployment.

---

### BigQuery migration path

When a client has their data in BigQuery, swap the data source in three steps:

1. **Install the BigQuery client**: `pip install google-cloud-bigquery db-dtypes`
2. **Set credentials**: export `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json`
3. **Replace the table reference** in each SQL file: change `telco` to `` `project.dataset.table` ``
4. **Swap the loader**: in `src/data_loader.py`, uncomment the BigQuery stub at the bottom and replace the call to `get_connection()` with `get_bq_client()`

The SQL files need **no other changes** — they are written in BigQuery Standard SQL dialect. The only local shim is the `SAFE_DIVIDE` macro, which is a built-in function in BigQuery.

---

### Dataset

IBM Telco Customer Churn dataset. Originally from IBM Watson Analytics sample data. Widely used in academic and commercial churn analysis examples.

- Source: [Kaggle — IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- 7,043 customer records, 21 columns
- No personally identifiable information

---
---

<a name="japanese"></a>
## 日本語

# 顧客離脱リスク分析ダッシュボード

### このツールが解決する課題

サブスクリプションやEC事業では、顧客データは蓄積されていても、「**誰が解約しそうか・なぜか・何をすべきか**」が見えていないケースがほとんどです。このプロジェクトは、標準的な顧客データCSVを受け取り、以下を提供します：

- すぐに共有できる**Streamlitダッシュボード**（URLを送るだけでブラウザで閲覧可能）
- **優先対応リスト**：リスクの高い顧客と具体的なアクション提案
- **経営層向けの売上リスクサマリー**
- **透明性のあるロジック**：すべてのスコアリングルールが読めるSQL

機械学習なし。ブラックボックスなし。なぜその顧客がフラグを立てられたか、非技術者でも説明できます。

---

### スコアリングロジックについて（透明性のあるルール）

リスクは `sql/03_customer_scoring.sql` に記述された、読みやすいSQLルールで決まります：

```sql
-- 高リスク（スコア3）：3つの警告条件がすべて揃っている
WHEN Contract = 'Month-to-month'
     AND tenure < 12
     AND TechSupport = 'No'
THEN '高リスク'

-- 中リスク（スコア2）：主要な警告が1つ以上ある
WHEN Contract = 'Month-to-month'
     OR tenure < 6
THEN '中リスク'

-- 低リスク（スコア1）：安定した顧客
ELSE '低リスク'
```

このしきい値は実際のデータから導き出されています：
- 月次契約の顧客は **42.7%** が解約（2年契約は 11.3%）
- 利用開始から6ヶ月以内の顧客は **52.9%** が解約
- テクニカルサポートなし顧客の解約率は **41.6%**

しきい値（例：「12ヶ月」→「18ヶ月」）は1行書き換えるだけで調整可能です。

---

### クライアント側で必要なもの

以下の列を含むCSVまたはBigQueryテーブル：

| 列名 | 型 | 例 |
|---|---|---|
| `customerID` | 文字列 | `7590-VHVEG` |
| `Contract` | 文字列 | `Month-to-month` |
| `tenure` | 整数 | `1`（月数） |
| `MonthlyCharges` | 小数 | `29.85` |
| `TechSupport` | 文字列 | `No` |
| `Churn` | 文字列 | `Yes` / `No` |

---

### クライアントが受け取るもの

1. **ダッシュボードURL** — ブラウザで即閲覧。インストール不要
2. **優先対応リストCSV** — CRM・Salesforceに直接インポート可能
3. **売上リスクサマリー** — 月次・年次、ROI計算機付き
4. **SQLファイル一式** — BigQueryに接続すればリアルタイム分析が可能

---

### 3つの強み

| | 説明 |
|---|---|
| **透明性のあるロジック** | スコアリングはSQLのCASE文。誰でも読める、誰でも確認できる |
| **すぐに使える優先リスト** | 「誰に・何をすすめるか」がリスト形式で即出力 |
| **専門知識不要** | データサイエンスの知識なしで導入・運用可能 |

---

### ローカル実行方法

```bash
git clone <your-repo-url>
cd customer-retention-analytics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

`http://localhost:8501` でダッシュボードが起動します。

---

### Streamlit Cloudへのデプロイ

1. このリポジトリをGitHubにpush
2. [share.streamlit.io](https://share.streamlit.io) にアクセスしてサインイン
3. **New app** → リポジトリを選択 → **Main file path** に `app.py` を指定
4. **Deploy** をクリック → 約60秒で公開URLが発行される

設定ファイルや環境変数は不要です。

---

### BigQueryへの接続（実際のクライアントデータとの連携）

クライアントのデータがBigQueryにある場合、以下の4ステップで切り替えできます：

1. `pip install google-cloud-bigquery db-dtypes`
2. サービスアカウントJSONを `GOOGLE_APPLICATION_CREDENTIALS` に設定
3. SQLファイル内の `telco` をクライアントのBigQueryテーブル名に置換
4. `src/data_loader.py` のBigQueryスタブをアンコメント

SQLファイルの変更はテーブル名のみです。ロジックは一切変更不要です。
