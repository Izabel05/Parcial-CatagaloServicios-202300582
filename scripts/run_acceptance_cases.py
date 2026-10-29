"""Ejecuta pruebas reales y emite la matriz P01–P17; P18 lo completa el harness Docker."""
import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import platform
import re
import sys
import time
import unittest
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records={}

    def startTest(self,test):
        super().startTest(test);self.started=time.perf_counter();self.output=io.StringIO()
        self.redirect=contextlib.redirect_stdout(self.output);self.redirect.__enter__()
        self.records[test.id()]={'estado':'EN_EJECUCION','inicio':datetime.now(timezone.utc).isoformat()}

    def addSuccess(self,test):
        super().addSuccess(test);self.records[test.id()]['estado']='APROBADO'

    def addFailure(self,test,error):
        super().addFailure(test,error);self.records[test.id()]['estado']='FALLIDO'

    def addError(self,test,error):
        super().addError(test,error)
        self.records.setdefault(test.id(),{})['estado']='ERROR'

    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.records.setdefault(test.id(),{}).update(estado='OMITIDO',motivo=reason)

    def stopTest(self,test):
        self.redirect.__exit__(None,None,None)
        self.records[test.id()].update(segundos=round(time.perf_counter()-self.started,6),salida=self.output.getvalue())
        super().stopTest(test)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--commit',required=True)
    parser.add_argument('--dirty',choices=['true','false'],required=True)
    args=parser.parse_args()
    database=os.getenv('TEST_DATABASE_URL','')
    if not urlparse(database).path.endswith('_test'): raise SystemExit('TEST_DATABASE_URL debe terminar en _test; se rechaza la ejecución')
    if not re.fullmatch('[0-9a-f]{40}',args.commit): raise SystemExit('Commit inválido')
    from tests.acceptance.matrix import MODULES,SCENARIOS
    started=datetime.now(timezone.utc).isoformat()
    suite=unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult).run(suite)
    command=f'python scripts/run_acceptance_cases.py --output {args.output} --commit {args.commit} --dirty {args.dirty}'
    cases=[]
    for code,title,inputs,expected,methods in SCENARIOS:
        observations=[{'metodo':m,**result.records.get(m,{'estado':'NO_EJECUTADO'})} for m in methods]
        passed=all(r['estado']=='APROBADO' for r in observations)
        entry={'id':code,'titulo':title,'comando':command,'entrada':inputs,'esperado':expected,
               'obtenido':observations,'estado':'APROBADO' if passed else 'FALLIDO',
               'fecha':datetime.now(timezone.utc).isoformat(),'commit':args.commit,'arbol_modificado':args.dirty=='true'}
        if code=='P04':entry['limitacion']='El Excel disponible no contiene un árbol multinivel; se verifica C5/C6 y no se atribuyen niveles inexistentes a la lección 22.'
        cases.append(entry)
    report={'inicio':started,'fin_backend':datetime.now(timezone.utc).isoformat(),'commit':args.commit,'arbol_modificado':args.dirty=='true',
            'entorno':{'python':platform.python_version(),'sistema':platform.platform(),'base':urlparse(database).path[1:]},
            'metodos_ejecutados':result.testsRun,'fallos':len(result.failures),'errores':len(result.errors),'omisiones':len(result.skipped),
            'metodos':result.records,'escenarios':cases,'pendiente':'P18: reinicio de contenedores mediante scripts/run_acceptance.sh'}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return 0 if result.wasSuccessful() and not result.skipped and all(c['estado']=='APROBADO' for c in cases) else 1


if __name__=='__main__':sys.exit(main())
