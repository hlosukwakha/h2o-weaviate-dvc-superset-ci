import os
import time
import logging
from pathlib import Path
from urllib.parse import urlparse
import logging


import requests
import pandas as pd
import h2o
from h2o.frame import H2OFrame
from sqlalchemy import create_engine
import weaviate
from weaviate.classes.config import Property, DataType
from weaviate.exceptions import WeaviateBaseError, UnexpectedStatusCodeException, InsufficientPermissionsError


logging.basicConfig(
    level=logging.DEBUG,  # or INFO if you prefer
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Config (env overrides)
# -----------------------------------------------------------------------------
DATA_URL = os.getenv(
    "DATA_URL",
    # Example OpenAQ CSV.GZ from S3 – replace with any other open CSV/CSV.GZ URL
    "https://openaq-data-archive.s3.amazonaws.com/records/csv.gz/"
    "locationid=2178/year=2022/month=05/location-2178-20220503.csv.gz",
)

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")

POSTGRES_URI = os.getenv(
    "POSTGRES_URI",
    "postgresql://superset:superset@postgres:5432/superset",
)

DATASET_NAME = os.getenv("DATASET_NAME", "openaq_measurements")

RAW_PATH = Path(os.getenv("RAW_PATH", "data/raw/opendata.csv.gz"))
PROCESSED_PATH = Path(os.getenv("PROCESSED_PATH", "data/processed/opendata_clean.csv"))

WEAVIATE_CLASS = os.getenv("WEAVIATE_CLASS", "Measurement")

# Flags to loosen coupling (CI / local dev)
SKIP_H2O = os.getenv("SKIP_H2O", "false").lower() == "true"
SKIP_WEAVIATE = os.getenv("SKIP_WEAVIATE", "false").lower() == "true"
SKIP_POSTGRES = os.getenv("SKIP_POSTGRES", "false").lower() == "true"

# Columns we care about (if present)
SELECT_COLS = ("location", "city", "country", "parameter", "value", "unit")


# -----------------------------------------------------------------------------
# Wait for Weaviate to be ready
# -----------------------------------------------------------------------------


def wait_for_weaviate(timeout: int = 120, interval: int = 5) -> weaviate.WeaviateClient:
    """
    Block until Weaviate is ready (leader elected & schema readable),
    then return a connected client.
    """
    start = time.time()
    logger.info("Waiting for Weaviate at %s ...", WEAVIATE_URL)

    while True:
        client = _connect_weaviate_v4()
        try:
            # lightweight readiness check
            client.collections.list_all()
            logger.info("✅ Weaviate is ready.")
            return client

        except InsufficientPermissionsError as e:
            logger.warning("Weaviate not ready yet (leader/permissions issue): %s", e)

        except UnexpectedStatusCodeException as e:
            logger.warning("Weaviate returned unexpected status while warming up: %s", e)

        except WeaviateBaseError as e:
            logger.warning("General Weaviate error while waiting: %s", e)

        except Exception as e:
            logger.warning("Error while waiting for Weaviate: %s", e)

        if time.time() - start > timeout:
            raise RuntimeError("Timed out waiting for Weaviate to be ready")

        logger.info("⏳ Waiting for Weaviate... retrying in %s seconds", interval)
        time.sleep(interval)


# -----------------------------------------------------------------------------
# Data download & load
# -----------------------------------------------------------------------------
def download_data() -> None:
    """Download raw data from DATA_URL and save to RAW_PATH."""
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading open data from %s ...", DATA_URL)
    resp = requests.get(DATA_URL, timeout=60)
    resp.raise_for_status()
    RAW_PATH.write_bytes(resp.content)
    logger.info("Saved raw data to %s", RAW_PATH)


def load_raw_dataframe() -> pd.DataFrame:
    """
    Load the raw file into a pandas DataFrame.

    Uses compression='infer', so both CSV and CSV.GZ are supported.
    """
    logger.info("Loading raw data from %s (compression='infer')", RAW_PATH)
    df = pd.read_csv(RAW_PATH, compression="infer")
    logger.info("Raw dataframe shape: %s", df.shape)
    return df


# -----------------------------------------------------------------------------
# Processing with H2O or pandas
# -----------------------------------------------------------------------------
def process_with_h2o(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Process data with H2O:
    - convert to H2OFrame
    - keep a subset of columns if present
    - drop rows with missing 'value'
    """
    logger.info("Starting H2O cluster...")
    h2o.init()

    try:
        hf = H2OFrame(df_raw)
        logger.info("Converted to H2OFrame with %d rows, %d cols", hf.nrows, hf.ncols)

        cols_to_keep = [c for c in hf.columns if c in SELECT_COLS]
        if cols_to_keep:
            hf = hf[cols_to_keep]
            logger.info("Keeping columns: %s", cols_to_keep)
        else:
            logger.warning(
                "None of the expected columns %s found; keeping all columns",
                SELECT_COLS,
            )

        if "value" in hf.columns:
            logger.info("Dropping rows with missing 'value'")
            hf = hf[~hf["value"].isna()]
        else:
            logger.warning("'value' column not found; no row filtering performed")

        df = hf.as_data_frame()
        PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(PROCESSED_PATH, index=False)
        logger.info(
            "Saved processed data (H2O) to %s (shape=%s)",
            PROCESSED_PATH,
            df.shape,
        )
        return df

    finally:
        logger.info("Shutting down H2O cluster...")
        try:
            h2o.shutdown(prompt=False)
        except Exception as e:  # noqa: BLE001
            logger.warning("Error during H2O shutdown (ignored): %s", e)


def process_with_pandas(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Process data using pure pandas (no H2O).
    Designed to mirror the H2O path as closely as is reasonable.
    """
    logger.info("Processing with pandas only (H2O disabled or failed)")

    df = df_raw.copy()

    cols_to_keep = [c for c in df.columns if c in SELECT_COLS]
    if cols_to_keep:
        df = df[cols_to_keep]
        logger.info("Keeping columns: %s", cols_to_keep)
    else:
        logger.warning(
            "None of the expected columns %s found; keeping all columns",
            SELECT_COLS,
        )

    if "value" in df.columns:
        before = len(df)
        df = df[df["value"].notna()]
        logger.info("Dropped %d rows with missing 'value'", before - len(df))
    else:
        logger.warning("'value' column not found; no row filtering performed")

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    logger.info(
        "Saved processed data (pandas) to %s (shape=%s)",
        PROCESSED_PATH,
        df.shape,
    )
    return df


# -----------------------------------------------------------------------------
# Weaviate v4 – connection & schema
# -----------------------------------------------------------------------------
def _connect_weaviate_v4():
    """
    Connect to Weaviate using v4 `connect_to_custom`, parsing WEAVIATE_URL.

    Example WEAVIATE_URL: http://weaviate:8080
    """
    parsed = urlparse(WEAVIATE_URL)
    host = parsed.hostname or "weaviate"
    http_port = parsed.port or 8080
    secure = parsed.scheme == "https"

    logger.info(
        "Connecting to Weaviate via connect_to_custom "
        "(host=%s, http_port=%d, secure=%s, grpc_port=50051)",
        host,
        http_port,
        secure,
    )

    client = weaviate.connect_to_custom(
        http_host=host,
        http_port=http_port,
        http_secure=secure,
        grpc_host=host,
        grpc_port=50051,
        grpc_secure=secure,
    )
    return client


def ensure_weaviate_schema(client) -> None:
    """
    Create or validate the Weaviate collection using the v4 API.
    """
    # v4 returns a list of names (strings)
    existing_names = client.collections.list_all()

    if WEAVIATE_CLASS in existing_names:
        logger.info("Weaviate collection '%s' already exists", WEAVIATE_CLASS)
        return

    logger.info("Creating Weaviate collection '%s' ...", WEAVIATE_CLASS)

    client.collections.create(
        name=WEAVIATE_CLASS,
        properties=[
            Property(name="location", data_type=DataType.TEXT),
            Property(name="city", data_type=DataType.TEXT),
            Property(name="country", data_type=DataType.TEXT),
            Property(name="parameter", data_type=DataType.TEXT),
            Property(name="value", data_type=DataType.NUMBER),
            Property(name="unit", data_type=DataType.TEXT),
        ],
        # vectorizer_config can be omitted to use the server default
    )


def ingest_into_weaviate(df: pd.DataFrame) -> None:
    logger.info("Connecting to Weaviate (Python client v4)...")
    logger.info("Starting Weaviate ingestion into %s", WEAVIATE_URL)

    client = wait_for_weaviate()

    try:
        ensure_weaviate_schema(client)

        collection = client.collections.get(WEAVIATE_CLASS)

        logger.info(
            "Ingesting %d rows into Weaviate collection '%s' ...",
            len(df),
            WEAVIATE_CLASS,
        )

        objects = []
        for _, row in df.iterrows():
            objects.append(
                {
                    "location": str(row.get("location", "")),
                    "city": str(row.get("city", "")),
                    "country": str(row.get("country", "")),
                    "parameter": str(row.get("parameter", "")),
                    "value": float(row.get("value", 0))
                    if pd.notnull(row.get("value", None))
                    else None,
                    "unit": str(row.get("unit", "")),
                }
            )

        collection.data.insert_many(objects)
        logger.info("Weaviate ingestion complete.")
    finally:
        try:
            client.close()
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to close Weaviate client cleanly: %s", e)


# -----------------------------------------------------------------------------
# Postgres load
# -----------------------------------------------------------------------------
def load_into_postgres(df: pd.DataFrame) -> None:
    logger.info("Connecting to Postgres: %s", POSTGRES_URI)
    engine = create_engine(POSTGRES_URI)
    table_name = DATASET_NAME
    logger.info("Writing %d rows to Postgres table '%s' ...", len(df), table_name)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    logger.info("Finished writing to Postgres table '%s'", table_name)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    logger.info("===== Ingestion pipeline starting =====")
    logger.info("DATA_URL=%s", DATA_URL)
    logger.info(
        "SKIP_H2O=%s, SKIP_WEAVIATE=%s, SKIP_POSTGRES=%s",
        SKIP_H2O,
        SKIP_WEAVIATE,
        SKIP_POSTGRES,
    )

    download_data()
    df_raw = load_raw_dataframe()

    if SKIP_H2O:
        df_processed = process_with_pandas(df_raw)
    else:
        try:
            df_processed = process_with_h2o(df_raw)
        except Exception as e:  # noqa: BLE001
            logger.error("H2O processing failed: %s. Falling back to pandas.", e)
            df_processed = process_with_pandas(df_raw)

    # 🔹 Never let Weaviate failure kill the whole pipeline
    if SKIP_WEAVIATE:
        logger.info("SKIP_WEAVIATE=true: skipping Weaviate ingestion")
    else:
        try:
            ingest_into_weaviate(df_processed)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Weaviate ingestion FAILED (%s). "
                "Continuing without vector store ingestion.",
                e,
            )

    # 🔹 Always attempt Postgres load if not explicitly skipped
    if SKIP_POSTGRES:
        logger.info("SKIP_POSTGRES=true: skipping Postgres load")
    else:
        load_into_postgres(df_processed)

    logger.info("===== Ingestion pipeline completed (even if some steps failed) =====")


if __name__ == "__main__":
    main()
