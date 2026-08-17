FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY app/ ./app/
COPY demo.py ./

RUN uv pip install --system -e .

EXPOSE 8080

CMD ["uvicorn", "app.routes:app", "--host", "0.0.0.0", "--port", "8080"]
