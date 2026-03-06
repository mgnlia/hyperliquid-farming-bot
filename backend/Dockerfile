FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY backend/pyproject.toml ./pyproject.toml
RUN uv pip install --system --no-cache fastapi uvicorn httpx sse-starlette pydantic pydantic-settings

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
