# Customer Retention Analytics Dashboard

**[English](#english) · [日本語](#japanese)**

---

<a name="english"></a>
## English

A portfolio project demonstrating how to turn raw customer data into a structured analytical story — from identifying who is about to leave, to understanding why, to building a budgetable retention plan.

Built to show the approach I take on real client engagements. The IBM Telco Churn dataset stands in for client data; the pipeline, SQL logic, and dashboard structure are designed to be adapted to any subscription or recurring-revenue business.

---

### The narrative arc

The dashboard is six pages, each with a defined role in the story:

| Page | Question it answers |
|------|---------------------|
| **About the Data** | What are we working with? What does "churn" mean here? |
| **Executive Summary** | How big is the problem — in customers and in dollars? |
| **Churn Drivers** | Why are customers leaving? Which traits predict it? |
| **Retention Priority List** | Who do we contact first, and what do we offer them? |
| **Revenue at Risk** | What does inaction cost, broken down by risk group? |
| **ROI Calculator** | Does a retention program pay for itself? |

Each page feeds into the next. A client can follow the story without any data background.

---

### Why rule-based SQL, not machine learning

Risk is assigned using a three-tier `CASE WHEN` rule in `sql/03_customer_scoring.sql`:

```sql
-- HIGH RISK: all three warning signals present simultaneously
WHEN Contract = 'Month-to-month'
     AND tenure < 12
     AND TechSupport = 'No'
THEN 'High'

-- MEDIUM RISK: at least one major warning signal present
WHEN Contract = 'Month-to-month'
     OR tenure < 6
THEN 'Medium'

-- LOW RISK: stable customers
ELSE 'Low'
```

These thresholds were derived from `sql/02_churn_drivers.sql`, which shows that:
- Month-to-month customers churn at **42.7%** vs 2.8% for two-year contracts
- Customers in their first 6 months churn at **47%+**
- Customers without tech support churn at **41.6%** — nearly 3× those who have it

A client can read every rule, challenge every threshold, and adjust any number in minutes. No model to explain. No black box to trust.

---

### What a client needs to provide

A CSV export or BigQuery table with at minimum these columns:

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `customerID` | String | `7590-VHVEG` | Unique per customer |
| `Contract` | String | `Month-to-month` | `Month-to-month` / `One year` / `Two year` |
| `tenure` | Integer | `1` | Months as a customer |
| `MonthlyCharges` | Float | `29.85` | Current monthly bill |
| `TechSupport` | String | `No` | `Yes` / `No` / `No internet service` |
| `Churn` | String | `Yes` | `Yes` / `No` — used to calibrate the loss estimate |

Optional columns used for additional driver analysis: `InternetService`, `PaymentMethod`.

---

### What the client gets

1. **Dashboard URL** — a Streamlit Cloud link, viewable in any browser with no installation
2. **Retention Priority List CSV** — exportable directly from the dashboard, ready to load into a CRM
3. **Revenue at Risk figures** — estimated annual loss by risk group, suitable for a budget conversation
4. **ROI Calculator** — model program cost vs. revenue recovered before committing to a spend
5. **The SQL files** — five readable query files runnable directly in BigQuery against live data

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

When a client has their data in BigQuery, swap the data source in four steps:

1. **Install the BigQuery client**: `pip install google-cloud-bigquery db-dtypes`
2. **Set credentials**: export `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json`
3. **Replace the table reference** in each SQL file: change `telco` to `` `project.dataset.table` ``
4. **Swap the loader**: in `src/data_loader.py`, uncomment the BigQuery stub at the bottom

The SQL files need **no other changes** — they are written in BigQuery Standard SQL dialect. The only local compatibility shim is the `SAFE_DIVIDE` macro, which is a native function in BigQuery.

---

### Dataset

IBM Telco Customer Churn dataset. Originally from IBM Watson Analytics sample data. Widely used in academic and commercial churn analysis examples.

- Source: [Kaggle — IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- 7,043 customer records · 21 columns · no personally identifiable information

---
---

<a name="japanese"></a>
## 日本語

「誰が解約しそうか」から「なぜか」「誰に何をすべきか」「いくらかかるか」まで、顧客データをひとつの一貫したストーリーとして提示するポートフォリオプロジェクトです。

実際のクライアント案件で取るアプローチをベースに構築しています。デモデータにはIBM Telco Churnデータセットを使用していますが、パイプライン・SQLロジック・ダッシュボード構成はサブスクリプション型や継続課金型のビジネス全般に適用可能です。

---

### 分析のストーリー構成

ダッシュボードは6ページで構成されており、各ページに明確な役割があります：

| ページ | 答える問い |
|--------|-----------|
| **データについて** | どのようなデータを使っているか？「解約」とは何か？ |
| **エグゼクティブサマリー** | 問題の規模は？顧客数と金額で把握する |
| **解約要因の分析** | なぜ顧客が離脱するのか？予測に使える特徴は？ |
| **優先対応リスト** | 誰に・何をすすめるか、優先順位付きで提示 |
| **売上リスクの定量化** | 何もしなければいくら失うか、リスク層別に算出 |
| **ROI計算機** | 施策に投資する価値はあるか？コストと回収額を比較 |

各ページは次のページへとつながっており、データの知識がないクライアントでもストーリーとして追えるよう設計されています。

---

### なぜ機械学習ではなくルールベースSQLなのか

リスクは `sql/03_customer_scoring.sql` に記述された、読みやすいSQLルールで決まります：

```sql
-- 高リスク：3つの警告条件がすべて揃っている
WHEN Contract = 'Month-to-month'
     AND tenure < 12
     AND TechSupport = 'No'
THEN '高リスク'

-- 中リスク：主要な警告が1つ以上ある
WHEN Contract = 'Month-to-month'
     OR tenure < 6
THEN '中リスク'

-- 低リスク：安定した顧客
ELSE '低リスク'
```

このしきい値は `sql/02_churn_drivers.sql` の実データ分析から導き出されています：
- 月次契約の顧客は **42.7%** が解約（2年契約は 2.8%）
- 利用開始から6ヶ月以内の顧客は **47%以上** が解約
- テクニカルサポートなし顧客の解約率は **41.6%** — サポートあり顧客の約3倍

すべてのルールをクライアントが読め、しきい値は数分で変更可能です。説明できないモデル、信頼するしかないブラックボックスは一切ありません。

---

### クライアント側で必要なもの

以下の列を含むCSVまたはBigQueryテーブル：

| 列名 | 型 | 例 | 備考 |
|------|----|----|------|
| `customerID` | 文字列 | `7590-VHVEG` | 顧客ごとの一意ID |
| `Contract` | 文字列 | `Month-to-month` | `Month-to-month` / `One year` / `Two year` |
| `tenure` | 整数 | `1` | 利用継続月数 |
| `MonthlyCharges` | 小数 | `29.85` | 月額料金 |
| `TechSupport` | 文字列 | `No` | `Yes` / `No` / `No internet service` |
| `Churn` | 文字列 | `Yes` | `Yes` / `No` — 損失額の推計に使用 |

追加分析に使用するオプション列：`InternetService`、`PaymentMethod`

---

### クライアントが受け取るもの

1. **ダッシュボードURL** — ブラウザで即閲覧。インストール不要
2. **優先対応リストCSV** — ダッシュボードから直接エクスポート、CRMへのインポートに対応
3. **売上リスク試算** — リスク層別の年間損失推計。経営層への説明資料として活用可能
4. **ROI計算機** — 施策コストと回収見込みを比較してから予算を確定できる
5. **SQLファイル一式** — BigQueryに接続すればリアルタイムデータで即実行可能な5つのクエリ

---

### ローカルでの実行方法

```bash
git clone <your-repo-url>
cd customer-retention-analytics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

データセット（`data/telco_customer_churn.csv`）はリポジトリに含まれています。`http://localhost:8501` でダッシュボードが起動します。

---

### Streamlit Cloudへのデプロイ

1. このリポジトリをGitHubにpush
2. [share.streamlit.io](https://share.streamlit.io) にアクセスしてサインイン
3. **New app** → リポジトリを選択 → **Main file path** に `app.py` を指定
4. **Deploy** をクリック → 約60秒で公開URLが発行される

設定ファイルや環境変数は不要です。

---

### BigQueryへの接続

クライアントのデータがBigQueryにある場合、4ステップで切り替えできます：

1. `pip install google-cloud-bigquery db-dtypes`
2. サービスアカウントJSONを `GOOGLE_APPLICATION_CREDENTIALS` に設定
3. 各SQLファイル内の `telco` をクライアントのBigQueryテーブル名（`` `project.dataset.table` ``）に変更
4. `src/data_loader.py` のBigQueryスタブをアンコメント

SQLファイルのロジックは一切変更不要です。テーブル名のみの変更で動作します。

---

### データセット

IBM Telco Customer Churnデータセット。IBM Watson Analyticsサンプルデータが出典。

- 出典：[Kaggle — IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- 7,043件の顧客レコード · 21列 · 個人情報なし
