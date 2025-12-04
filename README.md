# H2O + Weaviate + DVC + Superset (Open Data Demo)

This repository is a **GitHub-ready Docker project** showing an end-to-end, AI-native data stack using:

- **H2O** – for data ingestion and preprocessing
- **Weaviate** – AI-native vector database for semantic search
- **DVC** – data versioning and pipeline reproducibility
- **Apache Superset** – dashboarding and data visualization
- **Open data source** – default: [OpenAQ](https://openaq.org) air-quality measurements (CSV API)

The pipeline:

1. Downloads open data (OpenAQ CSV API by default)
2. Uses **H2O** to load and clean the data
3. Stores cleaned records in **Weaviate** (vector DB)
4. Writes the same cleaned data into **Postgres** for BI
5. Exposes the data via **Superset** dashboards
6. Uses **DVC** to version the data files and the pipeline stage

---

## Architecture Overview

**Services** (from `docker-compose.yml`):

- `weaviate` – vector database with `text2vec-transformers`
- `t2v-transformers` – transformer inference sidecar for Weaviate
- `postgres` – metadata DB for Superset and analytics store for the open data
- `superset` – BI layer and dashboards on top of Postgres
- `h2o_ingestor` – Python + H2O ingestion/preprocessing pipeline

**Data locations**:

- `data/raw/opendata.csv` – raw downloaded data
- `data/processed/opendata_clean.csv` – cleaned data

These outputs are tracked by **DVC** when you initialize it locally.

---

## Project Layout

```text
.
├── docker-compose.yml
├── README.md
├── dvc.yaml
├── .gitignore
├── .dvcignore
├── .env.example
├── data/
│   ├── raw/
│   └── processed/
└── services/
    └── h2o_ingestor/
        ├── Dockerfile
        ├── requirements.txt
        └── ingest.py
```

You can commit this repo to GitHub as-is.

---

## Prerequisites

- Docker & Docker Compose
- (Optional) `dvc` CLI for local data versioning
- (Optional) Python 3.11+ if you want to run the ingestion script outside Docker

---

## Quickstart

### 1. Clone and configure

```bash
git clone https://github.com/your-user/h2o-weaviate-dvc-superset.git
cd h2o-weaviate-dvc-superset

cp .env.example .env   # optional
```

### 2. Start core services

```bash
docker-compose up -d weaviate t2v-transformers postgres superset
```

### 3. Run the ingestion pipeline

```bash
docker-compose run --rm h2o_ingestor
```

The ingestion pipeline will:

1. Download CSV data from `DATA_URL` (OpenAQ by default)
2. Load into an `H2OFrame`
3. Select relevant columns and drop rows with missing values
4. Write `data/raw/opendata.csv` and `data/processed/opendata_clean.csv`
5. Push cleaned rows into Weaviate (`Measurement` class)
6. Load cleaned data into Postgres as table `openaq_measurements`

---

## Superset Usage

Superset runs at <http://localhost:8088>

Default admin credentials (from `docker-compose.yml`):

- username: `admin`
- password: `admin`

In Superset:

1. **Add a Database**:
   - SQLAlchemy URI: `postgresql://superset:superset@superset-db:5432/superset`
2. **Add a Dataset**:
   - Database: `superset`
   - Table: `openaq_measurements`
3. Explore the dataset and build charts/dashboards.

---

## Weaviate Semantic Search

Weaviate stores the `Measurement` class with properties:

- `location`
- `city`
- `country`
- `parameter`
- `value`
- `unit`

You can query via GraphQL, e.g.:

```bash
curl -s -X POST "http://localhost:8080/v1/graphql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{
      Get {
        Measurement(
          nearText: { concepts: [\"PM2.5 pollution\"] }
          limit: 5
        ) {
          location
          city
          country
          parameter
          value
          unit
        }
      }
    }"
  }'
```

This uses Weaviate's `nearText` operator to find semantically similar items.

---

## DVC Integration

The `dvc.yaml` defines one stage: `ingest`.

```yaml
stages:
  ingest:
    cmd: python services/h2o_ingestor/ingest.py
    deps:
      - services/h2o_ingestor/ingest.py
    outs:
      - data/raw/opendata.csv
      - data/processed/opendata_clean.csv
```

To enable DVC locally:

```bash
dvc init
dvc repro                    # run the pipeline stage
dvc add data/raw/opendata.csv data/processed/opendata_clean.csv
git add dvc.yaml data/*.dvc .dvc .gitignore .dvcignore
git commit -m "Add DVC pipeline"
```

You can then configure a remote (S3, GCS, etc.) and use `dvc push` / `dvc pull` to share data.

---

## Customising the Open Data Source

Default data source: OpenAQ CSV API

```text
https://api.openaq.org/v2/measurements?limit=1000&format=csv
```

Change it using the `DATA_URL` environment variable (in `.env` or `docker-compose.yml`). For a different CSV:

1. Make sure `pandas.read_csv(DATA_URL)` works.
2. Adjust the columns used in `process_with_h2o()` if necessary.

---

## H2O in the Pipeline

H2O is used here to:

- Start a local cluster in the ingestion container
- Convert a pandas DataFrame into an `H2OFrame`
- Perform basic selection and filtering
- Convert back to pandas for export

You can extend this to:

- AutoML training (`H2OAutoML`)
- Advanced transformations and feature engineering
- Scoring/prediction and pushing those into Weaviate/Postgres

---

## One-shot Demo Run

For a simple demo:

```bash
docker-compose up --build
```

Once all services are up, run the ingestor in another terminal:

```bash
docker-compose run --rm h2o_ingestor
```

---

## Production Notes

For real-world use:

- Set a strong `SUPERSET_SECRET_KEY`
- Restrict anonymous access to Weaviate
- Put Postgres and Weaviate behind proper networking and security
- Add monitoring/logging
- Add CI/CD (GitHub Actions) that runs `dvc repro` and tests on PRs

---

## License

Pick a license (MIT/Apache 2.0/etc.) and add a `LICENSE` file if open-sourcing.
