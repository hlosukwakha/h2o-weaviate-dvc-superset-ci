from services.h2o_ingestor import ingest


def test_process_with_pandas(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_path = data_dir / "opendata.csv"
    raw_path.write_text(
        "location,city,country,parameter,value,unit\n"
        "LocA,CityA,CO2,pm25,10,ug/m3\n"
    )

    monkeypatch.chdir(tmp_path)

    df = ingest.process_with_pandas()

    assert not df.empty
    assert "value" in df.columns
    assert (df["value"] == 10).all()
