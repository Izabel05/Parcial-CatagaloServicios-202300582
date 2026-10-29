#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f compose.test.yaml -p catalogo-desk-tests)
ready() {
  for attempt in $(seq 1 30); do
    if "${compose[@]}" exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  return 1
}
snapshot() {
  "${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -v ON_ERROR_STOP=1 -tAc \
    "SELECT json_build_object('tickets',(SELECT count(*) FROM sd_tickets),'colas',(SELECT count(*) FROM sd_colas),'historial',(SELECT count(*) FROM sd_historial),'comentarios',(SELECT count(*) FROM sd_comentarios),'adjuntos',(SELECT count(*) FROM sd_adjuntos),'datos',(SELECT md5(string_agg(row_to_json(t)::text,'|' ORDER BY id)) FROM sd_tickets t),'archivos',(SELECT md5(string_agg(sha256||encode(contenido,'hex'),'|' ORDER BY id)) FROM sd_adjuntos));"
}
"${compose[@]}" up -d db
ready
count=$("${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -tAc 'SELECT count(*) FROM sd_tickets;' | tr -d '[:space:]')
if [[ "$count" == 0 ]]; then echo 'Ejecute primero las pruebas Service Desk.' >&2; exit 1; fi
before=$(snapshot)
"${compose[@]}" restart db
ready
after=$(snapshot)
if [[ "$before" != "$after" ]]; then echo 'Persistencia Service Desk fallida.' >&2; exit 1; fi
echo "Persistencia Service Desk OK: $after"
