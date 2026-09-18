"""The observing fast path: deltas from change logs, restores only after writes."""

from __future__ import annotations

import copy
import unittest

from capcov.vectors.fixture import ComposedFixture, FixtureError, ObservingFixture
from capcov.vectors.recorder import Session, run_vector
from capcov.vectors.schema import Request, StepSpec


class LogStore:
    """An in-memory table set that records every change as it happens."""

    def __init__(self, rows: dict[str, list[dict]]) -> None:
        self.rows = copy.deepcopy(rows)
        self.log: list[tuple[str, str, dict]] = []

    # store protocol
    def snapshot(self):
        return copy.deepcopy(self.rows)

    def restore(self, token):
        self.rows = copy.deepcopy(token)
        self.log.clear()

    def inspect(self):
        return {"rows": copy.deepcopy(self.rows)}

    # observing protocol
    def mark(self):
        return len(self.log)

    def changes_since(self, mark):
        out: dict[str, dict] = {}
        for table, kind, row in self.log[mark:]:
            entry = out.setdefault(table, {"inserted": [], "updated": [], "deleted": []})
            entry[kind].append(row)
        return {"rows": out, "collections": {}, "unbound": []}

    # the "application"
    def update(self, table: str, row_id: int, **changes):
        for row in self.rows[table]:
            if row["id"] == row_id:
                changed = {k: [row.get(k), v] for k, v in changes.items() if row.get(k) != v}
                row.update(changes)
                if changed:
                    self.log.append((table, "updated", {"id": row_id, "changed": changed}))
                return


class PlainStore(LogStore):
    """Same data, no observation: forces the inspect-diff path."""

    mark = None
    changes_since = None


class Endpoint:
    """A fake oracle: DELETE flips state, GET reads, anything else 404s."""

    base_url = "http://oracle.test"

    def __init__(self, store: LogStore) -> None:
        self.store = store

    def send(self, request: Request):
        if request.method == "DELETE":
            self.store.update("orders", 31, state=-1)
            return 200, True
        if request.method == "GET":
            return 200, {"ids": [r["id"] for r in self.store.rows["orders"] if r["state"] == 1]}
        return 404, {"message": "Not found"}

    def run_shell(self, request):
        raise AssertionError("no shell steps in this test")


def planned(method: str):
    step = StepSpec(actor=11, method=method, path="/orders/31", params={}, body=None, query={}, headers={}, drain=False)
    return [(step, [Request(kind="http", method=method, path="/orders/31", headers={}, body=None, argv=[])])]


ROWS = {"orders": [{"id": 31, "state": 1}, {"id": 32, "state": 1}]}


class ObservingPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = LogStore(ROWS)
        self.fixture = ComposedFixture({"db": self.store})
        self.endpoint = Endpoint(self.store)
        self.token = self.fixture.snapshot()
        self.session = Session(self.fixture, self.token)

    def test_composition_of_observing_stores_is_observing(self) -> None:
        self.assertTrue(isinstance(self.fixture, ObservingFixture))
        self.assertTrue(self.fixture.observing)
        self.assertTrue(self.session.observing)

    def test_write_delta_comes_from_the_change_log(self) -> None:
        result = run_vector(planned("DELETE"), self.fixture, self.token, self.endpoint, "*", (), self.session)
        self.assertEqual(result["observed_by"], "change-log")
        self.assertEqual(result["delta"], {"rows.orders": {
            "inserted": [], "updated": [{"id": 31, "changed": {"state": [1, -1]}}], "deleted": []}})
        self.assertEqual(result["steps"][0]["status"], 200)

    def test_reads_do_not_restore_and_writes_do(self) -> None:
        run_vector(planned("GET"), self.fixture, self.token, self.endpoint, "*", (), self.session)
        run_vector(planned("GET"), self.fixture, self.token, self.endpoint, "*", (), self.session)
        self.assertEqual(self.session.restores, 1, "first vector restores once; clean reads do not")
        run_vector(planned("DELETE"), self.fixture, self.token, self.endpoint, "*", (), self.session)
        self.assertEqual(self.session.restores, 1)
        self.assertFalse(self.session.pristine, "a write dirties the fixture")
        read = run_vector(planned("GET"), self.fixture, self.token, self.endpoint, "*", (), self.session)
        self.assertEqual(self.session.restores, 2, "the vector after a write restores")
        self.assertEqual(read["steps"][0]["body"], {"ids": [31, 32]}, "and sees the snapshot again")
        self.assertEqual(read["delta"], {})

    def test_declared_and_informational_routing_matches_inspect_diff(self) -> None:
        result = run_vector(planned("DELETE"), self.fixture, self.token, self.endpoint,
                            {"rows": ["notes"]}, ("orders",), self.session)
        self.assertEqual(result["delta"], {})
        self.assertIn("rows.orders", result["informational"])


class InspectDiffPathTests(unittest.TestCase):
    def test_plain_stores_take_the_inspect_diff_path_and_always_restore(self) -> None:
        store = PlainStore(ROWS)
        fixture = ComposedFixture({"db": store})
        self.assertFalse(fixture.observing)
        endpoint = Endpoint(store)
        token = fixture.snapshot()
        session = Session(fixture, token)
        run_vector(planned("GET"), fixture, token, endpoint, "*", (), session)
        run_vector(planned("GET"), fixture, token, endpoint, "*", (), session)
        self.assertEqual(session.restores, 2)
        result = run_vector(planned("DELETE"), fixture, token, endpoint, "*", (), session)
        self.assertEqual(result["observed_by"], "inspect-diff")
        self.assertEqual(result["delta"]["rows.orders"]["updated"], [{"id": 31, "changed": {"state": [1, -1]}}])

    def test_mixed_composition_refuses_to_observe(self) -> None:
        fixture = ComposedFixture({"a": LogStore(ROWS), "b": PlainStore({"notes": []})})
        with self.assertRaisesRegex(FixtureError, "cannot observe.*'b'"):
            fixture.mark()


if __name__ == "__main__":
    unittest.main()
