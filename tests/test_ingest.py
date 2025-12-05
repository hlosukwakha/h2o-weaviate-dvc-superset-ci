import pandas as pd
from services.h2o_ingestor import ingest


def test_process_with_pandas(tmp_path, monkeypatch):
    # Arrange: create a tiny raw DataFrame
    df_raw = pd.DataFrame(
        {
            "location": ["loc1", "loc2", None],
            "parameter": ["pm25", "pm10", "pm25"],
            "value": [10.0, None, 5.0],  # one row with missing value
            "extra_col": [1, 2, 3],      # will be dropped
        }
    )

    # Point PROCESSED_PATH into a temp directory so the test doesn’t pollute repo
    processed_path = tmp_path / "opendata_clean.csv"
    monkeypatch.setattr(ingest, "PROCESSED_PATH", processed_path)

    # Act
    df_processed = ingest.process_with_pandas(df_raw)

    # Assert: columns are filtered
    assert list(df_processed.columns) == ["location", "parameter", "value"]

    # Assert: rows with missing "value" are dropped (we had 3, one with None)
    assert len(df_processed) == 2

    # Assert: file was written
    assert processed_path.exists()

    # Optional: read back and compare
    df_from_disk = pd.read_csv(processed_path)
    assert len(df_from_disk) == len(df_processed)