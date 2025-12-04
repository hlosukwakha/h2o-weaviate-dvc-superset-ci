import os

# -----------------------------------------
# Superset configuration

# IMPORTANT:
# Superset *only* loads SECRET_KEY from superset_config.py
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "ARsBtDQU3fVYNJO+rmAZvfSKWw+j3LldX0Ysd1l/cf+GHruz4TvRS1xx")

# (Optional) If you want Superset metadata to live in Postgres instead of SQLite
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:superset@postgres:5432/superset"

# Reduce noise in logs
SILENCE_FAB = True

# Allow embedding dashboards (optional)
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "expose_headers": ["*"],
    "methods": ["*"],
    "origins": ["*"],
}

# You can add more config here later