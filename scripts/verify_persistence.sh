#!/usr/bin/env bash
set -Eeuo pipefail

compose=(docker compose -f compose.test.yaml -p catalogo-servicios-tests)

cleanup() {
  "${compose[@]}" down
}
trap cleanup EXIT

"${compose[@]}" up -d db
ready=false
for attempt in $(seq 1 30); do
  if "${compose[@]}" exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done

if [[ "$ready" != true ]]; then
  echo "P12 no pudo esperar a que PostgreSQL estuviera disponible." >&2
  exit 1
fi

"${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -v ON_ERROR_STOP=1 -c \
  "CREATE TABLE IF NOT EXISTS persistence_probe (id INTEGER PRIMARY KEY, marker TEXT NOT NULL); INSERT INTO persistence_probe (id, marker) VALUES (1, 'P12-ok') ON CONFLICT (id) DO UPDATE SET marker=EXCLUDED.marker;"
"${compose[@]}" restart db

ready=false
for attempt in $(seq 1 30); do
  if "${compose[@]}" exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done

if [[ "$ready" != true ]]; then
  echo "P12 no pudo esperar a que PostgreSQL volviera a estar disponible." >&2
  exit 1
fi

marker=$("${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -tAc \
  "SELECT marker FROM persistence_probe WHERE id=1;" | tr -d '[:space:]')
if [[ "$marker" != "P12-ok" ]]; then
  echo "P12 falló: el marcador no persistió después del reinicio." >&2
  exit 1
fi

echo "P12 OK: los datos persistieron después de reiniciar el contenedor sin eliminar el volumen."
