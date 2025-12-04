FROM apache/superset:3.1.0

USER root

RUN /app/.venv/bin/python -m ensurepip --upgrade || true && \
    pip install --no-cache-dir \
        Flask-Cors \
        psycopg2-binary \
        pillow

USER superset