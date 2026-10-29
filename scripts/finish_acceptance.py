"""Completa P18 únicamente cuando snapshots y arranque reales coinciden."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--directory',default='/evidence');args=parser.parse_args()
root=Path(args.directory);report=json.loads((root/'casos.json').read_text())
before=json.loads((root/'antes.json').read_text());after=json.loads((root/'despues.json').read_text())
equal=before==after
enough=before['cmdb_dispositivos']['cantidad']>=5000 and before['sd_tickets']['cantidad']>=35 and before['sd_historial']['cantidad']>0
report['escenarios']=[c for c in report['escenarios'] if c['id']!='P18']
report['escenarios'].append({'id':'P18','titulo':'Reinicio sin pérdida','comando':'bash scripts/run_acceptance.sh',
    'entrada':{'contenedores':['db','backend','frontend'],'snapshot_antes':before},
    'esperado':'Mismos conteos y checksums; catálogo, 5000 dispositivos, tickets e historial conservados; API/frontend HTTP 200',
    'obtenido':{'snapshots_iguales':equal,'datos_minimos_presentes':enough,'snapshot_despues':after,
                'http':(root/'runtime-despues.txt').read_text().strip()},
    'estado':'APROBADO' if equal and enough else 'FALLIDO','fecha':datetime.now(timezone.utc).isoformat(),
    'commit':report['commit'],'arbol_modificado':report['arbol_modificado']})
report.pop('pendiente',None);report['fin']=datetime.now(timezone.utc).isoformat()
report['resumen']={key:sum(c['estado']==key for c in report['escenarios']) for key in ('APROBADO','FALLIDO')}
(root/'casos.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
lines=['# Resultados reales P01–P18','',f"Commit base: `{report['commit']}`. Árbol modificado: {report['arbol_modificado']}.",
       'La huella del código ejecutado está en `codigo.json`; los cambios sin commit no se atribuyen al commit base.','',
       '| Caso | Fecha UTC | Esperado | Obtenido |','|---|---|---|---|']
for case in report['escenarios']:
    lines.append(f"| {case['id']} · {case['titulo']} | {case['fecha']} | {case['esperado']} | {case['estado']} |")
lines+=['','Comandos, entradas, métodos, salidas y tiempos completos en `casos.json`.',
        'P04 verifica el material disponible: C5/C6 y B4:U4. No hay árbol multinivel en el Excel y no se inventa uno.']
(root/'RESULTADOS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(report['resumen']))
if not equal or not enough or any(c['estado']!='APROBADO' for c in report['escenarios']):raise SystemExit(1)
