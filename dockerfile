# Base images are pinned by digest (tag kept for readability); Dependabot keeps both up to date.
FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv

# ---- Builder stage ----
FROM python:3.13-alpine3.24@sha256:2d9aefe2fef018a7eb2c13064c89c71929800fd2e5dccdbf52ea5da5bb8d929a AS builder

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.13-alpine3.24@sha256:2d9aefe2fef018a7eb2c13064c89c71929800fd2e5dccdbf52ea5da5bb8d929a

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

# Run as an unprivileged user instead of root
RUN adduser -D -H -u 10001 app
USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=2)"

# One worker process with threads: the open connections live in the memory of the
# process, so several worker processes would not see each other's connections.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "app:app"]
