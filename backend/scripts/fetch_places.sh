#!/usr/bin/env bash
# Descarrega a base de localidades do GeoNames (CC BY 4.0) e carrega-a na base de dados.
set -euo pipefail
dest="${ARQUIVO_GEONAMES_PATH:-$(cd "$(dirname "$0")/../.." && pwd)/data/geonames}"
mkdir -p "$dest"
base="https://download.geonames.org/export/dump"
for name in cities500.zip admin1CodesASCII.txt; do
  [ -f "$dest/$name" ] || curl -sfL --retry 3 -o "$dest/$name" "$base/$name"
done
[ -f "$dest/cities500.txt" ] || unzip -oq "$dest/cities500.zip" -d "$dest"
cd "$(dirname "$0")/.."
uv run python -m arquivo.persistence.places "$dest"
