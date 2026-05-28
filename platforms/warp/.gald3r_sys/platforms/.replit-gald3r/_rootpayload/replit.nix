# Replit Nix environment — gald3r deploy scaffold
# Provides Node.js for the gald3r installer (bin/install.js).
{ pkgs }: {
  deps = [
    pkgs.nodejs_20
    pkgs.git
  ];
}
