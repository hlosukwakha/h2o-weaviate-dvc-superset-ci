
# 🚀 H2O + Weaviate + DVC + Superset  

# 🏷️ **4. Technology Stack**

![H2O.ai](https://img.shields.io/badge/H2O.ai-ML%20Engine-yellow?logo=h2o.ai&logoColor=black)
![Weaviate](https://img.shields.io/badge/Weaviate-Vector%20Database-blue?logo=weaviate&logoColor=white)
![DVC](https://img.shields.io/badge/DVC-Data%20Versioning-purple?logo=dvc&logoColor=white)
![Apache Superset](https://img.shields.io/badge/Superset-Data%20Visualization-00A9E0?logo=apache%20superset&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Postgres-Database-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?logo=docker&logoColor=white)
![Nebius](https://img.shields.io/badge/Nebius-AI%20Cloud-orange?logo=icloud&logoColor=white)

---
## **A Nebius‑Optimized, GPU‑Accelerated Data Preparation & Analytics Pipeline**  
### **Full PoC Implementation — Built for Nebius Cloud**

---

## 📘 **1. Introduction — Why This Project Exists**

Modern data pipelines increasingly require **scalable machine learning ingestion**, **vector‑native storage**, **repeatable versioning**, and **real‑time visualization**. This Proof‑of‑Concept (PoC) demonstrates how these capabilities can be unified into a single workflow optimized for **Nebius AI Cloud** — a cloud platform engineered for **GPU‑accelerated data processing**, **high‑throughput object storage**, and **cost‑efficient AI workloads**.

This project integrates:

- **H2O** → Fast ML preprocessing  
- **Weaviate (AI‑Native Vector Database)** → Semantic search & embeddings  
- **DVC** → Dataset versioning & reproducibility  
- **Apache Superset** → Enterprise‑grade dashboards  
- **Postgres** → Persistent analytical storage  

By combining these technologies, we demonstrate how Nebius Cloud’s **GPU compute**, **high‑performance object storage**, and **AI‑native infrastructure** significantly accelerate data preparation workflows.

---

# ✨ **2. Why Nebius Cloud? (Strong Positioning)**

Nebius Cloud provides a fully AI‑ready environment, particularly suited for:

### 🔥 **GPU‑accelerated data preparation**  
H2O and vector embedding models run **significantly faster** on Nebius GPU compute instances, enabling:

- Rapid H2OFrame transformations  
- High‑throughput vectorization in Weaviate  
- Large‑scale semantic search workloads  

---

### ☁️ **High-performance Object Storage**  
Nebius Object Storage serves perfectly as:

- A central location for **DVC remote storage**  
- A durable store for raw and intermediate datasets  
- A scalable backend for ML workflows  

---

### 🧠 **AI‑native infrastructure & compatibility**  

Using Nebius AI Cloud, the entire stack can run:

- **As microservices on Nebius Kubernetes**
- **In containerized GPU‑accelerated apps**
- **Integrated with Nebius VMs & observability tools**

This PoC highlights how enterprises can quickly experiment with an **AI‑augmented data pipeline** and later scale it across Nebius GPU and CPU nodes.

---

# 🧱 **3. Technology Stack Overview**

Below is a breakdown of each component and its role.

---

## **3.1 H2O — Machine Learning Preprocessing Engine**

H2O provides:

- Distributed data processing  
- Automatic ML transforms  
- Efficient missing‑value handling  
- H2OFrames for scalable ML workflows  

On Nebius GPU instances, H2O pipelines can process datasets **orders of magnitude faster**.

Used in this project for:

- Converting CSV/GZ data into structured frames  
- Cleaning, filtering & transforming datasets  
- Preparing inputs for Weaviate and Postgres  

If H2O is unavailable, the pipeline gracefully falls back to **pandas**.

---

## **3.2 Weaviate — AI‑Native Vector Database**

Weaviate enables:

- Real‑time vector search  
- Semantic similarity  
- Large‑scale embeddings  
- Storing ML‑enriched documents  

The project uses:

- `text2vec-transformers` → Transformer-based vectorization  
- Weaviate Collections API (v4)  
- Bulk ingestion with automatic embedding generation  

Running Weaviate on Nebius Cloud with GPU inference makes vector embedding extremely fast.

---

## **3.3 DVC — Data Version Control**

DVC ensures:

- Reproducible datasets  
- Versioned ML preprocessing  
- Hash‑based data lineage  
- Cloud‑stored raw/processed data  

DVC integrates nicely with:

- Nebius Object Storage as a remote  
- CI/CD pipelines (via GitHub Actions)

---

## **3.4 Apache Superset — Modern Data Visualization**

Superset provides:

- Dashboards  
- SQL Lab exploration  
- Visual charts and graphs  
- Authentication & RBAC  

Postgres acts as the analytical backend for Superset.

---

## **3.5 Postgres — Analytical Storage Layer**

Stores:

- Cleaned dataset from H2O/pandas  
- Tables exposed directly to Superset  

---

# 📦 **5. Clone the Project**

```bash
git clone https://github.com/hlosukwakha/h2o-weaviate-dvc-superset-ci.git
cd h2o-weaviate-dvc-superset-ci
```

---

# 🌲 **6. Project Tree**

```
h2o-weaviate-dvc-superset/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── dvc.yaml
├── ingest.py
├── docker-compose.yml
│
├── services/
│   └── h2o_ingestor/
│       ├── Dockerfile
│       └── ingest.py
│
├── superset/
│   ├── Dockerfile
│   └── superset_config.py
│
└── README.md
```

---

# 🌍 **7. Data Source**

This PoC uses OpenAQ public datasets:

Example dataset:

```
https://openaq-data-archive.s3.amazonaws.com/records/csv.gz/locationid=2178/year=2022/month=05/location-2178-20220503.csv.gz
```

The ingestor can be extended to support multiple datasets.

---

# ➕ **8. Adding a Second Ingestor**

1. Create new folder:

```
services/new_ingestor/
```

2. Add Dockerfile + script:

```
Dockerfile
second_ingest.py
```

3. Register service inside `docker-compose.yml`:

```yaml
new_ingestor:
  build: ./services/new_ingestor
  depends_on:
    - postgres
    - weaviate
  environment:
    DATA_URL: <second-dataset-url>
    DATASET_NAME: dataset2
```

4. Update DVC:

```bash
dvc add data/processed/new_dataset.csv
```

---

# ▶️ **9. How to Start & Run**

### 1. Build and start entire stack:

```bash
docker-compose up --build -d
```

### 2. Run the ingestion pipeline manually:

```bash
docker-compose logs -f h2o_ingestor
```

### 3. Access Superset:

```
http://localhost:8088
```

---

# 🛠️ **10. Issues & Troubleshooting (Table Format)**

| Issue | Explanation | Fix | Sanity Check Commands |
|-------|-------------|-----|------------------------|
| **1. Superset user (admin) not found** | Superset CLI user creation failed or did not run | Re-run admin creation command | `docker-compose exec superset superset fab list-users` |
| | | | Create user: `docker-compose exec superset superset fab create-admin --username admin --password admin --firstname Admin --lastname User --email admin@example.com` |
| **2. Database table is not being created** | Ingestor crashes before Postgres stage; SKIP flags misconfigured | Ensure `SKIP_POSTGRES=false` and wrap Weaviate ingestion in `try/except` | `docker-compose exec postgres psql -U superset -d superset -c "\dt"` |
| **3. Superset database connection errors** | Missing Postgres driver (`psycopg2-binary`) | Use custom Superset image with dependencies installed | Inside container: `python -c "import psycopg2"` |
| **4. Refusing to start due to insecure SECRET_KEY** | Superset refuses default insecure keys | Create custom `superset_config.py` | Check inside container: `cat /app/superset_config.py` |
| | | Generate secure key: `openssl rand -base64 42` | |
| **5. service "superset" refers to undefined volume** | Bind mount missing or misconfigured | Add volume definitions under `volumes:` | `docker-compose config` |
| **6. ModuleNotFoundError: flask_cors** | Python dependencies installed in wrong venv | Install via `EXTRA_PIP_REQUIREMENTS` or custom Dockerfile | `docker-compose exec superset python -c "import flask_cors"` |
| **7. GET Weaviate schema 403** | Raft not initialized; vectorizer not ready | Increase wait time; add single-node Raft config | `curl http://localhost:8080/v1/schema` |
| **8. leader not found (Raft)** | Single-node cluster needs explicit bootstrap | Add `RAFT_BOOTSTRAP_EXPECT=1` etc. | Check logs: `docker-compose logs weaviate` |

---

# 🎯 **11. Summary**

This PoC shows how Nebius Cloud can power a **fast, GPU‑accelerated**, reproducible data stack:

- H2O for data engineering  
- Weaviate for vector search  
- DVC for versioning  
- Superset for analytics  
- Postgres for storage  

When deployed on Nebius GPU instances, this pipeline becomes significantly faster, more scalable, and ready for enterprise AI workloads.

---

# ✔️ **12. Final Notes**

This README is meant to serve as:

- A **technical guide**
- A **deployment manual**
- A **Nebius‑aligned architecture reference**
- A **troubleshooting dictionary**

For enterprise-scale deployments, consider:

- Running Weaviate on **Nebius GPU Kubernetes**  
- Storing DVC remotes in **Nebius Object Storage**  
- Using Nebius **GPU inference endpoints** for ultra-fast embedding generation  

---

