import http.server
import threading
import unittest
from contextlib import redirect_stdout
from io import StringIO

import speedtest

PAYLOAD = b"x" * 250_000


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *args):
        pass


class SpeedtestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/file"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_fetch_reads_full_body(self):
        size, seconds = speedtest.fetch(self.url, timeout=5)
        self.assertEqual(size, len(PAYLOAD))
        self.assertGreater(seconds, 0)

    def test_mbit_per_s(self):
        self.assertAlmostEqual(speedtest.mbit_per_s(1_000_000, 1.0), 8.0)
        self.assertEqual(speedtest.mbit_per_s(100, 0), 0.0)

    def test_run_reports_totals(self):
        out = StringIO()
        with redirect_stdout(out):
            code = speedtest.main([self.url, "-n", "3"])
        self.assertEqual(code, 0)
        self.assertIn(f"({len(PAYLOAD) * 3} B)", out.getvalue())
        self.assertIn("3 из 3", out.getvalue())


if __name__ == "__main__":
    unittest.main()
