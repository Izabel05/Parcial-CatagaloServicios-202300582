#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f compose.test.yaml -p catalogo-procesos-tests)
ready() {
  for attempt in $(seq 1 30); do
    if "${compose[@]}" exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test </dev/null >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  return 1
}
snapshot() {
  "${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -v ON_ERROR_STOP=1 -tA <<'SQL'
WITH filas AS (
 SELECT 'tickets' entidad,id::text clave,row_to_json(t)::text valor FROM sd_tickets t
 UNION ALL SELECT 'flujos',ticket_id::text,row_to_json(t)::text FROM sd_procesos_ticket t
 UNION ALL SELECT 'aprobaciones',id::text,row_to_json(t)::text FROM sd_aprobaciones t
 UNION ALL SELECT 'vinculos',id::text,row_to_json(t)::text FROM sd_ticket_vinculos t
 UNION ALL SELECT 'correlaciones',evento_id::text,row_to_json(t)::text FROM sd_evento_incidente t
 UNION ALL SELECT 'notificaciones',id::text,row_to_json(t)::text FROM sd_notificaciones t
 UNION ALL SELECT 'historial',id::text,row_to_json(t)::text FROM sd_historial t
 UNION ALL SELECT 'adjuntos',id::text,row_to_json(t)::text FROM sd_adjuntos t
 UNION ALL SELECT 'servicios',id::text,row_to_json(t)::text FROM services t
)
SELECT jsonb_object_agg(entidad,resumen) FROM (
 SELECT entidad,jsonb_build_object('cantidad',count(*),'md5',md5(string_agg(valor,'|' ORDER BY clave))) resumen
 FROM filas GROUP BY entidad
) totales;
SQL
}
"${compose[@]}" up -d db </dev/null
ready
count=$("${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -tAc 'SELECT count(*) FROM sd_evento_incidente;' </dev/null | tr -d '[:space:]')
if [[ "$count" == 0 ]]; then echo 'Ejecute primero las pruebas de procesos.' >&2; exit 1; fi
before=$(snapshot)
"${compose[@]}" restart db </dev/null
ready
after=$(snapshot)
if [[ "$before" != "$after" ]]; then echo 'Persistencia de procesos fallida.' >&2; exit 1; fi
echo "Persistencia de procesos OK: $after"
