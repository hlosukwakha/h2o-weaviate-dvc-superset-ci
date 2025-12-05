import pandas as pd
from services.h2o_ingestor import ingest


def test_process_with_pandas(tmp_path, monkeypatch):
    # Arrange: small synthetic raw DF
    df_raw = pd.DataFrame(
        {
            "location": ["loc1", "loc2", None],
            "parameter": ["pm25", "pm10", "pm25"],
            "value": [10.0, None, 5.0],
            "extra_col": [1, 2, 3],
        }
    )

    processed_path = tmp_path / "opendata_clean.csv"
    monkeypatch.setattr(ingest, "PROCESSED_PATH", processed_path)

    # Act
    df_processed = ingest.process_with_pandas(df_raw)

    # Assert
    assert list(df_processed.columns) == ["location", "parameter", "value"]
    assert len(df_processed) == 2
    assert processed_path.exists()
