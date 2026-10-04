"""Branch B, stage 2 -- the command parser (Table 4's `parser.py`, PRD Sec. 4.3).

Transcript in, grammar-constrained JSON string out. The request shape --
`/apply-template` then `/tokenize` with `add_special=false` then
`/completion` with the GBNF grammar attached -- is not re-derived here: it is
`eval/surface_b.py`'s sequence, which Gate 3 proved token-for-token identical
to the Kaggle (`transformers`) side. A second, slightly different sequence
would quietly reopen that gap between the two measurement surfaces.

Two classes, deliberately separated:

* `LlamaServerProcess` owns the subprocess lifecycle -- start, health-check,
  stop. It is the only thing here that touches a real binary or a real GGUF
  file, which is what lets `CommandParser` be tested against a fake HTTP
  server instead (see `runtime/test_parser.py`'s abort test).
* `CommandParser` owns the request/response shape and Sec. 4.3's preemption
  *optimisation*: `abort()` closes the in-flight request's socket from
  whatever thread calls it. This is best-effort by construction -- Sec. 4.3
  is explicit that the correctness guarantee never depends on it: "A stale
  Branch B result therefore cannot take effect, whether or not its decode was
  stopped." The bus's sequence numbers (`runtime/bus.py`,
  `runtime/pipeline.py`'s `Dispatcher`) carry correctness regardless of
  whether `abort()` actually lands in time.

Spike S7 (`spikes/reports/S7_preemption_capability.md`) evaluated an
in-process `llama.cpp` abort callback against a separate, signal-killable
worker process, and adopted the in-process callback as primary with the
worker-process model as the safety fallback. `llama-server` is the worker
process in that architecture -- one per `CommandParser` -- and closing its
socket mid-request is the signal; `LlamaServerProcess.stop()` is the SIGKILL
fallback if a request-level abort does not land.
"""

from __future__ import annotations

import http.client
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from schema.logger import get_structured_logger
from schema.schema import GRAMMAR_PATH

__all__ = [
    "SYSTEM_PROMPT",
    "ParseAborted",
    "ParseResult",
    "LlamaServerProcess",
    "CommandParser",
]

logger = get_structured_logger("runtime.parser")

REPO_ROOT = Path(__file__).resolve().parent.parent

_ENV_LLAMA = os.environ.get("LLAMA_SERVER_BIN")
if _ENV_LLAMA:
    LLAMA_SERVER = Path(_ENV_LLAMA)
elif (Path.home() / "llama.cpp" / "build" / "bin" / "llama-server").is_file():
    LLAMA_SERVER = Path.home() / "llama.cpp" / "build" / "bin" / "llama-server"
elif shutil.which("llama-server"):
    LLAMA_SERVER = Path(shutil.which("llama-server"))
else:
    LLAMA_SERVER = Path.home() / "llama.cpp" / "build" / "bin" / "llama-server"

#: `eval/surface_b.py:199` reads the same key from the same file -- one fixed
#: audit prompt, so the runtime and the accuracy measurement never diverge.
AUDIT_PROMPTS_PATH = REPO_ROOT / "eval" / "fixed_audit_prompts.json"
SYSTEM_PROMPT: str = json.loads(AUDIT_PROMPTS_PATH.read_text(encoding="utf-8"))["system_prompt"]

#: Table 7: three cores for STT and the SLM, never concurrent.
DEFAULT_THREADS = 3
#: `-c 512` (Sec. 4, decision 3): the static prefix is KV-cached and actual
#: context is roughly 40 tokens; 512 is headroom, not a target.
DEFAULT_CONTEXT = 512
#: Matches `eval/surface_b.py`'s MAX_TOKENS -- enough for the longest
#: canonical command plus its closing brace.
DEFAULT_MAX_TOKENS = 96


class ParseAborted(Exception):
    """Raised when a decode was interrupted -- by `abort()`, or by a transport
    failure indistinguishable from one. Callers (`runtime/pipeline.py`) treat
    both the same way: no command reaches the bus for this utterance."""


@dataclass(frozen=True)
class ParseResult:
    """One decode. `prefill_ms`/`decode_ms` are Table 6's `slm_prefill` and
    `slm_decode` rows, read from `llama-server`'s own response timings rather
    than measured by wrapping the call -- the server's clock excludes this
    process's own JSON (de)serialisation overhead."""

    raw: str
    prefill_ms: float
    decode_ms: float


class LlamaServerProcess:
    """Subprocess lifecycle for one `llama-server` instance bound to one GGUF.

    Mirrors `eval/surface_b.py:run_artefact`'s process management (same
    flags: `--parallel 1` for deterministic greedy decoding, Sec 2.7's
    reproducibility requirement), packaged as a reusable component instead of
    inline experiment-script code.
    """

    def __init__(
        self,
        gguf: Path,
        *,
        host: str = "127.0.0.1",
        port: int = 8914,
        threads: int = DEFAULT_THREADS,
        context: int = DEFAULT_CONTEXT,
        binary: Path = LLAMA_SERVER,
    ) -> None:
        if not binary.is_file():
            raise FileNotFoundError(f"llama-server not built at {binary}")
        if not gguf.is_file():
            raise FileNotFoundError(f"gguf artefact not found at {gguf}")
        self.host = host
        self.port = port
        self._process = subprocess.Popen(
            [
                str(binary), "-m", str(gguf), "--host", host, "--port", str(port),
                "-t", str(threads), "-c", str(context), "--parallel", "1", "--log-disable",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def wait_ready(self, timeout: float = 180.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(f"llama-server exited early ({self._process.returncode})")
            try:
                conn = http.client.HTTPConnection(self.host, self.port, timeout=2)
                try:
                    conn.request("GET", "/health")
                    response = conn.getresponse()
                    response.read()
                    if response.status == 200:
                        return
                finally:
                    conn.close()
            except OSError:
                pass
            time.sleep(0.2)
        raise RuntimeError("llama-server did not become healthy in time")

    def stop(self, timeout: float = 20.0) -> None:
        """The SIGKILL fallback path from Spike S7: terminate, then kill."""
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=timeout)

    def __enter__(self) -> "LlamaServerProcess":
        self.wait_ready()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.stop()


class CommandParser:
    """Transcript -> grammar-constrained JSON string, over an already-running
    `llama-server`. Does not itself manage the subprocess -- see
    `CommandParser.for_gguf` for the common case, or point `host`/`port` at a
    fake HTTP server in tests to exercise `abort()` deterministically.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        grammar_path: Path = GRAMMAR_PATH,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._host = host
        self._port = port
        self._grammar = grammar_path.read_text(encoding="utf-8")
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        self._lock = threading.Lock()
        self._conn: http.client.HTTPConnection | None = None

    @classmethod
    def for_gguf(cls, gguf: Path, **server_kwargs: object) -> tuple["CommandParser", LlamaServerProcess]:
        """Convenience path for real use: start a server, return both it and
        a parser bound to it. Caller owns the server's lifetime (stop it when
        done, or use it as a context manager)."""
        server = LlamaServerProcess(gguf, **server_kwargs)  # type: ignore[arg-type]
        server.wait_ready()
        return cls(host=server.host, port=server.port), server

    def _post(self, path: str, payload: dict, *, timeout: float = 30.0) -> dict:
        conn = http.client.HTTPConnection(self._host, self._port, timeout=timeout)
        with self._lock:
            self._conn = conn
        try:
            conn.request(
                "POST", path, body=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )
            response = conn.getresponse()
            return json.loads(response.read())
        finally:
            with self._lock:
                if self._conn is conn:
                    self._conn = None
            conn.close()

    def abort(self) -> None:
        """Best-effort: close the in-flight request's socket (Sec. 4.3's
        "optimisation, desirable" half). A no-op if nothing is in flight."""
        with self._lock:
            conn = self._conn
        if conn is not None and conn.sock is not None:
            try:
                conn.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def parse(self, transcript: str) -> ParseResult:
        """One utterance through the deployed decode path.

        Raises `ParseAborted` on any transport failure -- including the one
        `abort()` deliberately causes -- so callers cannot tell an abort apart
        from a genuine server fault and are not tempted to. Sec. 4.3 does not
        need them to: either way, no command reaches the bus for this
        utterance.
        """
        try:
            templated = self._post(
                "/apply-template",
                {
                    "messages": [
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": transcript},
                    ]
                },
            )["prompt"]
            tokens = self._post("/tokenize", {"content": templated, "add_special": False})["tokens"]
            data = self._post(
                "/completion",
                {
                    "prompt": tokens,
                    "temperature": 0.0,
                    "n_predict": self._max_tokens,
                    "cache_prompt": False,
                    "grammar": self._grammar,
                },
                timeout=60.0,
            )
        except (OSError, ValueError, KeyError) as exc:
            logger.info(
                "Branch B decode did not complete: %s", exc,
                extra={"event": "parse_aborted", "reason": str(exc)},
            )
            raise ParseAborted(str(exc)) from exc

        timings = data.get("timings", {})
        return ParseResult(
            raw=data.get("content", "").strip(),
            prefill_ms=float(timings.get("prompt_ms", 0.0)),
            decode_ms=float(timings.get("predicted_ms", 0.0)),
        )
