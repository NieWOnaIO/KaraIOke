{
  inputs = {
    # nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flakeUtils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flakeUtils,
  }:
    flakeUtils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        buildInputs = with pkgs; [
          zlib
          stdenv.cc.cc.lib
          glib

          # python313
          python39
          ffmpeg

          uv
        ];
        ld_path = "${pkgs.lib.makeLibraryPath buildInputs}";
      in {
        devShells = {
          default = pkgs.mkShell {
            inherit buildInputs;
            shellHook = ''
              export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:${ld_path}"
            '';
          };
        };
      }
    );
}
