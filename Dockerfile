FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    OTEL_SERVICE_NAME=math-mcp \
    OTEL_PROPAGATORS=xray \
    OTEL_PYTHON_ID_GENERATOR=xray

COPY pyproject.toml .
RUN uv pip install . && uv pip install "aws-opentelemetry-distro>=0.10.1"

RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8000

COPY src/ src/

CMD ["opentelemetry-instrument", "python", "-m", "math_mcp.server"]
