from datetime import datetime, timedelta, timezone
import unittest
from backend.app.services.desk_metrics import calculate, objective


class MetricsTest(unittest.TestCase):
    def row(self, **values):
        now=datetime(2026,10,28,tzinfo=timezone.utc)
        row=dict(ticket_id=1,ticket_numero='SD-1',titulo='Prueba',estado='en_atencion',proceso='incidentes',prioridad=3,cola_id=1,cola_nombre='Incidentes',
                 created_at=now-timedelta(minutes=120),inicio_at=now-timedelta(minutes=60),numero=1,actual=True,origen='nativo',
                 primera_atencion_at=None,resuelto_at=None,cerrado_at=None,objetivo_atencion_min=30,objetivo_resolucion_min=60)
        return {**row,**values},now

    def test_limites_y_no_objetivo(self):
        self.assertEqual(objective(30,30,True),'cumplido')
        self.assertEqual(objective(30,30,False),'pendiente')
        self.assertEqual(objective(30.01,30,False),'vencido')
        self.assertEqual(objective(30.01,30,True),'incumplido')
        self.assertEqual(objective(999,None,True),'sin_objetivo')

    def test_pendientes_no_son_cero_y_pausas_no_descontadas(self):
        row,now=self.row();result=calculate([row],now)
        self.assertIsNone(result['promedio_primera_atencion_min'])
        self.assertIsNone(result['promedio_resolucion_min'])
        self.assertEqual(result['tickets'][0]['tiempo_ciclo_min'],60)
        self.assertEqual(result['pausas_descontadas_min'],0)
        self.assertEqual(result['objetivos_atencion']['vencido'],1)

    def test_reapertura_conserva_ciclo_anterior_sin_duplicar_tickets(self):
        old,now=self.row(actual=False,estado='abierto')
        old['primera_atencion_at']=old['inicio_at']+timedelta(minutes=5)
        old['resuelto_at']=old['inicio_at']+timedelta(minutes=20)
        new={**old,'numero':2,'actual':True,'inicio_at':now-timedelta(minutes=10),'primera_atencion_at':None,'resuelto_at':None}
        result=calculate([old,new],now)
        self.assertEqual(result['total'],1);self.assertEqual(result['ciclos'],2)
        self.assertEqual(result['reaperturas_registradas'],1)
        self.assertEqual(result['promedio_resolucion_min'],20)
        self.assertEqual(result['promedio_primera_atencion_min'],5)
        self.assertEqual(result['tickets'][0]['tiempo_ciclo_min'],10)

    def test_cierre_sin_resolucion_no_es_solucion(self):
        row,now=self.row(estado='cerrado',cerrado_at=datetime(2026,10,28,tzinfo=timezone.utc))
        result=calculate([row],now)
        self.assertEqual(result['objetivos_resolucion']['no_aplica'],1)
        self.assertIsNone(result['promedio_resolucion_min'])
