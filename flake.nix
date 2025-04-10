{
  inputs = {
    # commit specified to avoid rebuilding of packages
    nixpkgs.url = "github:NixOS/nixpkgs/5bf7fe9dd333ea6e9220b92fdb12b03185279be2";
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

          python313
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
