"""Laravel route reader: group prefixes composed, both handler styles, resources.

FacilityGrid's backend declares 592 distinct routes across 47 Route::group
prefixes. The generic tree-sitter query sees the literal path only, so 'GET /'
under /account and 'GET /' under /project collapse to one surface and the
inventory reads 323. This reader walks the nesting and composes the path a
runtime probe will actually see. It refuses to guess: a non-literal path or
prefix is an unresolved obligation, a duplicate composed route is reported under
excluded_surfaces, never silently dropped.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from capcov.adapters import load

_HAVE_TS = (
    importlib.util.find_spec("tree_sitter") is not None
    and importlib.util.find_spec("tree_sitter_language_pack") is not None
)

ROUTES = r"""<?php
use App\Http\Controllers\AccountController;
use Illuminate\Support\Facades\Route;

Route::group(['prefix' => 'api/v1', 'middleware' => ['auth']], function () {
    Route::get('/', [AccountController::class, 'index']);
    Route::group(['prefix' => 'account'], function () {
        Route::get('/', [AccountController::class, 'show']);
        Route::post('settings', ['uses' => 'AccountController@update']);
        Route::delete('tokens/{token_id}', 'AccountController@revoke');
    });
    Route::prefix('billing')->middleware('auth')->group(function () {
        Route::get('invoices', [AccountController::class, 'invoices']);
    });
    Route::resource('photos', PhotoController::class)->only(['index', 'store', 'destroy']);
    Route::apiResource('tags', TagController::class);
    Route::get($dynamic, [AccountController::class, 'dyn']);
    Route::group(['prefix' => $tenant], function () {
        Route::get('inside', [AccountController::class, 'inside']);
    });
    Route::get('/', [AccountController::class, 'index']);
});
\Route::get('health', fn () => 'ok');
"""


@unittest.skipUnless(_HAVE_TS, "treesitter extra not installed")
class LaravelRoutesTests(unittest.TestCase):
    def _core(self) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes").mkdir()
            (root / "routes" / "api.php").write_text(ROUTES)
            module = load("laravel-routes", plugin="capcov_contrib.laravel_routes:discover")
            return module.discover(root, root, config={"globs": ["routes/**/*.php"]})

    def test_group_prefixes_compose_into_the_path(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /api/v1", ids)
        self.assertIn("http:GET /api/v1/account", ids)
        self.assertIn("http:POST /api/v1/account/settings", ids)
        self.assertIn("http:DELETE /api/v1/account/tokens/{token_id}", ids)

    def test_fluent_prefix_group_composes_too(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /api/v1/billing/invoices", ids)

    def test_both_handler_styles_are_read(self) -> None:
        by_id = {s["id"]: s for s in self._core()["surfaces"]}
        self.assertEqual(by_id["http:GET /api/v1/account"]["handler_symbol"], "AccountController@show")
        self.assertEqual(by_id["http:POST /api/v1/account/settings"]["handler_symbol"], "AccountController@update")
        self.assertEqual(by_id["http:DELETE /api/v1/account/tokens/{token_id}"]["handler_symbol"], "AccountController@revoke")
        self.assertEqual(by_id["http:GET /health"]["handler_symbol"], "closure")

    def test_resource_expands_with_only_and_api_resource_omits_forms(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /api/v1/photos", ids)
        self.assertIn("http:POST /api/v1/photos", ids)
        self.assertIn("http:DELETE /api/v1/photos/{photo}", ids)
        self.assertNotIn("http:GET /api/v1/photos/create", ids)
        self.assertNotIn("http:GET /api/v1/photos/{photo}", ids)
        for verb, path in [("GET", "/api/v1/tags"), ("POST", "/api/v1/tags"), ("GET", "/api/v1/tags/{tag}"),
                           ("PUT", "/api/v1/tags/{tag}"), ("PATCH", "/api/v1/tags/{tag}"),
                           ("DELETE", "/api/v1/tags/{tag}")]:
            self.assertIn(f"http:{verb} {path}", ids)
        self.assertNotIn("http:GET /api/v1/tags/create", ids)
        self.assertNotIn("http:GET /api/v1/tags/{tag}/edit", ids)

    def test_dynamic_path_and_dynamic_prefix_are_unresolved_not_guessed(self) -> None:
        core = self._core()
        kinds = [(u["kind"], u["reason"]) for u in core["unresolved"]]
        self.assertTrue(any(k == "dynamic-route" for k, _ in kinds), kinds)
        self.assertTrue(any(k == "dynamic-prefix" for k, _ in kinds), kinds)
        ids = {s["id"] for s in core["surfaces"]}
        self.assertFalse(any(i.endswith("/inside") for i in ids), ids)

    def test_duplicate_composed_route_is_reported_not_dropped(self) -> None:
        core = self._core()
        dup = [s for s in core["excluded_surfaces"]["surfaces"] if s["path"] == "/api/v1" and s["method"] == "GET"]
        self.assertEqual(len(dup), 1)
        self.assertIn("duplicate", dup[0]["reason"])
        self.assertEqual(core["excluded_surfaces"]["count"], len(core["excluded_surfaces"]["surfaces"]))

    def test_leading_backslash_facade_is_read(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /health", ids)

    def test_no_route_files_is_an_unresolved_entry_not_an_empty_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = load("laravel-routes", plugin="capcov_contrib.laravel_routes:discover")
            core = module.discover(root, root, config={"globs": ["routes/**/*.php"]})
        self.assertEqual(core["surfaces"], [])
        self.assertTrue(any(u["kind"] == "no-surfaces" for u in core["unresolved"]))
