# ---- Builder stage ----
FROM python:3.13-alpine3.23 AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.13-alpine3.23

WORKDIR /app

# Only the built virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Only the application files needed at runtime
COPY app.py netcat_core.py ./
COPY templates ./templates
COPY static ./static

# pip is not needed at runtime; remove it to shrink the attack surface
# (its vendored msgpack, urllib3 and setuptools are flagged by Trivy)
RUN python -m pip uninstall -y pip

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

CMD ["python", "app.py"]
