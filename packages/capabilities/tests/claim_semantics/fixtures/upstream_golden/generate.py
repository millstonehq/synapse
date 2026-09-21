"""Regenerate the upstream-main golden artifacts (see README.md).

Run with CWD=<upstream>/packages/capabilities, CAPCOV_CAP_ROOT set to that same
directory, PYTHONPATH="$CAPCOV_CAP_ROOT/src:$CAPCOV_CAP_ROOT", and the hidden
PATH from the README, then pass the RAW output directory as argv[1]:

    python3 generate.py /path/to/raw
    python3 normalize.py /path/to/raw <golden_dir> "<raw>/_work=<root>" ...

The raw run embeds absolute paths; normalize.py is what makes it comparable.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CAP = Path(os.environ["CAPCOV_CAP_ROOT"])  # <upstream>/packages/capabilities
OUT = Path(sys.argv[1])
WORK = OUT / "_work"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
WORK.mkdir(parents=True)

ENV = dict(os.environ)


def run(name: str, argv: list[str], cwd: Path) -> int:
    d = OUT / name
    d.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-m", "capcov", *argv],
        cwd=str(cwd), env=ENV, text=True, capture_output=True,
    )
    (OUT / f"{name}.stdout").parent.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.stdout").write_text(proc.stdout)
    (OUT / f"{name}.stderr").write_text(proc.stderr)
    (OUT / f"{name}.exit").write_text(f"{proc.returncode}\n")
    (OUT / f"{name}.cmd").write_text(
        "capcov " + " ".join(argv) + "\n"
    )
    return proc.returncode


def copy(src: Path, name: str) -> None:
    if src.exists():
        dst = OUT / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


# ---------------------------------------------------------------- go_app ----
go = WORK / "go_app"
shutil.copytree(CAP / "tests" / "fixtures" / "go_app", go)
run("go_app/discover", ["discover", "--target", str(go), "--out", str(WORK / "go_caps.json"), "--quiet"], WORK)
copy(WORK / "go_caps.json", "go_app/capabilities.json")
run("go_app/discover_resolver_scip", ["discover", "--target", str(go), "--out", str(WORK / "go_caps_scip.json"), "--quiet", "--resolver", "scip"], WORK)
copy(WORK / "go_caps_scip.json", "go_app/capabilities.resolver-scip.json")

# ------------------------------------------------------------ python_app ----
sys.path.insert(0, str(CAP))
from tests.support import APP  # noqa: E402

pyroot = WORK / "python_app"
pkg = pyroot / "src" / "app"
pkg.mkdir(parents=True)
(pkg / "__init__.py").write_text("")
for fname, body in APP.items():
    (pkg / fname).write_text(body)
(pyroot / "capcov.toml").write_text(
    '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\nprobe = "load"\n'
)
copy(pyroot / "capcov.toml", "python_app/capcov.toml")

caps = pyroot / "capabilities.json"
obs = pyroot / "observed.json"
cov = pyroot / "coverage.json"
run("python_app/discover", ["discover", "--target", str(pyroot), "--out", str(caps)], pyroot)
copy(caps, "python_app/capabilities.json")
run("python_app/discover_resolver_scip", ["discover", "--target", str(pyroot), "--out", str(WORK / "py_scip.json"), "--quiet", "--resolver", "scip"], pyroot)
copy(WORK / "py_scip.json", "python_app/capabilities.resolver-scip.json")
run("python_app/observe", ["observe", "--target", str(pyroot), "--out", str(obs), "--probe", "load"], pyroot)
copy(obs, "python_app/observed.json")
run("python_app/reconcile", ["reconcile", str(caps), str(obs), "--out", str(cov)], pyroot)
copy(cov, "python_app/coverage.json")
run("python_app/gate", ["gate", str(cov)], pyroot)
run("python_app/report", ["report", str(cov)], pyroot)

# ------------------------------------------------------- structured_spec ----
ss = WORK / "structured_spec"
(ss / "src").mkdir(parents=True)
(ss / "capcov.toml").write_text(
    '[capcov]\nadapter = "structured-spec"\nsource = "src"\n'
    'document = "openapi.json"\nprofile = "openapi"\n'
)
(ss / "src" / "openapi.json").write_text(
    json.dumps({"openapi": "3.1.0", "paths": {"/items": {"get": {}, "post": {}}}})
)
copy(ss / "capcov.toml", "structured_spec/capcov.toml")
copy(ss / "src" / "openapi.json", "structured_spec/openapi.json")
ss_caps = ss / "capabilities.json"
run("structured_spec/discover", ["discover", "--target", str(ss), "--out", str(ss_caps)], ss)
copy(ss_caps, "structured_spec/capabilities.json")

# ------------------------------------------------------------- flows -------
from capcov.flows.model import plan  # noqa: E402
from tests.test_flows import evidence, fixture  # noqa: E402

inventory, model = fixture()
execution_plan = plan(model, "browser")
runev = evidence(inventory, execution_plan)
fl = WORK / "flows"
fl.mkdir()
for nm, val in (("inventory", inventory), ("model", model), ("plan", execution_plan), ("run", runev)):
    (fl / f"{nm}.json").write_text(json.dumps(val))
    copy(fl / f"{nm}.json", f"flows/input_{nm}.json")
run("flows/coverage", ["flows", "coverage", str(fl / "inventory.json"), str(fl / "model.json"),
                       str(fl / "plan.json"), "--run", str(fl / "run.json"),
                       "--out", str(fl / "coverage.json")], fl)
copy(fl / "coverage.json", "flows/coverage.json")
run("flows/gate", ["flows", "gate", str(fl / "coverage.json")], fl)

# ---------------------------------------------------------- features -------
run("features/validate", ["features", "validate", str(CAP / "examples" / "feature-model-authentication.json")], CAP)
run("features/help", ["features", "--help"], CAP)

# ---------------------------------------------------------- outcomes -------
run("outcomes/help", ["outcomes", "--help"], CAP)

# ------------------------------------------------------------- help --------
run("cli/help", ["--help"], CAP)
for sub in ("discover", "observe", "reconcile", "gate", "report"):
    run(f"cli/help_{sub}", [sub, "--help"], CAP)

shutil.rmtree(WORK)
print("done")
