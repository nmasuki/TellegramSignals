"""HTTP Server for MT5 EA signal delivery"""
import json
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional

from .signal_store import SignalStore


class SignalRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for signal endpoints"""

    # Class-level references (set by server)
    signal_store: Optional[SignalStore] = None
    mt5_executor = None  # Optional MT5Executor reference

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/signals":
            self._handle_get_signals(query)
        elif path == "/health":
            self._handle_health()
        elif path == "/stats":
            self._handle_stats()
        elif path == "/positions":
            self._handle_positions()
        else:
            self._send_error(404, "Not found")

    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        # POST /signals/<message_id>/ack
        if path.startswith("/signals/") and path.endswith("/ack"):
            message_id = path.split("/")[2]
            self._handle_acknowledge(message_id)
        else:
            self._send_error(404, "Not found")

    def _handle_get_signals(self, query: dict):
        """Handle GET /signals?symbol=XAUUSD&since=2026-02-06T10:00:00Z"""
        if not self.signal_store:
            self._send_error(500, "Signal store not initialized")
            return

        # Get optional symbol filter
        symbol = query.get("symbol", [None])[0]

        # Get optional since filter (ISO format datetime)
        since = None
        since_str = query.get("since", [None])[0]
        if since_str:
            try:
                since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
            except ValueError:
                self._send_error(400, f"Invalid 'since' format. Use ISO format (e.g., 2026-02-06T10:00:00Z)")
                return

        # Get pending signals
        signals = self.signal_store.get_pending_signals(symbol=symbol, since=since)

        response = {
            "signals": signals,
            "count": len(signals),
            "last_update": datetime.now(timezone.utc).isoformat(),
        }

        self._send_json(response)

    def _handle_acknowledge(self, message_id: str):
        """Handle POST /signals/<message_id>/ack"""
        if not self.signal_store:
            self._send_error(500, "Signal store not initialized")
            return

        success = self.signal_store.acknowledge_signal(message_id)

        if success:
            self._send_json({
                "status": "acknowledged",
                "message_id": message_id,
            })
        else:
            self._send_error(404, f"Signal {message_id} not found")

    def _handle_health(self):
        """Handle GET /health"""
        self._send_json({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
        })

    def _handle_stats(self):
        """Handle GET /stats"""
        if not self.signal_store:
            self._send_error(500, "Signal store not initialized")
            return

        stats = self.signal_store.get_stats()

        # Add trading executor stats
        if self.mt5_executor:
            executor_stats = self.mt5_executor.get_stats()
            stats["trading"] = executor_stats
            stats["opened_position_count"] = executor_stats.get("opened_position_count", 0)
        else:
            stats["opened_position_count"] = 0

        self._send_json(stats)

    def _handle_positions(self):
        """Handle GET /positions"""
        if not self.mt5_executor:
            self._send_json({
                "positions": [],
                "opened_position_count": 0,
            })
            return

        positions = self.mt5_executor.get_all_positions()
        self._send_json({
            "positions": positions,
            "opened_position_count": self.mt5_executor.get_open_position_count(),
        })

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))

    def _send_error(self, status: int, message: str):
        """Send error response"""
        self._send_json({"error": message}, status)

    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[SignalServer] {args[0]}")


class SignalServer:
    """
    HTTP Server for MT5 EA signal delivery.

    Usage:
        store = SignalStore()
        server = SignalServer(store, port=8080)
        server.start()  # Runs in background thread

        # Add signals from Telegram extractor
        store.add_signal(signal)

        # MT5 EA fetches via: GET http://localhost:8080/signals?symbol=XAUUSD
        # MT5 EA acknowledges via: POST http://localhost:8080/signals/<id>/ack
    """

    def __init__(self, signal_store: SignalStore, host: str = "0.0.0.0", port: int = 4726):
        """
        Initialize signal server.

        Args:
            signal_store: SignalStore instance for managing signals
            host: Server bind address (default: all interfaces)
            port: Server port (default: 8080)
        """
        self.signal_store = signal_store
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def set_executor(self, executor):
        """Set the MT5 executor reference for position tracking."""
        SignalRequestHandler.mt5_executor = executor

    def start(self):
        """Start server in background thread"""
        if self._running:
            return

        # Set store on handler class
        SignalRequestHandler.signal_store = self.signal_store

        # Create server
        self._server = HTTPServer((self.host, self.port), SignalRequestHandler)
        self._running = True

        # Run in background thread
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        print(f"Signal server started on http://{self.host}:{self.port}")
        print(f"  GET  /signals                - Fetch all pending signals")
        print(f"       ?symbol=XAUUSD          - Filter by symbol")
        print(f"       &since=2026-02-06T10:00:00Z  - Filter by time (ISO format)")
        print(f"  POST /signals/<id>/ack       - Acknowledge signal")
        print(f"  GET  /health                 - Health check")
        print(f"  GET  /stats                  - Signal statistics + opened position count")
        print(f"  GET  /positions              - Open positions from MT5 executor")

    def stop(self):
        """Stop server"""
        if not self._running:
            return

        self._running = False

        if self._server:
            self._server.shutdown()
            self._server = None

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        print("Signal server stopped")

    def _run(self):
        """Server run loop"""
        try:
            self._server.serve_forever()
        except Exception as e:
            if self._running:
                print(f"Signal server error: {e}")

    def is_running(self) -> bool:
        """Check if server is running"""
        return self._running


def run_server(port: int = 4726, persistence_path: str = None):
    """
    Run signal server standalone (for testing).

    Args:
        port: Server port
        persistence_path: Path to persistence file
    """
    import signal as sig

    store = SignalStore(persistence_path=persistence_path)
    server = SignalServer(store, port=port)

    def shutdown_handler(signum, frame):
        print("\nShutting down...")
        server.stop()
        exit(0)

    sig.signal(sig.SIGINT, shutdown_handler)
    sig.signal(sig.SIGTERM, shutdown_handler)

    server.start()

    print("\nServer running. Press Ctrl+C to stop.")
    print("Add test signal with: POST /signals (not implemented in standalone mode)")

    # Keep main thread alive
    while server.is_running():
        import time
        time.sleep(1)


if __name__ == "__main__":
    run_server()
