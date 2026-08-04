"""runtime/parser.py -- the LLM decode stage and Sec. 4.3's abort optimisation.

Two kinds of test, deliberately separated:

* `abort()`'s causal effect is tested against a fake HTTP server that sleeps
  on `/completion`, so the assertion ("abort cuts the wait short") is
  deterministic and does not depend on how fast a real model happens to
  decode on this machine.
* The request/response wiring itself -- `/apply-template` -> `/tokenize` ->
  `/completion` under the real GBNF grammar -- is tested against the real
  `llama-server` binary and a real quantised GGUF artefact, both already on
  this workstation (Session 04's Gate 3 build). Marked `slow` per
  `pytest.ini`'s convention for real subprocesses; skipped, not failed, on a
  checkout that has neither.
"""

from __future__ import annotations

import http.server
import json
import socket
import threading
import time
from pathlib import Path

import pytest

from runtime.parser import LLAMA_SERVER, REPO_ROOT, CommandParser, ParseAborted
from schema.schema import INTENTS

GGUF_DIR = REPO_ROOT / "gguf"
SMALLEST_GGUF = GGUF_DIR / "smollm2-360m-instruct-Q4_K_M.gguf"


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class _SlowCompletionHandler(http.server.BaseHTTPRequestHandler):
    """Stands in for `llama-server`: instant on template/tokenize, sleeps on
    `/completion` long enough for a test to observe `abort()` cutting it off."""

    completion_sleep_seconds = 2.0

    def _respond(self, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802 -- BaseHTTPRequestHandler's own naming
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        if self.path == "/apply-template":
            self._respond({"prompt": "TEMPLATED"})
        elif self.path == "/tokenize":
            self._respond({"tokens": [1, 2, 3]})
        elif self.path == "/completion":
            time.sleep(self.completion_sleep_seconds)
            self._respond({"content": '{"intent":"hover"}',
                           "timings": {"prompt_ms": 5.0, "predicted_ms": 1995.0}})
        else:
            self.send_error(404)

    def log_message(self, *args: object) -> None:  # silence test output
        pass


@pytest.fixture
def slow_fake_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _SlowCompletionHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        thread.join(timeout=5.0)


def test_parse_succeeds_without_abort(slow_fake_server: int) -> None:
    _SlowCompletionHandler.completion_sleep_seconds = 0.05
    parser = CommandParser(host="127.0.0.1", port=slow_fake_server)
    result = parser.parse("swarm hold")
    assert result.raw == '{"intent":"hover"}'
    assert result.decode_ms == 1995.0


def test_abort_interrupts_an_in_flight_completion_request(slow_fake_server: int) -> None:
    """Sec. 4.3: 'Abort the in-flight decode so the three inference cores are
    released immediately.' The request must not be left to run to completion."""
    _SlowCompletionHandler.completion_sleep_seconds = 2.0
    parser = CommandParser(host="127.0.0.1", port=slow_fake_server)
    outcome: dict[str, object] = {}

    def run() -> None:
        try:
            outcome["result"] = parser.parse("swarm hold")
        except ParseAborted as exc:
            outcome["aborted"] = exc

    worker = threading.Thread(target=run)
    started = time.monotonic()
    worker.start()
    time.sleep(0.3)  # let the request reach the sleeping /completion handler
    parser.abort()
    worker.join(timeout=5.0)
    elapsed = time.monotonic() - started

    assert not worker.is_alive()
    assert "aborted" in outcome, "abort() must surface as ParseAborted, not a hang or a stale result"
    assert elapsed < 1.5, f"abort took {elapsed:.2f}s against a 2.0s decode -- it did not cut anything short"


def test_abort_with_nothing_in_flight_is_a_safe_no_op(slow_fake_server: int) -> None:
    parser = CommandParser(host="127.0.0.1", port=slow_fake_server)
    parser.abort()  # must not raise


@pytest.mark.slow
def test_real_llama_server_produces_a_grammar_valid_command() -> None:
    if not LLAMA_SERVER.is_file():
        pytest.skip(f"llama-server not built at {LLAMA_SERVER}")
    if not SMALLEST_GGUF.is_file():
        pytest.skip(f"gguf artefact not present at {SMALLEST_GGUF}")

    parser, server = CommandParser.for_gguf(SMALLEST_GGUF, port=_free_tcp_port())
    try:
        result = parser.parse("swarm hold position")
        parsed = json.loads(result.raw)  # Layer 1's guarantee: always valid JSON
        assert parsed.get("intent") in INTENTS
        assert result.prefill_ms >= 0.0
        assert result.decode_ms >= 0.0
    finally:
        server.stop()
