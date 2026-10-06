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

// ============ TCP CONNECT TAB ============
document.getElementById('connect-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const host = document.getElementById('connect-host').value;
    const port = parseInt(document.getElementById('connect-port').value);
    const timeout = parseInt(document.getElementById('connect-timeout').value);

    const resultDiv = document.getElementById('connect-result');
    resultDiv.innerHTML = '<div class="result-info"><span class="spinner"></span> Connecting...</div>';
    resultDiv.classList.add('show');

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port, timeout })
        });

        const data = await response.json();

        if (data.success) {
            activeSessions.connect = data.connection_id;
            resultDiv.innerHTML = `<div class="result-success"><strong>✓ Connected!</strong><br>${data.message}</div>`;
            document.getElementById('connect-form').style.display = 'none';
            showConnectSession(data);
        } else {
            resultDiv.innerHTML = `<div class="result-error"><strong>✗ Error:</strong> ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="result-error"><strong>✗ Error:</strong> ${error.message}</div>`;
    }
});

function showConnectSession(connectionData) {
    const sessionDiv = document.getElementById('connect-session');
    sessionDiv.classList.add('show');
    sessionDiv.innerHTML = `
        <div class="session-header">
            Active Connection
            <button class="btn btn-danger btn-small">Close</button>
        </div>
        <div class="session-info">
            <strong>Host:</strong> ${connectionData.host}:${connectionData.port}
        </div>
        <div class="session-input">
            <input type="text" id="connect-message" placeholder="Type message and press Enter...">
            <button class="btn btn-primary">Send</button>
        </div>
        <div id="connect-output" class="session-output"></div>
    `;

    // Inline handlers are blocked by the Content-Security-Policy, so attach them here
    sessionDiv.querySelector('.btn-danger').addEventListener('click', closeConnectSession);
    sessionDiv.querySelector('#connect-message').addEventListener('keypress', handleConnectKeypress);
    sessionDiv.querySelector('.btn-primary').addEventListener('click', sendConnectData);
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
    output.innerHTML += `<div><strong class="output-sent">→</strong> ${escapeHtml(message)}</div>`;
    output.scrollTop = output.scrollHeight;

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
            output.innerHTML += `<div class="output-error"><strong>Error:</strong> ${data.error}</div>`;
            output.scrollTop = output.scrollHeight;
        }
    } catch (error) {
        output.innerHTML += `<div class="output-error"><strong>Error:</strong> ${error.message}</div>`;
        output.scrollTop = output.scrollHeight;
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
    document.getElementById('connect-session').innerHTML = '';
    document.getElementById('connect-result').classList.remove('show');
    document.getElementById('connect-result').innerHTML = '';
    document.getElementById('connect-form').style.display = '';
}

// ============ TCP LISTEN TAB ============
document.getElementById('listen-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const port = parseInt(document.getElementById('listen-port').value);
    const timeout = parseInt(document.getElementById('listen-timeout').value);

    const resultDiv = document.getElementById('listen-result');
    resultDiv.innerHTML = '<div class="result-info"><span class="spinner"></span> Listening on port ' + port + '...</div>';
    resultDiv.classList.add('show');

    try {
        const response = await fetch('/api/listen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port, timeout })
        });

        const data = await response.json();

        if (data.success) {
            activeSessions.listen = data.connection_id;
            resultDiv.innerHTML = `<div class="result-success"><strong>✓ Connection Accepted!</strong><br>${data.message}</div>`;
            document.getElementById('listen-form').style.display = 'none';
            showListenSession(data);
        } else {
            resultDiv.innerHTML = `<div class="result-error"><strong>✗ Error:</strong> ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="result-error"><strong>✗ Error:</strong> ${error.message}</div>`;
    }
});

function showListenSession(connectionData) {
    const sessionDiv = document.getElementById('listen-session');
    sessionDiv.classList.add('show');
    sessionDiv.innerHTML = `
        <div class="session-header">
            Active Connection
            <button class="btn btn-danger btn-small">Close</button>
        </div>
        <div class="session-info">
            <strong>Remote Host:</strong> ${connectionData.remote_host}:${connectionData.remote_port}
        </div>
        <div class="session-input">
            <input type="text" id="listen-message" placeholder="Type message and press Enter...">
            <button class="btn btn-primary">Send</button>
        </div>
        <div id="listen-output" class="session-output"></div>
    `;

    // Inline handlers are blocked by the Content-Security-Policy, so attach them here
    sessionDiv.querySelector('.btn-danger').addEventListener('click', closeListenSession);
    sessionDiv.querySelector('#listen-message').addEventListener('keypress', handleListenKeypress);
    sessionDiv.querySelector('.btn-primary').addEventListener('click', sendListenData);
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
    output.innerHTML += `<div><strong class="output-sent">→</strong> ${escapeHtml(message)}</div>`;
    output.scrollTop = output.scrollHeight;

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
            output.innerHTML += `<div class="output-error"><strong>Error:</strong> ${data.error}</div>`;
            output.scrollTop = output.scrollHeight;
        }
    } catch (error) {
        output.innerHTML += `<div class="output-error"><strong>Error:</strong> ${error.message}</div>`;
        output.scrollTop = output.scrollHeight;
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
    document.getElementById('listen-session').innerHTML = '';
    document.getElementById('listen-result').classList.remove('show');
    document.getElementById('listen-result').innerHTML = '';
    document.getElementById('listen-form').style.display = '';
}

// ============ PORT SCAN TAB ============
document.getElementById('scan-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const host = document.getElementById('scan-host').value;
    const ports = document.getElementById('scan-ports').value;
    const timeout = parseInt(document.getElementById('scan-timeout').value);

    const resultDiv = document.getElementById('scan-result');
    resultDiv.innerHTML = '<div class="result-info"><span class="spinner"></span> Scanning ports on ' + host + '...</div>';
    resultDiv.classList.add('show');

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, ports, timeout })
        });

        const data = await response.json();

        if (data.success) {
            let html = `<div class="result-success"><strong>✓ Scan Complete!</strong><br>${data.scan_summary}</div>`;
            html += '<div class="scan-results">';

            if (data.open_ports.length > 0) {
                html += '<strong>Open Ports:</strong><div class="port-list">';
                data.open_ports.forEach(port => {
                    html += `<span class="port-tag port-open">${port}</span>`;
                });
                html += '</div>';
            }

            if (data.closed_ports.length > 0) {
                html += '<strong>Closed Ports:</strong><div class="port-list">';
                data.closed_ports.forEach(port => {
                    html += `<span class="port-tag port-closed">${port}</span>`;
                });
                html += '</div>';
            }

            html += '</div>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="result-error"><strong>✗ Error:</strong> ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="result-error"><strong>✗ Error:</strong> ${error.message}</div>`;
    }
});

// Utility function to escape HTML special characters
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}