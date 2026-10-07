// Tab switching functionality
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons and contents
        document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Add active class to clicked button and corresponding content
        button.classList.add('active');
        const tabName = button.getAttribute('data-tab');
        document.getElementById(tabName).classList.add('active');
    });
});

// Connection storage (session-based)
const activeSessions = {
    connect: null,
    listen: null
};

// ============ SAFE RENDERING (F-001) ============
// Everything shown on the page is built from DOM nodes. append() turns a string into a text node,
// so host names and messages from the API are never parsed as HTML. Do not use innerHTML here:
// tests/test_xss.py fails when it comes back.
function node(tag, className, ...children) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.append(...children);
    return element;
}

function showResult(container, className, ...children) {
    container.replaceChildren(node('div', className, ...children));
    container.classList.add('show');
}

function showError(container, message) {
    showResult(container, 'result-error', node('strong', null, '✗ Error:'), ` ${message}`);
}

function appendOutput(output, className, ...children) {
    output.append(node('div', className, ...children));
    output.scrollTop = output.scrollHeight;
}

function showSession(sessionDiv, prefix, infoLabel, infoText, handlers) {
    const closeButton = node('button', 'btn btn-danger btn-small', 'Close');
    closeButton.addEventListener('click', handlers.close);

    const input = node('input');
    input.type = 'text';
    input.id = `${prefix}-message`;
    input.placeholder = 'Type message and press Enter...';
    input.addEventListener('keypress', handlers.keypress);

    const sendButton = node('button', 'btn btn-primary', 'Send');
    sendButton.addEventListener('click', handlers.send);

    const output = node('div', 'session-output');
    output.id = `${prefix}-output`;

    sessionDiv.replaceChildren(
        node('div', 'session-header', 'Active Connection', closeButton),
        node('div', 'session-info', node('strong', null, infoLabel), ` ${infoText}`),
        node('div', 'session-input', input, sendButton),
        output
    );
    sessionDiv.classList.add('show');
}

// ============ TCP CONNECT TAB ============
document.getElementById('connect-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const host = document.getElementById('connect-host').value;
    const port = parseInt(document.getElementById('connect-port').value);
    const timeout = parseInt(document.getElementById('connect-timeout').value);

    const resultDiv = document.getElementById('connect-result');
    showResult(resultDiv, 'result-info', node('span', 'spinner'), ' Connecting...');

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port, timeout })
        });

        const data = await response.json();

        if (data.success) {
            activeSessions.connect = data.connection_id;
            showResult(resultDiv, 'result-success', node('strong', null, '✓ Connected!'), node('br'), data.message);
            document.getElementById('connect-form').style.display = 'none';
            showConnectSession(data);
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, error.message);
    }
});

function showConnectSession(connectionData) {
    showSession(
        document.getElementById('connect-session'),
        'connect',
        'Host:',
        `${connectionData.host}:${connectionData.port}`,
        { close: closeConnectSession, keypress: handleConnectKeypress, send: sendConnectData }
    );
}

function handleConnectKeypress(event) {
    if (event.key === 'Enter') {
        sendConnectData();
    }
}

async function sendConnectData() {
    const input = document.getElementById('connect-message');
    const message = input.value.trim();

    if (!message) return;

    const output = document.getElementById('connect-output');
    appendOutput(output, null, node('strong', 'output-sent', '→'), ` ${message}`);

    try {
        const response = await fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ connection_id: activeSessions.connect, message })
        });

        const data = await response.json();

        if (data.success) {
            input.value = '';
        } else {
            appendOutput(output, 'output-error', node('strong', null, 'Error:'), ` ${data.error}`);
        }
    } catch (error) {
        appendOutput(output, 'output-error', node('strong', null, 'Error:'), ` ${error.message}`);
    }
}

function closeConnectSession() {
    if (!activeSessions.connect) return;

    fetch('/api/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: activeSessions.connect })
    });

    activeSessions.connect = null;
    document.getElementById('connect-session').classList.remove('show');
    document.getElementById('connect-session').replaceChildren();
    document.getElementById('connect-result').classList.remove('show');
    document.getElementById('connect-result').replaceChildren();
    document.getElementById('connect-form').style.display = '';
}

// ============ TCP LISTEN TAB ============
document.getElementById('listen-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const port = parseInt(document.getElementById('listen-port').value);
    const timeout = parseInt(document.getElementById('listen-timeout').value);

    const resultDiv = document.getElementById('listen-result');
    showResult(resultDiv, 'result-info', node('span', 'spinner'), ` Listening on port ${port}...`);

    try {
        const response = await fetch('/api/listen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port, timeout })
        });

        const data = await response.json();

        if (data.success) {
            activeSessions.listen = data.connection_id;
            showResult(resultDiv, 'result-success', node('strong', null, '✓ Connection Accepted!'), node('br'), data.message);
            document.getElementById('listen-form').style.display = 'none';
            showListenSession(data);
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, error.message);
    }
});

function showListenSession(connectionData) {
    showSession(
        document.getElementById('listen-session'),
        'listen',
        'Remote Host:',
        `${connectionData.remote_host}:${connectionData.remote_port}`,
        { close: closeListenSession, keypress: handleListenKeypress, send: sendListenData }
    );
}

function handleListenKeypress(event) {
    if (event.key === 'Enter') {
        sendListenData();
    }
}

async function sendListenData() {
    const input = document.getElementById('listen-message');
    const message = input.value.trim();

    if (!message) return;

    const output = document.getElementById('listen-output');
    appendOutput(output, null, node('strong', 'output-sent', '→'), ` ${message}`);

    try {
        const response = await fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ connection_id: activeSessions.listen, message })
        });

        const data = await response.json();

        if (data.success) {
            input.value = '';
        } else {
            appendOutput(output, 'output-error', node('strong', null, 'Error:'), ` ${data.error}`);
        }
    } catch (error) {
        appendOutput(output, 'output-error', node('strong', null, 'Error:'), ` ${error.message}`);
    }
}

function closeListenSession() {
    if (!activeSessions.listen) return;

    fetch('/api/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: activeSessions.listen })
    });

    activeSessions.listen = null;
    document.getElementById('listen-session').classList.remove('show');
    document.getElementById('listen-session').replaceChildren();
    document.getElementById('listen-result').classList.remove('show');
    document.getElementById('listen-result').replaceChildren();
    document.getElementById('listen-form').style.display = '';
}

// ============ PORT SCAN TAB ============
function portList(title, className, ports) {
    return [
        node('strong', null, title),
        node('div', 'port-list', ...ports.map(port => node('span', `port-tag ${className}`, String(port))))
    ];
}

document.getElementById('scan-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const host = document.getElementById('scan-host').value;
    const ports = document.getElementById('scan-ports').value;
    const timeout = parseInt(document.getElementById('scan-timeout').value);

    const resultDiv = document.getElementById('scan-result');
    showResult(resultDiv, 'result-info', node('span', 'spinner'), ` Scanning ports on ${host}...`);

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, ports, timeout })
        });

        const data = await response.json();

        if (data.success) {
            const results = node('div', 'scan-results');

            if (data.open_ports.length > 0) {
                results.append(...portList('Open Ports:', 'port-open', data.open_ports));
            }

            if (data.closed_ports.length > 0) {
                results.append(...portList('Closed Ports:', 'port-closed', data.closed_ports));
            }

            resultDiv.replaceChildren(
                node('div', 'result-success', node('strong', null, '✓ Scan Complete!'), node('br'), data.scan_summary),
                results
            );
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, error.message);
    }
});
