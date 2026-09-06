# Dependency maintenance

Audit date: 2026-09-06.

The root npm audit originally reported 66 vulnerable packages (8 critical,
38 high, 14 moderate, 6 low). Compatible upgrades and removal of the unused
Continue integration reduced the result to zero. Independent CLI, context-MCP,
and site lockfiles also audit clean. Continue removal deleted 779 installed
packages and the associated indexing, embedding, bundling, and native assets.
No dependency overrides remain in the main workspaces.

Quartz is a separate dependency graph inside a Git submodule. Its audit originally
reported 14 findings. The reviewed `packages/site/quartz-package-lock.json` updates
compatible dependencies and upgrades Sharp to 0.35.4 and TOML to 5.0.0. Its audit
now reports zero findings. Setup applies that lockfile's dependency declarations
to the local Quartz checkout and runs `npm ci --ignore-scripts`. This preserves
the upstream submodule revision and keeps the overlay reproducible in CI and
published site packages. Updating the Quartz version requires refreshing this
lockfile; setup rejects a version mismatch.

To refresh Quartz dependencies, run setup, update dependencies in the Quartz
checkout, run its tests/build and `npm audit`, then copy its `package-lock.json`
back to `packages/site/quartz-package-lock.json`. Keep that file in review with
any submodule update. Dependabot tracks ordinary npm manifests, GitHub Actions,
and the capability package's uv lock; the Quartz overlay needs this explicit
refresh workflow.

Checks:

```sh
npm audit
npm audit --prefix packages/site/quartz
npm run check:types -w packages/cli
npm test -w packages/cli -- --runInBand
npm run check:types -w packages/context-mcp
npm test -w packages/context-mcp
```

The capability package's complete pinned optional dependency set was exported
with `uv export --all-extras --no-hashes --no-emit-project` and checked with
`pip-audit --no-deps --disable-pip`: no known vulnerabilities found.

Audit results describe known advisories at the recorded date. Deprecation or
new-major-version notices are distinct from vulnerability findings; this change
does not force unrelated major tooling migrations.
