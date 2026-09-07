import sqlite3
import unittest

from capcov.adapters import python_fastapi_sqlalchemy as adapter
from capcov.adapters.sqlite_literals import tables
from capcov.core import fixpoint

from .support import Project


class DeclarationTest(unittest.TestCase):
    def test_inventory_matches_real_sqlite_tables(self):
        script = '''
            -- CREATE TABLE imaginary (id);
            CREATE TABLE IF NOT EXISTS widgets (
                id INTEGER PRIMARY KEY, note TEXT DEFAULT 'CREATE TABLE fake (id);');
            /* CREATE TABLE also_fake (id); */
            CREATE TABLE "order details" (id INTEGER);
            CREATE TABLE `backtick` (id INTEGER);
            CREATE TABLE [bracketed] (id INTEGER);
        '''
        with sqlite3.connect(":memory:") as db:
            db.executescript(script)
            actual = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        self.assertEqual(set(tables(script)), actual)

    def test_attached_schema_and_escaped_identifier_are_retained(self):
        self.assertEqual(
            tables('create temporary table "audit"."odd""name" (id);'),
            ['audit.odd"name'],
        )

    def test_unsupported_declarations_and_non_sql_are_not_invented(self):
        self.assertEqual(tables('''
            SELECT 'CREATE TABLE fake (id)';
            CREATE VIEW view_name AS SELECT 1;
            CREATE TABLE 'single_quoted' (id);
            CREATE TABLE derived AS SELECT 1;
            CREATE VIRTUAL TABLE search USING fts5(body);
        '''), [])


class AdapterTest(unittest.TestCase):
    SOURCE = '''
from fastapi import FastAPI
app = FastAPI()

def initialize(db):
    db.executescript("CREATE TABLE items (id INTEGER); CREATE TABLE history (id INTEGER);")
    db.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER)")

@app.get("/items")
def items(db):
    return db.execute("SELECT * FROM items")

def dynamic(db, name):
    db.execute(f"SELECT * FROM {name}")
'''

    def discover(self, enabled):
        with Project({"main.py": self.SOURCE}) as project:
            (project.root / "capcov.toml").write_text(
                f"[capcov]\nsqlite_ddl = {str(enabled).lower()}\n"
            )
            return adapter.discover(project.source, project.root)

    def test_explicit_opt_in_preserves_existing_adapter_behavior(self):
        raw = self.discover(False)
        self.assertEqual(raw["entities"], [])
        self.assertEqual(raw["blind_spots"], [])

    def test_declarations_expand_denominator_without_fabricating_route_binding(self):
        raw = self.discover(True)
        self.assertEqual([e["name"] for e in raw["entities"]], ["history", "items"])
        entity = raw["entities"][0]
        self.assertEqual(entity["file"], "app/main.py")
        self.assertEqual(entity["declaration_kind"], "sqlite_literal_ddl")
        self.assertIsNone(entity["symbol"])
        bindings, _ = fixpoint.bind(
            [s["handler"] for s in raw["surfaces"]], raw["_calls"], raw["_direct"]
        )
        self.assertEqual(bindings["app.main:items"], {})

    def test_every_sql_call_keeps_an_explicit_binding_gap(self):
        blind = self.discover(True)["blind_spots"]
        self.assertEqual(len(blind), 4)
        self.assertEqual(sum(b["kind"] == "literal_sql_unbound" for b in blind), 3)
        self.assertEqual(sum(b["kind"] == "computed_sql_or_expression" for b in blind), 1)
        self.assertTrue(all(b["blind"] and b["line"] for b in blind))

    def test_orm_declaration_takes_priority_over_duplicate_sql(self):
        source = self.SOURCE + '\nclass Item:\n    __tablename__ = "items"\n'
        with Project({"main.py": source}) as project:
            (project.root / "capcov.toml").write_text("[capcov]\nsqlite_ddl = true\n")
            raw = adapter.discover(project.source, project.root)
        items = [e for e in raw["entities"] if e["name"] == "items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["symbol"], "Item")

    def test_string_false_does_not_silently_enable_discovery(self):
        with Project({"main.py": self.SOURCE}) as project:
            (project.root / "capcov.toml").write_text('[capcov]\nsqlite_ddl = "false"\n')
            with self.assertRaisesRegex(ValueError, "must be a boolean"):
                adapter.discover(project.source, project.root)


if __name__ == "__main__":
    unittest.main()
