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

Without uv, use `./run.sh` (macOS/Linux) or `run.bat` (Windows).

### Docker

```bash
docker compose up --build
```

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

- **SAST** – Semgrep
- **SCA** – Trivy image scan
- **DAST** – OWASP ZAP baseline scan

Secrets are checked locally with [gitleaks](https://github.com/gitleaks/gitleaks) via pre-commit (`pre-commit install`).
