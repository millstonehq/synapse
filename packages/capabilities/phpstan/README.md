# capcov's PHPStan edge producer

`CapcovCallCollector.php` is the incumbent side of the static account: five
PHPStan rules that write down, for every call node PHPStan types, the edge it
makes and *how* it was resolved -- and, for every call node PHPStan cannot
type, the site and the reason. `phpstan-capcov.neon` registers them and holds
the framework tables (facades, Eloquent base classes, route registrars) so no
framework name is hard-coded in the rules.

    phpstan analyse -c phpstan-capcov.neon --error-format=json app routes > report.json

The configuration bootstraps `CapcovCallCollector.php` itself, so nothing needs
to be installed into the analysed project.

Then, on the Python side:

```python
from capcov.claims.static import phpstan_facts

facts = phpstan_facts.load_report("report.json")
result = phpstan_facts.export_bundle(facts, source_root=".", analyser_version="2.1.17",
                                     observe_tree=True)
bundle = phpstan_facts.attach(result.bundle, facts, phpstan_facts.pack_bundle(), base_pack)
```

`export_bundle` emits `schema_static_v1` -- the same relations the SCIP exporter
emits -- plus `phpstan_call_edge`, which `rules-static-phpstan-v1` lifts into
`static_edge`. Every rule over the call graph (`rules-static-v1`,
`rules-static-closure-v1`, `rules-static-reflexion-v1`, the vectors join) then
applies to a PHP index unchanged, and two indexes -- an incumbent and a
candidate -- can sit in one bundle and be compared by `rules-static-parity-v1`.

## Why not scip-php alone

capcov already runs scip-php (`capcov.scip.runner`), and it resolves PHP
*symbols* well. What it cannot resolve is the framework: every `DB::`, `Auth::`,
`Route::` and Eloquent static forward is `facade_magic` residue by construction
(`capcov.scip.blindspots`' PHP census kinds), which on a Laravel-shaped tree is
most of the interesting edges -- so `call_graph_closed` would never be emitted
and no negative static claim about such a tree could ever resolve. PHPStan types
those receivers. The two producers are complementary and are kept apart by
producer class: scip-php's rows are `scip`, these are `phpstan`, and Larastan's
framework resolutions are labelled in the edge's `kind` column rather than
passed off as typed calls.

## The recorded report

`tests/fixtures/php_app/phpstan/report.json` is the report this configuration
produces for `tests/fixtures/php_app`. PHPStan is **not** in the devShell, so
that file is authored against the contract above rather than captured from a
run, and `tests/claim_semantics/test_static_phpstan_facts.py` is in two halves:

* the default tests consume the committed report and need no PHP at all;
* `PhpstanLiveReportTest` runs the command above against a real `phpstan` and
  asserts the committed report is what comes back. It **skips by name** when
  `phpstan` is not on `PATH` -- it is the only thing that can turn the committed
  report from a contract into a recording, and until it runs somewhere that is
  exactly what it is.

Re-record with:

    cd packages/capabilities/tests/fixtures/php_app
    phpstan analyse -c ../../../phpstan/phpstan-capcov.neon \
        --error-format=json --no-progress app routes > phpstan/report.json
