{
  description = "Reproducible toolchain for the capcov claim-semantics experiment";

  inputs.nixpkgs.url =
    "github:NixOS/nixpkgs/34ab99075ac4f7e40cf037eef32cb1c360bb85e9";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];
      eachSystem = nixpkgs.lib.genAttrs systems;
      shenRevision = "c12933d89d7312d5d25a951bbe20d1511c3dfbea";
      forSystem = system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          go = pkgs.go_1_27;
          shenGo = (pkgs.buildGoModule.override { inherit go; }) {
            pname = "shen-go";
            version = "0-unstable-2026-09-14";
            src = pkgs.fetchFromGitHub {
              owner = "pyrex41";
              repo = "shen-go";
              rev = shenRevision;
              hash = "sha256-He6LoA/M6IjuV25KK7d2DO5dW8yccloK37KRSj5jKTA=";
            };
            vendorHash = "sha256-iTtlmSlY0qbH/1waOlfRMc1qAkBacQxI6pohRPni/so=";
            subPackages = [ "cmd/shen" ];
            nativeBuildInputs = [ pkgs.git ];
            env.GOTOOLCHAIN = "local";
            passthru.revision = shenRevision;
            meta = {
              description = "Go port of the Shen language";
              homepage = "https://github.com/pyrex41/shen-go";
              license = pkgs.lib.licenses.bsd3;
              mainProgram = "shen";
              platforms = systems;
            };
          };
        in
        { inherit pkgs go shenGo; };
    in
    {
      packages = eachSystem (system:
        let values = forSystem system;
        in {
          shen-go = values.shenGo;
          default = values.shenGo;
        });

      devShells = eachSystem (system:
        let
          values = forSystem system;
          toolPackages = with values.pkgs; [
            python312
            uv
            values.go
            git
            jq
            hyperfine
            souffle
            scip
            scip-go
            values.shenGo
          ];
          # macOS login shells run path_helper after `nix develop` sets PATH.
          # The workflow invokes `bash -lc`, so interpose a transparent Nix bash
          # that restores the pinned tool prefix through BASH_ENV.
          bashEnv = values.pkgs.writeText "capcov-bash-env" ''
            export PATH="${values.pkgs.lib.makeBinPath toolPackages}:$PATH"
          '';
          workflowBash = values.pkgs.writeShellScriptBin "bash" ''
            export BASH_ENV=${bashEnv}
            exec ${values.pkgs.bashInteractive}/bin/bash --noprofile "$@"
          '';
          shellPackages = [ workflowBash ] ++ toolPackages;
        in {
          default = values.pkgs.mkShell {
            packages = shellPackages;
            BASH_ENV = bashEnv;
            GOTOOLCHAIN = "local";
            UV_PYTHON = "${values.pkgs.python312}/bin/python3.12";
            UV_PYTHON_DOWNLOADS = "never";
            UV_PYTHON_PREFERENCE = "only-system";
            shellHook = ''
              export PATH="${values.pkgs.lib.makeBinPath shellPackages}:$PATH"
              python -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'
            '';
          };
        });

      checks = eachSystem (system:
        let
          values = forSystem system;
          pkgs = values.pkgs;
          capabilitiesSource = pkgs.lib.cleanSource ./packages/capabilities;
          goAppSource = pkgs.lib.cleanSource ./packages/capabilities/tests/fixtures/go_app;
          goAppGolden = ./packages/capabilities/tests/fixtures/scip_go_app_index.json;
        in {
          shen-package = values.shenGo;

          shen-evaluator-smoke = pkgs.runCommand "shen-evaluator-smoke" {
            nativeBuildInputs = [ values.shenGo ];
          } ''
            mkdir -p "$out"
            shen --version | tee "$out/version.txt"
            shen eval -e '(+ 20 22)' | tee "$out/evaluation.txt"
            grep -Fx '42' "$out/evaluation.txt"
            if shen eval -e '(+ 1' >"$out/malformed.stdout" 2>"$out/malformed.stderr"; then
              echo "malformed Shen unexpectedly succeeded" >&2
              exit 1
            fi
          '';

          souffle-recursive-typed-smoke = pkgs.runCommand "souffle-recursive-typed-smoke" {
            nativeBuildInputs = [ pkgs.souffle ];
          } ''
            export LC_ALL=C
            mkdir -p facts output "$out"
            cp ${./tests/souffle/recursive-typed.dl} recursive-typed.dl
            cp ${./tests/souffle/edge.facts} facts/edge.facts
            souffle --version | tee "$out/version.txt"
            souffle -F facts -D output recursive-typed.dl
            sort output/reachable.csv > reachable.sorted.csv
            diff -u ${./tests/souffle/reachable.expected.csv} reachable.sorted.csv
            cp reachable.sorted.csv "$out/reachable.csv"
          '';

          capability-regression = pkgs.runCommand "capcov-capability-regression" {
            nativeBuildInputs = [ pkgs.python312 pkgs.souffle ];
          } ''
            export LC_ALL=C
            cp -R ${capabilitiesSource} source
            chmod -R u+w source
            cd source
            # Absolute PYTHONPATH: some tests spawn `python -m capcov` from a temp cwd.
            PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .
            touch "$out"
          '';

          # Index the Go fixture with the pinned scip-go, print it with the pinned
          # scip CLI, canonicalize, and compare byte-for-byte with the committed golden.
          # go.mod has no `require` lines, so no module download is needed.
          scip-go-index-smoke = pkgs.runCommand "scip-go-index-smoke" {
            nativeBuildInputs = [ values.go pkgs.scip pkgs.scip-go pkgs.jq ];
          } ''
            export HOME="$TMPDIR/home" GOCACHE="$TMPDIR/gocache" GOPATH="$TMPDIR/gopath"
            export GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local LC_ALL=C
            mkdir -p "$HOME" "$GOCACHE" "$GOPATH" "$out"
            cp -R ${goAppSource} go_app
            chmod -R u+w go_app
            ( cd go_app && scip-go --output index.scip )
            scip print --json go_app/index.scip > raw.json
            jq -S -f ${./tests/scip/canonicalize.jq} raw.json > canonical.json
            diff -u ${goAppGolden} canonical.json
            cp canonical.json "$out/scip_go_app_index.json"
            scip --version | tee "$out/scip-version.txt"
            { scip-go --version 2>&1 || true; } | tee "$out/scip-go-version.txt"
            go version | tee "$out/go-version.txt"
            sha256sum go_app/index.scip | tee "$out/index.scip.sha256"
          '';
        });
    };
}
