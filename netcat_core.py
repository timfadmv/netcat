"""
Core netcat functionality: TCP connections, listening, and port scanning
"""
import socket
import threading
import uuid
from datetime import datetime


class NetcatCore:
    """Core netcat operations"""

    def __init__(self):
        """Initialize the NetcatCore with connection tracking"""
        self.connections: dict[str, socket.socket] = {}
        self.connection_data: dict[str, dict] = {}
        self.lock = threading.Lock()

    def _generate_connection_id(self) -> str:
        """Generate a unique connection ID"""
        return str(uuid.uuid4())

    def _validate_port(self, port: int) -> bool:
        """Validate port number is in valid range"""
        return 1 <= port <= 65535

    def _validate_host(self, host: str) -> bool:
        """Validate host string is not empty"""
        return bool(host and len(host.strip()) > 0)

    def connect(self, host: str, port: int, timeout: int = 5) -> dict:
        """
        Establish a TCP connection to a remote host

        Args:
            host: Target hostname or IP address
            port: Target port number
            timeout: Connection timeout in seconds

        Returns:
            Dictionary with connection details or error
        """
        if not self._validate_host(host):
            return {'success': False, 'error': 'Invalid host'}

        if not self._validate_port(port):
            return {'success': False, 'error': 'Invalid port number (1-65535)'}

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            # Attempt connection
            sock.connect((host, port))

            # Store connection
            conn_id = self._generate_connection_id()
            with self.lock:
                self.connections[conn_id] = sock
                self.connection_data[conn_id] = {
                    'type': 'outbound',
                    'host': host,
                    'port': port,
                    'connected_at': datetime.now().isoformat()
                }

            return {
                'success': True,
                'connection_id': conn_id,
                'message': f'Connected to {host}:{port}',
                'host': host,
                'port': port
            }

        except TimeoutError:
            return {'success': False, 'error': f'Connection timeout after {timeout}s'}
        except socket.gaierror:
            return {'success': False, 'error': f'Cannot resolve host: {host}'}
        except ConnectionRefusedError:
            return {'success': False, 'error': f'Connection refused by {host}:{port}'}
        except Exception as e:
            return {'success': False, 'error': f'Connection error: {str(e)}'}

    def listen(self, port: int, timeout: int = 30) -> dict:
        """
        Listen for incoming TCP connections on a local port

        Args:
            port: Local port to listen on
            timeout: How long to wait for a connection (in seconds)

        Returns:
            Dictionary with connection details or error
        """
        if not self._validate_port(port):
            return {'success': False, 'error': 'Invalid port number (1-65535)'}

        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.settimeout(timeout)

            # Bind to local address
            server_socket.bind(('127.0.0.1', port))
            server_socket.listen(1)

            # Wait for connection
            client_socket, client_address = server_socket.accept()

            # Store connection
            conn_id = self._generate_connection_id()
            with self.lock:
                self.connections[conn_id] = client_socket
                self.connection_data[conn_id] = {
                    'type': 'inbound',
                    'remote_host': client_address[0],
                    'remote_port': client_address[1],
                    'local_port': port,
                    'connected_at': datetime.now().isoformat()
                }

            server_socket.close()

            return {
                'success': True,
                'connection_id': conn_id,
                'message': f'Accepted connection from {client_address[0]}:{client_address[1]}',
                'remote_host': client_address[0],
                'remote_port': client_address[1]
            }

        except TimeoutError:
            return {'success': False, 'error': f'No connection received within {timeout}s'}
        except PermissionError:
            return {'success': False, 'error': f'Permission denied on port {port} (may require root)'}
        except OSError as e:
            return {'success': False, 'error': f'Socket error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Listen error: {str(e)}'}

    def scan_ports(self, host: str, ports: str, timeout: int = 2) -> dict:
        """
        Scan ports on a target host

        Args:
            host: Target hostname or IP address
            ports: Port specification (e.g., "20-25,80,443")
            timeout: Connection timeout per port in seconds

        Returns:
            Dictionary with scan results
        """
        if not self._validate_host(host):
            return {'success': False, 'error': 'Invalid host'}

        try:
            port_list = self._parse_port_spec(ports)
            if not port_list:
                return {'success': False, 'error': 'Invalid port specification'}

            open_ports = []
            closed_ports = []
            error_ports = []

            for port in port_list:
                result = self._scan_single_port(host, port, timeout)
                if result['status'] == 'open':
                    open_ports.append(port)
                elif result['status'] == 'closed':
                    closed_ports.append(port)
                else:
                    error_ports.append(port)

            return {
                'success': True,
                'host': host,
                'open_ports': open_ports,
                'closed_ports': closed_ports,
                'error_ports': error_ports,
                'scan_summary': f'{len(open_ports)} open, {len(closed_ports)} closed'
            }

        except Exception as e:
            return {'success': False, 'error': f'Scan error: {str(e)}'}

    def _parse_port_spec(self, spec: str) -> list[int]:
        """
        Parse port specification string

        Format: "20-25,80,443,8000-8010"

        Args:
            spec: Port specification string

        Returns:
            List of port numbers
        """
        ports = []
        try:
            for part in spec.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = part.split('-')
                    start, end = int(start), int(end)
                    if self._validate_port(start) and self._validate_port(end):
                        ports.extend(range(start, end + 1))
                else:
                    port = int(part)
                    if self._validate_port(port):
                        ports.append(port)
            return list(set(ports))  # Remove duplicates
        except (ValueError, AttributeError):
            return []

    def _scan_single_port(self, host: str, port: int, timeout: int) -> dict:
        """
        Scan a single port

        Args:
            host: Target host
            port: Target port
            timeout: Connection timeout

        Returns:
            Dictionary with port status
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return {'port': port, 'status': 'open'}
            else:
                return {'port': port, 'status': 'closed'}

        except Exception:
            return {'port': port, 'status': 'error'}

    def send_data(self, connection_id: str, message: str) -> dict:
        """
        Send data through an active connection

        Args:
            connection_id: ID of the connection
            message: Data to send

        Returns:
            Dictionary with send result
        """
        with self.lock:
            if connection_id not in self.connections:
                return {'success': False, 'error': 'Connection not found'}

            try:
                sock = self.connections[connection_id]
                sock.sendall(message.encode('utf-8'))

                return {
                    'success': True,
                    'bytes_sent': len(message),
                    'message': 'Data sent successfully'
                }

            except BrokenPipeError:
                return {'success': False, 'error': 'Connection closed by remote host'}
            except Exception as e:
                return {'success': False, 'error': f'Send error: {str(e)}'}

    def close_connection(self, connection_id: str) -> dict:
        """
        Close an active connection

        Args:
            connection_id: ID of the connection to close

        Returns:
            Dictionary with close result
        """
        with self.lock:
            if connection_id not in self.connections:
                return {'success': False, 'error': 'Connection not found'}

            try:
                sock = self.connections[connection_id]
                sock.close()
                del self.connections[connection_id]
                del self.connection_data[connection_id]

                return {
                    'success': True,
                    'message': 'Connection closed'
                }

            except Exception as e:
                return {'success': False, 'error': f'Close error: {str(e)}'}
