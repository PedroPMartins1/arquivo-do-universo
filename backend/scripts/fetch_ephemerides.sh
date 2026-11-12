#!/usr/bin/env bash
# Descarrega as efemérides (Swiss Ephemeris 1800–2400 e JPL DE421 para validação) e verifica-as.
set -euo pipefail
dest="${ARQUIVO_EPHEMERIS_PATH:-$(cd "$(dirname "$0")/../.." && pwd)/data/ephe}"
mkdir -p "$dest"
swiss="https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"
while read -r sha name url; do
  if [ ! -f "$dest/$name" ] || ! echo "$sha  $dest/$name" | sha256sum -c --quiet - 2>/dev/null; then
    curl -sfL --retry 3 -o "$dest/$name" "$url"
  fi
  echo "$sha  $dest/$name" | sha256sum -c --quiet -
done <<LIST
ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66 sepl_18.se1 $swiss/sepl_18.se1
1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7 semo_18.se1 $swiss/semo_18.se1
a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2 seas_18.se1 $swiss/seas_18.se1
a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc de421.bsp https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp
LIST
echo "efemérides em $dest"
