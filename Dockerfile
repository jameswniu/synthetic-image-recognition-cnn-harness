FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.8.13

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY scripts/serve.py ./scripts/serve.py
COPY data/golden ./data/golden
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "scripts.serve:app", "--host", "0.0.0.0", "--port", "8000"]
