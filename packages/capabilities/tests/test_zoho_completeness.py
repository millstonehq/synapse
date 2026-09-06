from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capcov.flows.catalog import build_catalog
from capcov.flows.cli import main
from capcov.flows.discovery import discover
from capcov.flows.zoho import Export, derive

SOURCE = """application "Fixture"
{
 forms
 {
  form Stores
  {
   Login_List
   (
    type = text
   )
  }
  form Prices
  {
   Store
   (
    type = picklist
    values = Stores.ID
   )
  }
  form SelectStores
  {
   store data in zc = false
  }
 }
 reports
 {
  default spreadsheet Pricing
  {
   show all rows from Prices [Store.Login_List.contains(zoho.loginuserid)]
   custom actions
   (
    "Save"
    (
     workflow = save
    )
   )
  }
 }
 pages
 {
  page Dashboard(argument)
  {
   Content="<report componentLinkName='Pricing'/>"
  }
 }
 functions
 {
  Deluge
  {
   void PEOPLE.update(int id)
   {
    row = Stores[ID == id];
    if(id > 0)
    {
     row.Login_List = "a-secret-that-must-not-appear";
    }
    thisapp.PEOPLE.cycle(id);
   }
   void PEOPLE.cycle(int id)
   {
    thisapp.PEOPLE.update(id);
   }
  }
 }
 workflow
 {
  form
  {
   OnSubmit as "Submit"
   {
    type = form
    form = SelectStores
    button = Submit
    on click
    {
     thisapp.PEOPLE.update(input.Stores);
    }
   }
  }
  functions
  {
   save as "Save"
   {
    form = Prices
    on start
    {
     thisapp.PEOPLE.update(ID);
    }
   }
  }
  schedule
  {
   Daily as "Daily"
   {
    frequency = daily
    status = inactive
    on start
    {
     thisapp.PEOPLE.update(1);
    }
   }
  }
 }
 web
 {
  forms
  {
   form Stores
   {
    label placement = left
   }
  }
  menu
  {
   space Main
   {
    section Tools
    {
     form SelectStores
     {
     }
    }
   }
  }
 }
 share_settings
 {
  "Operator"
  {
   ModulePermissions
   {
    Prices
    {
     enabled = Viewall,Modifyall
     ReportPermissions
     {
      Pricing={"View","Edit"}
     }
    }
   }
  }
 }
}
"""


def inventory(source: str = SOURCE) -> dict:
    graph = derive(source, "fixture.ds")
    return {
        "scope": "fixture",
        "obligations": graph["nodes"],
        "graphs": [{k: v for k, v in graph.items() if k != "nodes"}],
    }


class ZohoCompletenessTests(unittest.TestCase):
    def test_regenerating_an_incomplete_inventory_cannot_bypass_the_census_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = inventory()
            document["graphs"][0]["census"][0]["classified"] = 0
            path = root / "inventory.json"
            path.write_text(json.dumps(document))
            with patch("builtins.print"):
                self.assertEqual(
                    main(
                        [
                            "catalog",
                            str(path),
                            "--out",
                            str(root / "catalog.json"),
                            "--require-declarations",
                            "--quiet",
                        ]
                    ),
                    1,
                )

    def test_unique_and_required_field_declarations_are_accounted(self) -> None:
        changed = SOURCE.replace("   Login_List\n", "   must have unique Login_List\n")
        graph = derive(changed, "fixture.ds")
        field = next(n for n in graph["nodes"] if n["id"] == "zoho:field:Stores:Login_List")
        self.assertTrue(field["required"])
        self.assertTrue(field["unique"])
        self.assertTrue(all(c["declared"] == c["classified"] for c in graph["census"]))

    def test_unrecognised_field_syntax_keeps_census_open(self) -> None:
        changed = SOURCE.replace("   Login_List\n", "   unexpected modifier Login_List\n")
        graph = derive(changed, "fixture.ds")
        self.assertTrue(
            any(g["reason"] == "unsupported field declaration" for g in graph["unresolved"])
        )

    def test_query_equality_is_not_a_field_write(self) -> None:
        changed = SOURCE.replace(
            'row.Login_List = "a-secret-that-must-not-appear";',
            "result = Stores[Store.Login_List = input.Name];",
        )
        graph = derive(changed, "fixture.ds")
        self.assertFalse(any(e["relation"] == "writes-field" for e in graph["edges"]))

    def test_cross_app_call_resolves_only_with_the_named_dependency_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.ds").write_text(
                SOURCE.replace("thisapp.PEOPLE.cycle(id);", "common.PEOPLE.update(id);")
            )
            (root / "common.ds").write_text(SOURCE)
            config = {
                "scope": "fixture",
                "root": ".",
                "adapters": [{"kind": "zoho-export", "export": "main.ds"}],
            }
            path = root / "config.json"
            path.write_text(json.dumps(config))
            before = discover(path)
            missing = [
                n
                for n in before["obligations"]
                if n.get("owner") == "zoho:external:common.PEOPLE.update"
            ]
            self.assertTrue(missing)
            config["adapters"].append(
                {"kind": "zoho-export", "export": "common.ds", "namespace": "common"}
            )
            path.write_text(json.dumps(config))
            after = discover(path)
            self.assertFalse(
                any(
                    n.get("owner") == "zoho:external:common.PEOPLE.update"
                    for n in after["obligations"]
                )
            )
            self.assertTrue(
                any(
                    e["to"] == "zoho:common:function:PEOPLE.update"
                    and e["relation"] == "resolves-to"
                    for e in after["graphs"][0]["edges"]
                )
            )
            self.assertIn("common.ds", after["sources"])

    def test_metadata_does_not_duplicate_declarations(self) -> None:
        graph = derive(SOURCE, "fixture.ds")
        self.assertEqual(graph["summary"]["surface"], 5)
        self.assertTrue(all(c["declared"] == c["classified"] for c in graph["census"]))

    def test_default_spreadsheet_and_parameterised_page_are_inventoried(self) -> None:
        graph = derive(SOURCE, "fixture.ds")
        nodes = {n["id"]: n for n in graph["nodes"]}
        self.assertEqual(nodes["zoho:screen:Pricing"]["screen_kind"], "default spreadsheet")
        self.assertIn("zoho:screen:Dashboard", nodes)
        self.assertTrue(
            any(
                e["from"] == "zoho:screen:Dashboard"
                and e["to"] == "zoho:screen:Pricing"
                and e["relation"] == "page-reference"
                for e in graph["edges"]
            )
        )

    def test_dialog_is_a_surface_without_inventing_a_table(self) -> None:
        graph = derive(SOURCE, "fixture.ds")
        self.assertNotIn("zoho:entity:SelectStores", {n["id"] for n in graph["nodes"]})
        self.assertFalse(any(g["reason"] == "unresolved edits to" for g in graph["unresolved"]))

    def test_store_selection_dependency_is_derived_through_a_call_and_lookup(self) -> None:
        catalog = build_catalog(inventory())
        dependency = next(
            d for d in catalog["dependencies"] if d["from"] == "zoho:workflow:form:OnSubmit"
        )
        self.assertEqual(dependency["to"], "zoho:screen:Pricing")
        self.assertEqual(dependency["via"], "zoho:field:Stores:Login_List")
        self.assertEqual(dependency["status"], "candidate")

    def test_removed_write_removes_dependency(self) -> None:
        changed = SOURCE.replace('row.Login_List = "a-secret-that-must-not-appear";', "info id;")
        self.assertEqual(build_catalog(inventory(changed))["dependencies"], [])

    def test_nav_actions_schedules_and_grants_are_separate_obligations(self) -> None:
        graph = derive(SOURCE, "fixture.ds")
        self.assertEqual(graph["summary"]["grant"], 4)
        self.assertEqual(graph["summary"]["action"], 1)
        schedule = next(n for n in graph["nodes"] if n["kind"] == "schedule")
        self.assertFalse(schedule["active"], "inactive schedules are retained, not dropped")
        nav = next(n for n in graph["nodes"] if n.get("navigation_kind") == "form")
        self.assertEqual(nav["path"], ["Main", "Tools", "SelectStores"])

    def test_source_literals_are_not_exported(self) -> None:
        self.assertNotIn("a-secret-that-must-not-appear", json.dumps(derive(SOURCE, "fixture.ds")))

    def test_braces_in_comments_and_strings_cannot_create_declarations(self) -> None:
        changed = SOURCE.replace(
            "row = Stores[ID == id];", 'row = Stores[ID == id];\n/* } { */\ninfo "} {";\n// } {\n'
        )
        self.assertEqual(
            derive(changed, "fixture.ds")["summary"], derive(SOURCE, "fixture.ds")["summary"]
        )

    def test_unbalanced_export_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "unclosed"):
            Export(SOURCE[:-2])

    def test_new_section_is_not_silently_accepted(self) -> None:
        graph = derive(SOURCE[:-2] + "\nnew_runtime_surface\n{\n}\n}\n", "fixture.ds")
        self.assertTrue(
            any(g["reason"] == "unsupported top-level section" for g in graph["unresolved"])
        )
        self.assertFalse(all(c["declared"] == c["classified"] for c in graph["census"]))

    def test_missing_function_is_retained_as_a_reference_failure(self) -> None:
        changed = SOURCE.replace("thisapp.PEOPLE.cycle(id);", "thisapp.PEOPLE.missing(id);")
        graph = derive(changed, "fixture.ds")
        self.assertTrue(
            any(g["owner"] == "zoho:function:PEOPLE.missing" for g in graph["unresolved"])
        )

    def test_candidate_generation_does_not_claim_behavioral_coverage(self) -> None:
        catalog = build_catalog(inventory())
        self.assertTrue(catalog["declarations_accounted"])
        self.assertFalse(catalog["behaviorally_complete"])
        self.assertTrue(all(f["missing"] for f in catalog["families"]))
        # Recursion in the fixture must terminate without a guessed depth cap.
        self.assertTrue(catalog["memberships"]["zoho:function:PEOPLE.cycle"])

    def test_source_set_detects_new_unknown_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text('@app.get("/")\ndef index():\n return 1\n')
            config = {
                "scope": "fixture",
                "root": ".",
                "adapters": [{"kind": "python-routes", "globs": ["*.py"]}],
                "source_sets": [
                    {
                        "directory": ".",
                        "extensions": [".py"],
                        "exclude": {"config.json": "discovery config is hashed separately"},
                    }
                ],
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config))
            before = discover(config_path)
            (root / "new.js").write_text('export const endpoint = "/new";')
            after = discover(config_path)
            self.assertNotEqual(before["sources"], after["sources"])
            self.assertIn("boundary:file:new.js", {o["id"] for o in after["obligations"]})
            narrowed = copy.deepcopy(config)
            narrowed["source_sets"][0]["exclude"]["new.js"] = ""
            config_path.write_text(json.dumps(narrowed))
            with self.assertRaisesRegex(ValueError, "reasons"):
                discover(config_path)
