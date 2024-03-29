{
  description = "Repo for experimenting on EigenTrust";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let 
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs { inherit system overlays; };
        rustVersion = pkgs.rust-bin.stable.latest.default;
      in {
        devShell = pkgs.mkShell {
          buildInputs = [
            (rustVersion.override { extensions = [ "rust-src" ]; } )
            (pkgs.python311.withPackages
              (ps: with ps; [
                numpy
                scipy
                matplotlib
                networkx
                jupyterlab
                pip
                notebook
              ]))
            pkgs.pdm
          ];

          shellHook = ''
            export CARGO_HOME=$PWD/.cargo
            export RUSTUP_HOME=$PWD/.rustup
            export PATH=$PWD/.cargo/bin:$PWD/.rustup/bin:$PWD/python/.venv/bin:$PATH
            export PYTHONPATH=$PWD/python/.venv/lib/python3.11/site-packages:$PYTHONPATH
          '';
        };
      });
}
