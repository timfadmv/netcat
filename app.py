"""
Main Flask application for Netcat web interface
"""
import os

from flask import Flask, jsonify, render_template, request

from netcat_core import NetcatCore

app = Flask(__name__)
netcat = NetcatCore()

# The frontend only loads its own script and stylesheet and talks to its own API.
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

SECURITY_HEADERS = {
    'Content-Security-Policy': CONTENT_SECURITY_POLICY,
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Embedder-Policy': 'require-corp',
    'Cross-Origin-Resource-Policy': 'same-origin',
}


@app.after_request
def add_security_headers(response):
    """Add security headers to every response, including errors and static files"""
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)

    # API responses carry connection details and must not be stored by caches
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'

    return response


@app.route('/')
def index():
    """Render the main web interface"""
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect():
    """Establish a TCP connection to a remote host"""
    try:
        data = request.json
        host = data.get('host')
        port = int(data.get('port'))
        timeout = int(data.get('timeout', 5))

        if not host or not port:
            return jsonify({'error': 'Host and port are required'}), 400

        result = netcat.connect(host, port, timeout)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Connection failed: {str(e)}'}), 500

@app.route('/api/listen', methods=['POST'])
def listen():
    """Start listening on a local port"""
    try:
        data = request.json
        port = int(data.get('port'))
        timeout = int(data.get('timeout', 30))

        if not port:
            return jsonify({'error': 'Port is required'}), 400

        result = netcat.listen(port, timeout)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Listen failed: {str(e)}'}), 500

@app.route('/api/scan', methods=['POST'])
def scan_ports():
    """Scan ports on a target host"""
    try:
        data = request.json
        host = data.get('host')
        ports = data.get('ports')  # e.g., "20-25,80,443"
        timeout = int(data.get('timeout', 2))

        if not host or not ports:
            return jsonify({'error': 'Host and ports are required'}), 400

        result = netcat.scan_ports(host, ports, timeout)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500

@app.route('/api/send', methods=['POST'])
def send_data():
    """Send data through an active connection"""
    try:
        data = request.json
        connection_id = data.get('connection_id')
        message = data.get('message')

        if not connection_id or message is None:
            return jsonify({'error': 'Connection ID and message are required'}), 400

        result = netcat.send_data(connection_id, message)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Send failed: {str(e)}'}), 500

@app.route('/api/close', methods=['POST'])
def close_connection():
    """Close an active connection"""
    try:
        data = request.json
        connection_id = data.get('connection_id')

        if not connection_id:
            return jsonify({'error': 'Connection ID is required'}), 400

        result = netcat.close_connection(connection_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Close failed: {str(e)}'}), 500

LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def get_server_config(env=None):
    """
    Read host, port and debug flag for the development server from the environment.

    Defaults are safe: loopback only, debugger off. The Werkzeug debugger allows code
    execution, so it is refused on any interface other than loopback.
    """
    env = os.environ if env is None else env

    host = env.get('NETCAT_HOST', '127.0.0.1')

    try:
        port = int(env.get('NETCAT_PORT', '5000'))
    except ValueError:
        raise SystemExit('NETCAT_PORT must be a number') from None
    if not 1 <= port <= 65535:
        raise SystemExit('NETCAT_PORT must be between 1 and 65535')

    debug = env.get('NETCAT_DEBUG', '').lower() in ('1', 'true', 'yes')
    if debug and host not in LOOPBACK_HOSTS:
        raise SystemExit('Refusing to run the debugger on a non-loopback interface')

    return host, port, debug


if __name__ == "__main__":
    # Development server only; the Docker image runs the app with gunicorn.
    host, port, debug = get_server_config()
    app.run(host=host, port=port, debug=debug)
