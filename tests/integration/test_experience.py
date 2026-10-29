from tests.integration import test_desk as base


class ExperienceIntegrationTest(base.DeskIntegrationTest):
    def test_ex01_portal_y_consola_aislados_en_servidor(self):
        a=self.ticket();b=self.ticket(solicitante_id=None)
        own=self.call('GET','/tickets?ambito=propios',actor='ag1').json()
        self.assertEqual(own['total'],0)
        self.call('GET',f"/tickets/{a['id']}?ambito=propios",expected=403)
        self.call('GET',f"/tickets/{a['id']}?ambito=colas")
        self.assertTrue(all(t['solicitante_id']==self.ids['sol1'] for t in self.call('GET','/tickets?ambito=propios',actor='sol1').json()['items']))
        self.assertEqual(self.call('GET','/tickets?ambito=colas',actor='sol1').json()['total'],0)
        self.assertFalse(self.call('GET','/espacios',actor='reader').json()['administracion'])
        self.assertFalse(self.call('GET','/espacios',actor='sol1').json()['consola'])
        self.assertTrue(self.call('GET','/espacios',actor='admin').json()['administracion'])

    def test_ex02_tablero_ambito_y_objetivos_capturados(self):
        queue=self.queues[0]
        payload={k:queue[k] for k in ('codigo','nombre','descripcion','proceso','activo','nivel_soporte','ordenamiento','objetivo_primera_atencion_min','objetivo_resolucion_min')}
        payload.update(responsables_ids=[],objetivo_primera_atencion_min=60,objetivo_resolucion_min=120)
        self.call('PUT',f"/colas/{queue['id']}",payload,actor='admin')
        ticket=self.ticket()
        result=self.call('GET','/tablero?ambito=propios',actor='sol2').json()
        self.assertEqual(result['total'],0)
        rows=self.call('GET','/tablero?ambito=propios&page_size=100',actor='sol1').json()['tickets']
        row=next(r for r in rows if r['ticket_id']==ticket['id'])
        self.assertEqual(row['objetivo_atencion_min'],60)
        self.assertIsNone(row['primera_atencion_min'])
        self.call('POST',f"/tickets/{ticket['id']}/tomar")
        payload['objetivo_primera_atencion_min']=1
        self.call('PUT',f"/colas/{queue['id']}",payload,actor='admin')
        result=self.call('GET','/tablero?ambito=colas&page_size=100').json()
        row=next(r for r in result['tickets'] if r['ticket_id']==ticket['id'])
        self.assertEqual(row['objetivo_atencion_min'],60)
        self.assertIsNotNone(row['primera_atencion_min'])
        self.assertEqual(result['unidad'],'minutos calendario')
        self.assertEqual(result['pausas_descontadas_min'],0)
        self.assertEqual(sum(result['por_proceso'].values()),result['total'])
        self.assertEqual(sum(result['por_prioridad'].values()),result['total'])
        self.call('POST',f"/tickets/{ticket['id']}/transferir",{'cola_id':self.queues[1]['id'],'motivo':'Segundo nivel'})
        moved=self.call('GET','/tablero?ambito=colas&page_size=100').json()
        moved=next(r for r in moved['tickets'] if r['ticket_id']==ticket['id'])
        self.assertEqual(moved['objetivo_atencion_min'],60)
        self.assertEqual(moved['primera_atencion_min'],row['primera_atencion_min'])
        self.assertEqual(self.client.get('/api/v1/desk/tablero').status_code,401)

    def test_ex03_reapertura_y_primera_atencion_por_ciclo(self):
        ticket=self.ticket();tid=ticket['id']
        self.call('POST',f'/tickets/{tid}/tomar')
        self.call('PATCH',f'/tickets/{tid}/proceso/datos',{'datos':{'categoria':'I0','interrupcion':False,'diagnostico':'Diagnóstico',
            'evidencia_recuperacion':'Recuperado','duracion_real_horas':0,'solucion':'Solución'},'motivo':'Registro'})
        for state in ['clasificacion','diagnostico','atencion','recuperado','resuelto','cerrado','abierto']:
            self.call('POST',f'/tickets/{tid}/proceso/transiciones',{'estado':state,'motivo':'Transición de prueba'})
        data=self.call('GET','/tablero?ambito=propios&page_size=100',actor='sol1').json()
        row=next(r for r in data['tickets'] if r['ticket_id']==tid)
        self.assertEqual(row['ciclo'],2);self.assertIsNone(row['primera_atencion_min']);self.assertIsNone(row['resolucion_min'])
        self.assertGreaterEqual(data['muestras_resolucion'],1);self.assertGreaterEqual(data['reaperturas_registradas'],1)
        history=self.call('GET',f'/tickets/{tid}').json()['historial']
        self.assertTrue(all(h['actor_id'] and h['fecha'] for h in history))
        self.assertTrue(any(h['accion']=='proceso' and h['antes'] and h['despues'] for h in history))
        self.call('POST',f'/tickets/{tid}/tomar')
        data=self.call('GET','/tablero?ambito=propios&page_size=100',actor='sol1').json()
        self.assertIsNotNone(next(r for r in data['tickets'] if r['ticket_id']==tid)['primera_atencion_min'])

    def test_ex04_faq_borradores_publicacion_y_autorizacion(self):
        values={'titulo':'FAQ de prueba','pregunta':'¿Cómo consultar?','respuesta':'Abre el portal','publicado':False}
        self.call('POST','/faq',values,actor='reader',expected=403)
        self.call('POST','/faq',values,actor='ag1',expected=403)
        faq=self.call('POST','/faq',values,actor='admin',expected=201).json()
        self.assertEqual(self.call('GET','/faq?search=FAQ%20de%20prueba',actor='sol1').json(),[])
        self.call('GET','/faq?administracion=true',actor='reader',expected=403)
        self.call('PUT',f"/faq/{faq['id']}",{**values,'publicado':True},actor='admin')
        items=self.call('GET','/faq?search=FAQ%20de%20prueba',actor='sol1').json()
        self.assertEqual(items[0]['id'],faq['id'])
        self.call('PUT',f"/faq/{faq['id']}",{**values,'servicio_id':999999},actor='admin',expected=409)
        self.assertEqual(self.client.get('/api/v1/desk/faq').status_code,401)

    def test_ex05_paginacion_y_filtros_no_amplian_acceso(self):
        self.ticket();self.ticket()
        data=self.call('GET','/tablero?ambito=colas&page_size=1').json()
        self.assertEqual(len(data['tickets']),1)
        self.assertGreater(data['detalle_total'],1)
        denied=self.call('GET',f"/tablero?ambito=colas&cola_id={self.queues[0]['id']}",actor='sol2').json()
        self.assertEqual(denied['total'],0)
        self.call('GET','/tablero?page_size=1000',expected=422)

    def test_ex06_migracion_no_inventa_objetivos_historicos(self):
        from pathlib import Path
        from uuid import uuid4
        from psycopg import sql
        from backend.app.database.connection import get_connection
        ticket=self.ticket()
        self.call('POST',f"/tickets/{ticket['id']}/tomar")
        # Ejecuta la migración sobre tablas temporales de otro esquema de la misma BD de pruebas.
        schema='migration_'+uuid4().hex
        with get_connection(base.base.TEST_DATABASE_URL) as connection:
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
            connection.execute(sql.SQL('SET LOCAL search_path TO {},public').format(sql.Identifier(schema)))
            connection.execute(Path('backend/db/migrations/006_pantallas_metricas.sql').read_text())
            row=connection.execute('SELECT * FROM sd_ciclos_tiempo WHERE ticket_id=%s',(ticket['id'],)).fetchone()
            self.assertEqual(row['origen'],'migracion')
            self.assertIsNone(row['objetivo_atencion_min']);self.assertIsNone(row['objetivo_resolucion_min'])
            self.assertIsNotNone(row['primera_atencion_at'])
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
