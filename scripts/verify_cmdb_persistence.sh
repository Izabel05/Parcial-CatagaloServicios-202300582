#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose -f compose.test.yaml -p catalogo-cmdb-tests)
ready() {
  for attempt in $(seq 1 30); do
    if "${compose[@]}" exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}
snapshot() {
  "${compose[@]}" exec -T db psql -U catalogo_test -d catalogo_servicios_test -v ON_ERROR_STOP=1 -tAc \
    "SELECT json_build_object('servicios',(SELECT count(*) FROM services),'dispositivos',(SELECT count(*) FROM cmdb_dispositivos),'relaciones',(SELECT count(*) FROM cmdb_relaciones),'historial',(SELECT count(*) FROM cmdb_auditoria),'datos_ci',(SELECT md5(string_agg(codigo||atributos_tecnicos::text,'|' ORDER BY codigo)) FROM cmdb_ci));"
}
"${compose[@]}" up -d db
ready
before=$(snapshot)
"${compose[@]}" restart db
ready
after=$(snapshot)
if [[ "$before" != "$after" ]]; then
  echo 'Persistencia CMDB fallida: los datos cambiaron al reiniciar.' >&2
  exit 1
fi
echo "Persistencia CMDB OK: $after"
