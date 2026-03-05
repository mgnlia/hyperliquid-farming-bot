FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy backend source (the entire backend/ directory is the build context)
COPY . /app/backend/
COPY pyproject.toml* /app/ 2>/dev/null || true

# Install dependencies
RUN uv pip install --system fastapi uvicorn httpx sse-starlette pydantic pydantic-settings

EXPOSE 8000

ENV SIMULATION_MODE=true

# Module path: backend.main:app because we run from /app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
