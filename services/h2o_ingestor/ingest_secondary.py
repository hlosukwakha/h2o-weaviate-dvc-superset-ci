import os
import pandas as pd
import os
import os
import logging
logging.basicConfig(level=logging.DEBUG)

SECONDARY_DATA_URL = os.getenv(
    "SECONDARY_DATA_URL",
    "https://people.sc.fsu.edu/~jburkardt/data/csv/airtravel.csv",
)

RAW_PATH = "data/raw/secondary.csv"
PROCESSED_PATH = "data/processed/secondary_clean.csv"


def download_secondary():
    import requests

    os.makedirs("data/raw", exist_ok=True)
    print(f"Downloading secondary open data from {SECONDARY_DATA_URL} ...")
    r = requests.get(SECONDARY_DATA_URL)
    r.raise_for_status()
    with open(RAW_PATH, "wb") as f:
        f.write(r.content)
    print(f"Saved secondary raw data to {RAW_PATH}")


def process_secondary():
    os.makedirs("data/processed", exist_ok=True)
    df = pd.read_csv(RAW_PATH)
    df = df.dropna(how="all")
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Saved secondary processed data to {PROCESSED_PATH}")
    return df


def main():
    download_secondary()
    process_secondary()


if __name__ == "__main__":
    main()
