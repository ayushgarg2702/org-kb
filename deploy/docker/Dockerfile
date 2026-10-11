FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY schemas ./schemas
COPY templates ./templates
COPY config ./config
COPY migrations ./migrations
COPY alembic.ini ./
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["org-brain", "serve"]
