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
      shenRevision = "610ba423795b38e58dde3515a0583a109411433c";
      forSystem = system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          go = pkgs.go_1_27;
          shenGo = (pkgs.buildGoModule.override { inherit go; }) {
            pname = "shen-go";
            version = "0-unstable-2026-09-09";
            src = pkgs.fetchFromGitHub {
              owner = "pyrex41";
              repo = "shen-go";
              rev = shenRevision;
              hash = "sha256-nhJdMOcSFY5Kfd695pTGGRfrtnqBdFuy5ZLoa9tfT5Y=";
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

          capability-regression = pkgs.runCommand "capcov-capability-regression" {
            nativeBuildInputs = [ pkgs.python312 ];
          } ''
            cp -R ${capabilitiesSource} source
            chmod -R u+w source
            cd source
            PYTHONPATH=src python -m unittest discover -s tests -t .
            touch "$out"
          '';
        });
    };
}
