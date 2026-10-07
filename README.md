# Netcat Web

A small web-based Netcat alternative built with Python and Flask: open TCP connections, listen for incoming ones and scan ports from the browser.

> **Security notice.** This is a learning project with **no authentication**. It can open connections and scan ports from the machine it runs on, so run it only on a trusted local machine and never expose it to the internet or an untrusted network.

## Features

- **TCP Connect** – connect to a remote host and send messages
- **TCP Listen** – wait for one incoming connection on a local port (`127.0.0.1`) and send messages
- **Port Scan** – check which ports are open, e.g. `20-25,80,443`
- REST API under `/api/*` and a simple web UI

Not implemented yet: receiving data from the remote side, UDP, IPv6.

## Tech stack

Python 3.11+, Flask, plain JavaScript, [uv](https://docs.astral.sh/uv/), Docker (optional).

## Quick start

```bash
git clone https://github.com/timfadmv/netcat.git
cd netcat
uv sync
uv run python app.py
```

Open http://127.0.0.1:5000.

`./run.sh` (macOS/Linux) and `run.bat` (Windows) do the same: they install the locked dependencies with uv and start the app.

Dependencies are defined in `pyproject.toml` and locked in `uv.lock`, which is the only source of pinned versions (also used by the Docker image).

### Configuration

The development server (`python app.py`) is configured with environment variables. The defaults are safe: loopback only, debugger off.

| Variable | Default | Meaning |
|---|---|---|
| `NETCAT_HOST` | `127.0.0.1` | Interface to listen on |
| `NETCAT_PORT` | `5000` | Port |
| `NETCAT_DEBUG` | off | `1` enables the Flask debugger; refused unless the host is a loopback address |

### Docker

```bash
docker compose up --build
```

The container runs gunicorn (one worker, eight threads) as an unprivileged user with a read-only file system and no extra capabilities. The port is published on `127.0.0.1` only. The open connections are kept in the memory of the process, which is why there is a single worker.

TCP Listen only accepts connections from inside the container (it binds to `127.0.0.1` there), so use it when running the app locally rather than in Docker.

## API

All endpoints accept and return JSON.

| Method | Endpoint       | Body                                   |
|--------|----------------|----------------------------------------|
| POST   | `/api/connect` | `host`, `port`, `timeout`              |
| POST   | `/api/listen`  | `port`, `timeout`                      |
| POST   | `/api/scan`    | `host`, `ports`, `timeout`             |
| POST   | `/api/send`    | `connection_id`, `message`             |
| POST   | `/api/close`   | `connection_id`                        |

## CI / security checks

GitHub Actions runs a single pipeline on every push and pull request to `main`:

- **Tests** – `pytest` and `ruff` on the Python version used in the Docker image
- **SAST** – Semgrep; findings fail the job
- **SCA** – Trivy image scan
- **DAST** – OWASP ZAP baseline scan
- **Secrets** – [gitleaks](https://github.com/gitleaks/gitleaks) over the whole git history; the job fails when a secret is found

Secrets are also checked before every commit with the same gitleaks version via pre-commit (`pre-commit install`).
