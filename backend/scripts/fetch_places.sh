#!/usr/bin/env bash
# Descarrega a base de localidades do GeoNames (CC BY 4.0) e carrega-a na base de dados.
set -euo pipefail
dest="${ARQUIVO_GEONAMES_PATH:-$(cd "$(dirname "$0")/../.." && pwd)/data/geonames}"
mkdir -p "$dest"
base="https://download.geonames.org/export/dump"
for name in cities500.zip admin1CodesASCII.txt; do
  if [ ! -f "$dest/$name" ]; then
    curl -sfL --retry 3 -o "$dest/$name.part" "$base/$name"
    mv "$dest/$name.part" "$dest/$name"
  fi
done
if [ ! -f "$dest/cities500.txt" ]; then
  unzip -p "$dest/cities500.zip" cities500.txt > "$dest/cities500.txt.part"
  mv "$dest/cities500.txt.part" "$dest/cities500.txt"
fi
cd "$(dirname "$0")/.."
uv run python -m arquivo.persistence.places "$dest"
