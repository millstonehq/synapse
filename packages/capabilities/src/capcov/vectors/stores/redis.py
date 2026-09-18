"""Redis store adapter on a stdlib RESP client: DUMP every key, RESTORE it back.

No redis-py: the protocol needed here is small (SCAN with a cursor, DUMP, PTTL,
RESTORE ... REPLACE, FLUSHALL, LLEN, PING, SELECT) and a socket that speaks it is
forty lines. Restoring key by key from DUMP payloads, rather than flushing, keeps
caches the seed warmed as part of the starting state exactly as the incumbent
left them; a TTL is carried through PTTL (``-1``/``-2`` become "no expiry").

Inspection reports the sorted key list and, when the adapter is told which keys
are queues, each queue's length -- that is what the fixture's drain loop polls.

Refusal: a ``-ERR`` reply is ``RedisError`` with the server's text; a closed
socket mid-reply is ``RedisError`` too, never a truncated snapshot.
"""

from __future__ import annotations

import socket


class RedisError(RuntimeError):
    """The server answered with an error, or stopped answering."""


class RespClient:
    """Minimal RESP2 client over one blocking socket."""

    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""

    def close(self) -> None:
        self.sock.close()

    def _fill(self) -> None:
        chunk = self.sock.recv(65536)
        if not chunk:
            raise RedisError("server closed the connection mid-reply")
        self.buf += chunk

    def _line(self) -> bytes:
        while b"\r\n" not in self.buf:
            self._fill()
        line, self.buf = self.buf.split(b"\r\n", 1)
        return line

    def _bulk(self, size: int) -> bytes:
        while len(self.buf) < size + 2:
            self._fill()
        data, self.buf = self.buf[:size], self.buf[size + 2 :]
        return data

    def _read(self):
        line = self._line()
        kind, rest = line[:1], line[1:]
        if kind == b"+":
            return rest
        if kind == b"-":
            raise RedisError(rest.decode(errors="replace"))
        if kind == b":":
            return int(rest)
        if kind == b"$":
            size = int(rest)
            return None if size < 0 else self._bulk(size)
        if kind == b"*":
            count = int(rest)
            return None if count < 0 else [self._read() for _ in range(count)]
        raise RedisError("unexpected reply " + line.decode(errors="replace"))

    def call(self, *args: bytes | str | int):
        parts = [a if isinstance(a, bytes) else str(a).encode() for a in args]
        payload = b"*%d\r\n" % len(parts) + b"".join(b"$%d\r\n%s\r\n" % (len(p), p) for p in parts)
        self.sock.sendall(payload)
        return self._read()

    # -- the commands the adapter needs ------------------------------------

    def ping(self) -> bool:
        return self.call("PING") == b"PONG"

    def keys(self, count: int = 1000) -> list[bytes]:
        found, cursor = [], b"0"
        while True:
            cursor, batch = self.call("SCAN", cursor, "COUNT", count)
            found.extend(batch)
            if cursor == b"0":
                break
        return found

    def snapshot(self) -> list[tuple[bytes, int, bytes]]:
        entries = []
        for key in self.keys():
            payload = self.call("DUMP", key)
            if payload is None:
                continue  # expired between SCAN and DUMP: not part of the state
            entries.append((key, max(0, self.call("PTTL", key)), payload))
        return entries

    def restore(self, entries: list[tuple[bytes, int, bytes]]) -> None:
        self.call("FLUSHALL")
        for key, ttl, payload in entries:
            self.call("RESTORE", key, ttl, payload, "REPLACE")


class RedisStore:
    """Snapshot/restore/inspect one Redis database.

    ``queues`` maps a queue NAME (what the fixture reports) to the list KEY whose
    length is that queue's depth. A connection is opened per operation so a
    server restart between vectors is not a stale socket.
    """

    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        queues: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.host, self.port, self.db = host, int(port), int(db)
        self.queues = dict(queues or {})
        self.timeout = timeout

    def connect(self) -> RespClient:
        client = RespClient(self.host, self.port, self.timeout)
        if self.db:
            client.call("SELECT", self.db)
        return client

    def ping(self) -> bool:
        client = self.connect()
        try:
            return client.ping()
        finally:
            client.close()

    def snapshot(self) -> list[tuple[bytes, int, bytes]]:
        client = self.connect()
        try:
            return client.snapshot()
        finally:
            client.close()

    def restore(self, token: list[tuple[bytes, int, bytes]]) -> None:
        if not isinstance(token, list):
            raise ValueError("RedisStore.restore: token is not a list of (key, ttl, payload)")
        client = self.connect()
        try:
            client.restore(token)
        finally:
            client.close()

    def queue_depths(self) -> dict[str, int]:
        """Only the configured queues' lengths: what a drain loop needs to ask."""
        client = self.connect()
        try:
            return {name: int(client.call("LLEN", key)) for name, key in sorted(self.queues.items())}
        finally:
            client.close()

    def inspect(self) -> dict:
        """``{"redis_keys": [sorted keys], "queues": {name: length}}``."""
        client = self.connect()
        try:
            keys = sorted(key.decode(errors="replace") for key in client.keys())
            queues = {name: int(client.call("LLEN", key)) for name, key in sorted(self.queues.items())}
        finally:
            client.close()
        return {"redis_keys": keys, "queues": queues}

    # -- observation ----------------------------------------------------------
    # Key-value changes are informational (a cache is inside the box), so the
    # cheap honest signal is DBSIZE: when it moved, list keys and diff; when it
    # did not, report nothing. A value rewritten in place under an existing key
    # is not observed here -- that is the documented limit of this store.

    def mark(self) -> tuple[int, list[str]]:
        client = self.connect()
        try:
            size = int(client.call("DBSIZE"))
            keys = sorted(key.decode(errors="replace") for key in client.keys()) if size <= self.observe_keys_up_to else []
        finally:
            client.close()
        return (size, keys)

    def changes_since(self, mark: tuple[int, list[str]]) -> dict:
        size_before, keys_before = mark
        client = self.connect()
        try:
            size = int(client.call("DBSIZE"))
            if size == size_before:
                return {"rows": {}, "collections": {}, "unbound": []}
            keys = sorted(key.decode(errors="replace") for key in client.keys())
        finally:
            client.close()
        before = set(keys_before)
        added, removed = sorted(set(keys) - before), sorted(before - set(keys))
        return {"rows": {}, "collections": {}, "unbound": [],
                "redis": {"added": added, "removed": removed, "size": [size_before, size]}}

    observe_keys_up_to = 20000
