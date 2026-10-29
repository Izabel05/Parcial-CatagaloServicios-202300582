#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
export ACCEPTANCE_EVIDENCE_DIR="${ACCEPTANCE_EVIDENCE_DIR:-docs/evidencias/aceptacion-local}"
if [[ "$ACCEPTANCE_EVIDENCE_DIR" != docs/evidencias/* || "$ACCEPTANCE_EVIDENCE_DIR" == *..* ]]; then
  echo 'La salida debe estar dentro de docs/evidencias/ sin ..' >&2; exit 2
fi
mkdir -p "$ACCEPTANCE_EVIDENCE_DIR"
compose=(docker compose -p catalogo-aceptacion-tests -f compose.acceptance.yaml)
cleanup() { "${compose[@]}" down </dev/null >> "$ACCEPTANCE_EVIDENCE_DIR/cleanup.txt" 2>&1; }
trap cleanup EXIT
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  commit=$(git rev-parse HEAD)
  dirty=false
  if [[ -n "$(git status --porcelain)" ]]; then dirty=true; fi
else
  commit="${ACCEPTANCE_COMMIT:?La exportación sin .git requiere el commit base verificado}"
  dirty="${ACCEPTANCE_DIRTY:-true}"
fi
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ || ! "$dirty" =~ ^(true|false)$ ]]; then echo 'Metadatos Git inválidos' >&2; exit 2; fi
printf '%s\n' "Inicio UTC: $(date -u +%FT%TZ)" "Commit base: $commit" "Árbol modificado: $dirty" > "$ACCEPTANCE_EVIDENCE_DIR/ejecucion.txt"
"${compose[@]}" build backend-tests backend </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/build.txt" 2>&1
"${compose[@]}" up -d db --wait </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/db-start.txt" 2>&1
"${compose[@]}" run --rm --no-deps backend-tests python scripts/run_acceptance_cases.py --output /evidence/casos.json --commit "$commit" --dirty "$dirty" </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/backend-tests.txt" 2>&1
"${compose[@]}" run --rm --no-deps -v "$PWD:/workspace:ro" backend-tests python scripts/source_manifest.py --root /workspace --output /evidence/codigo.json </dev/null
"${compose[@]}" up -d backend frontend --wait </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/app-start.txt" 2>&1
"${compose[@]}" exec -T backend python scripts/check_acceptance_runtime.py </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/runtime-antes.txt"
"${compose[@]}" exec -T backend python scripts/persistence_snapshot.py --output /evidence/antes.json </dev/null
"${compose[@]}" restart db backend frontend </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/reinicio.txt" 2>&1
"${compose[@]}" up -d backend frontend --wait </dev/null >> "$ACCEPTANCE_EVIDENCE_DIR/reinicio.txt" 2>&1
"${compose[@]}" exec -T backend python scripts/check_acceptance_runtime.py </dev/null > "$ACCEPTANCE_EVIDENCE_DIR/runtime-despues.txt"
"${compose[@]}" exec -T backend python scripts/persistence_snapshot.py --output /evidence/despues.json </dev/null
"${compose[@]}" exec -T backend python scripts/finish_acceptance.py </dev/null | tee "$ACCEPTANCE_EVIDENCE_DIR/resumen.txt"
printf '%s\n' "Fin UTC: $(date -u +%FT%TZ)" >> "$ACCEPTANCE_EVIDENCE_DIR/ejecucion.txt"
# Se conservan volúmenes y reportes. Nunca down -v ni conexión a la base de demostración.
