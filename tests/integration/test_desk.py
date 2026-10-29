import json
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from urllib.parse import urlparse
import unittest

from tests.integration import test_scenarios as base


@unittest.skipUnless(base.INTEGRATION_AVAILABLE and base.TEST_DATABASE_URL,'Requiere PostgreSQL exclusivo de pruebas')
class DeskIntegrationTest(base.ScenarioIntegrationTest):
    @classmethod
    def setUpClass(cls):
        if not urlparse(base.TEST_DATABASE_URL).path.endswith('_test'):
            raise RuntimeError('Nombre de base de pruebas debe terminar en _test')
        super().setUpClass()
        from backend.app.database.migrate import migrate
        migrate(base.TEST_DATABASE_URL)
        def login(name,password):
            response=cls.client.post('/api/v1/auth/login',json={'identifier':name,'password':password})
            assert response.status_code==200,response.text
            return {'Authorization':'Bearer '+response.json()['access_token']}
        cls.admin=login('integration-admin','Admin-Test-12345')
        cls.reader=login('integration-consulta','Consulta-Test-12345')
        cls.ids={};cls.headers={}
        for name,role in [('sol1','solicitante'),('sol2','solicitante'),('ag1','agente'),('ag2','solicitante'),('apr','aprobador')]:
            response=cls.client.post('/api/v1/usuarios',headers=cls.admin,json={'name':name,'username':'desk-'+name,
                'email':'desk-'+name+'@test.local','password':'Desk-Test-12345','role':role,'puesto_id':cls.test_position})
            assert response.status_code==201,response.text
            cls.ids[name]=response.json()['id'];cls.headers[name]=login('desk-'+name,'Desk-Test-12345')
        for name,roles in [('ag2',['agente']),('apr',['solicitante'])]:
            response=cls.client.put(f"/api/v1/desk/usuarios/{cls.ids[name]}/roles",headers=cls.admin,json={'roles':roles})
            assert response.status_code==200,response.text
        cls.queues=[]
        for code,process,level in [('SD-A','incidentes',1),('SD-B','incidentes',2),('SD-C','cambios',1)]:
            response=cls.client.post('/api/v1/desk/colas',headers=cls.admin,json={'codigo':code,'nombre':code,'proceso':process,'nivel_soporte':level})
            assert response.status_code==201,response.text
            queue=response.json();cls.queues.append(queue)
            grants=[{'rol':role,'permiso':permission} for role,permissions in
                [('agente',['consultar','atender','transferir']),('aprobador',['consultar','aprobar']),('consulta',['consultar','atender','aprobar','transferir','administrar'])]
                for permission in permissions]
            # Ag2 obtiene acceso mediante concesión directa además de su rol adicional.
            grants.extend({'usuario_id':cls.ids['ag2'],'permiso':p} for p in ['consultar','atender','transferir'])
            response=cls.client.put(f"/api/v1/desk/colas/{queue['id']}/permisos",headers=cls.admin,json={'permisos':grants})
            assert response.status_code==200,response.text
        cls.service=next(r['id'] for r in cls.client.get('/api/v1/services?page_size=100',headers=cls.admin).json()['items'] if r['active'] is True)
        classification=cls.client.post('/api/v1/cmdb/catalogos/clasificaciones',headers=cls.admin,
            json={'codigo':'SD-HW','nombre':'Hardware'}).json()['id']
        location=cls.client.post('/api/v1/cmdb/catalogos/ubicaciones',headers=cls.admin,
            json={'codigo':'SD-LOC','nombre':'Ubicación SD'}).json()['id']
        cls.ci=cls.client.post('/api/v1/cmdb/ci',headers=cls.admin,json={'codigo':'SD-CI','nombre':'CI de tickets',
            'clasificacion_id':classification,'ubicacion_id':location,'responsable_usuario_id':cls.integration_admin_id,'etiqueta':'SD-CI'}).json()['id']

    def call(self,method,path,body=None,actor='ag1',expected=200,**kwargs):
        response=self.client.request(method,'/api/v1/desk'+path,headers=self.headers.get(actor,self.admin if actor=='admin' else self.reader),
                                     **({'json':body} if body is not None else {}),**kwargs)
        self.assertEqual(response.status_code,expected,response.text)
        return response

    def ticket(self,**changes):
        values={'titulo':'Ticket '+uuid4().hex,'descripcion':'Prueba controlada','cola_id':self.queues[0]['id'],
                'servicio_id':self.service,'ci_ids':[self.ci]}
        values.update(changes)
        return self.call('POST','/tickets',values,actor='sol1',expected=201).json()

    def test_sd_08_historial_ci_filtrado_y_paginado(self):
        original=self.client.get(f'/api/v1/cmdb/ci/{self.ci}',headers=self.admin).json()
        code='AUD-CI-'+uuid4().hex
        created=self.client.post('/api/v1/cmdb/ci',headers=self.admin,json={
            'codigo':code,'nombre':'Historial CI de auditoría','etiqueta':code,
            'clasificacion_id':original['clasificacion_id'],'ubicacion_id':original['ubicacion_id'],
            'responsable_usuario_id':self.integration_admin_id})
        self.assertEqual(created.status_code,201,created.text)
        ci=created.json()['id']
        first=self.ticket(ci_ids=[ci]);second=self.ticket(ci_ids=[ci])
        self.ticket()  # Otro CI no debe entrar en el historial.
        private=self.call('POST','/colas',{'codigo':'AUD-'+uuid4().hex,'nombre':'Cola privada','proceso':'incidentes'},actor='admin',expected=201).json()
        hidden=self.call('POST','/tickets',{'titulo':'Ticket reservado','descripcion':'No visible a otras colas',
            'cola_id':private['id'],'servicio_id':self.service,'ci_ids':[ci],'solicitante_id':self.ids['sol2']},actor='admin',expected=201).json()
        url=f'/api/v1/cmdb/ci/{ci}/tickets'
        self.assertEqual(self.client.get(url).status_code,401)
        for headers in (self.headers['sol1'],self.headers['ag1'],self.reader):
            page1=self.client.get(url+'?page_size=1',headers=headers).json()
            page2=self.client.get(url+'?page_size=1&page=2',headers=headers).json()
            self.assertEqual(page1['total'],2)
            self.assertEqual({page1['items'][0]['id'],page2['items'][0]['id']},{first['id'],second['id']})
        own=self.client.get(url,headers=self.headers['sol2']).json()
        self.assertEqual([t['id'] for t in own['items']],[hidden['id']])
        self.assertEqual(self.client.get(url,headers=self.admin).json()['total'],3)
        self.assertEqual(self.client.get('/api/v1/cmdb/ci/99999999/tickets',headers=self.admin).status_code,404)

    def test_sd_09_consultar_no_materializa_flujos(self):
        from backend.app.database.connection import get_connection
        ticket=self.ticket()
        # Simula un registro heredado incompleto; la lectura no debe repararlo escribiendo.
        with get_connection(base.TEST_DATABASE_URL) as connection:
            connection.execute('DELETE FROM sd_procesos_ticket WHERE ticket_id=%s',(ticket['id'],))
        for actor in ('sol1','reader'):
            response=self.call('GET',f"/tickets/{ticket['id']}",actor=actor)
            self.assertEqual(response.json()['flujo']['estado'],'registro')
        with get_connection(base.TEST_DATABASE_URL) as connection:
            self.assertEqual(connection.execute('SELECT count(*) AS n FROM sd_procesos_ticket WHERE ticket_id=%s',(ticket['id'],)).fetchone()['n'],0)

    def test_sd_01_referencias_y_aislamiento(self):
        ticket=self.ticket()
        self.call('GET',f"/tickets/{ticket['id']}",actor='sol2',expected=403)
        listed=self.call('GET','/tickets',actor='sol2').json()
        self.assertEqual(listed['total'],0)
        detail=self.call('GET',f"/tickets/{ticket['id']}",actor='sol1').json()
        self.assertEqual(detail['ci'][0]['id'],self.ci)
        self.assertTrue(detail['level_1_code'])
        self.assertEqual(detail['tipo'],'incidente')
        self.ticket(ci_ids=[],motivo_sin_ci='Trámite sin equipo')
        bad={'titulo':'No válido','descripcion':'Datos','cola_id':self.queues[0]['id'],'servicio_id':999999,'motivo_sin_ci':'No aplica'}
        self.call('POST','/tickets',bad,actor='sol1',expected=409)
        self.call('POST','/tickets',{**bad,'servicio_id':self.service,'ci_ids':[999999]},actor='sol1',expected=409)
        self.assertEqual(self.client.get('/api/v1/desk/tickets').status_code,401)

    def test_sd_02_consulta_no_se_eleva(self):
        ticket=self.ticket()
        self.call('PUT',f'/usuarios/{self.integration_consulta_id}/roles',{'roles':['agente','aprobador','solicitante']},actor='admin')
        for operation in ['tomar']:
            self.call('POST',f"/tickets/{ticket['id']}/{operation}",actor='reader',expected=403)
        self.call('POST',f"/tickets/{ticket['id']}/comentarios",{'texto':'No autorizado'},actor='reader',expected=403)
        self.call('POST','/tickets',{'titulo':'No','descripcion':'No','cola_id':self.queues[0]['id'],
            'servicio_id':self.service,'motivo_sin_ci':'No aplica'},actor='reader',expected=403)
        self.call('DELETE',f"/colas/{self.queues[2]['id']}",actor='reader',expected=403)
        self.call('POST',f"/tickets/{ticket['id']}/aprobaciones",{'aprobado':True,'motivo':'No'},actor='reader',expected=403)

    def test_sd_03_tomar_atomico_y_orden(self):
        first=self.ticket(prioridad=4)
        urgent=self.ticket(prioridad=1)
        listed=self.call('GET',f"/tickets?cola_id={self.queues[0]['id']}&page_size=100").json()['items']
        ids=[r['id'] for r in listed];self.assertLess(ids.index(urgent['id']),ids.index(first['id']))
        barrier=threading.Barrier(2)
        def take(actor):
            barrier.wait()
            return self.client.post(f"/api/v1/desk/tickets/{urgent['id']}/tomar",headers=self.headers[actor]).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(take,['ag1','ag2']))
        self.assertEqual(sorted(statuses),[200,409])
        detail=self.call('GET',f"/tickets/{urgent['id']}").json()
        self.assertIn(detail['responsable_id'],[self.ids['ag1'],self.ids['ag2']])
        self.assertEqual(sum(h['accion']=='tomar' for h in detail['historial']),1)
        self.assertIsNotNone(detail['primera_atencion_at'])

    def test_sd_04_transferencia_escalamiento_y_bajas(self):
        ticket=self.ticket()
        self.call('POST',f"/tickets/{ticket['id']}/asignar",{'usuario_id':self.ids['ag1'],'motivo':'Asignar agente válido'})
        # Una vía antigua de administración tampoco puede dejar al ticket sin agente activo.
        response=self.client.patch(f"/api/v1/admin/users/{self.ids['ag1']}/status",headers=self.admin,json={'is_active':False})
        self.assertEqual(response.status_code,409,response.text)
        self.call('DELETE',f"/colas/{self.queues[0]['id']}",actor='admin',expected=409)
        self.call('POST',f"/tickets/{ticket['id']}/transferir",{'cola_id':self.queues[2]['id'],'motivo':'Proceso inválido'},expected=409)
        self.call('POST',f"/tickets/{ticket['id']}/escalar",{'cola_id':self.queues[1]['id'],'motivo':'Requiere soporte superior'})
        detail=self.call('GET',f"/tickets/{ticket['id']}").json()
        self.assertIsNone(detail['responsable_id']);self.assertEqual(detail['estado'],'abierto')
        self.assertIn('escalar',{h['accion'] for h in detail['historial']})
        self.call('POST',f"/tickets/{ticket['id']}/escalar",{'cola_id':self.queues[0]['id'],'motivo':'Nivel inferior'},expected=409)
        self.call('POST',f"/tickets/{ticket['id']}/transferir",{'cola_id':self.queues[0]['id'],'motivo':'Regreso a cola inicial'})

    def test_sd_05_notas_adjuntos_y_descarga(self):
        ticket=self.ticket();path=f"/tickets/{ticket['id']}"
        self.call('POST',path+'/comentarios',{'texto':'Respuesta pública'},actor='sol1',expected=201)
        self.call('POST',path+'/comentarios',{'texto':'SECRETO-NOTA','interno':True},expected=201)
        self.call('POST',path+'/comentarios',{'texto':'No puede','interno':True},actor='sol1',expected=403)
        internal=self.client.post('/api/v1/desk'+path+'/adjuntos?nombre=interno.txt&interno=true',headers={**self.headers['ag1'],'Content-Type':'text/plain'},content=b'SECRETO-ADJUNTO')
        self.assertEqual(internal.status_code,201,internal.text)
        attachment_id=internal.json()['id']
        self.call('GET',f'/adjuntos/{attachment_id}',actor='sol1',expected=403)
        downloaded=self.call('GET',f'/adjuntos/{attachment_id}')
        self.assertEqual(downloaded.content,b'SECRETO-ADJUNTO')
        self.assertEqual(downloaded.headers['x-content-type-options'],'nosniff')
        for actor in ['sol1','reader']:
            data=self.call('GET',path,actor=actor).json()
            self.assertNotIn('SECRETO',json.dumps(data))
            self.assertEqual(len(data['comentarios']),1);self.assertEqual(len(data['adjuntos']),0)
        bad=self.client.post('/api/v1/desk'+path+'/adjuntos?nombre=bad.png',headers={**self.headers['ag1'],'Content-Type':'image/png'},content=b'not-a-png')
        self.assertEqual(bad.status_code,409)
        large=self.client.post('/api/v1/desk'+path+'/adjuntos?nombre=large.txt',headers={**self.headers['ag1'],'Content-Type':'text/plain'},content=b'x'*(5242880+1))
        self.assertEqual(large.status_code,413)
        unauthorized=self.client.post('/api/v1/desk'+path+'/adjuntos?nombre=file.txt',headers={**self.headers['sol2'],'Content-Type':'text/plain'},content=b'no')
        self.assertEqual(unauthorized.status_code,403)
        public=self.client.post('/api/v1/desk'+path+'/adjuntos?nombre=publico.txt',headers={**self.headers['sol1'],'Content-Type':'text/plain'},content=b'Visible')
        self.assertEqual(public.status_code,201,public.text)
        self.assertEqual(self.call('GET',f"/adjuntos/{public.json()['id']}",actor='sol1').content,b'Visible')
        self.call('GET',f"/adjuntos/{public.json()['id']}",actor='sol2',expected=403)

    def test_sd_06_vinculos_y_rechazo_de_saltos(self):
        a,b=self.ticket(),self.ticket()
        self.call('POST',f"/tickets/{a['id']}/vinculos",{'ticket_id':b['id'],'tipo':'incidente_problema'},expected=409)
        self.call('POST',f"/tickets/{a['id']}/vinculos",{'ticket_id':b['id'],'tipo':'relacionado'},expected=201)
        detail=self.call('GET',f"/tickets/{a['id']}").json()
        self.assertEqual(detail['vinculos'][0]['otro_id'],b['id'])
        self.call('POST',f"/tickets/{a['id']}/aprobaciones",{'aprobado':True,'motivo':'Incidente no requiere aprobación'},actor='apr',expected=409)
        self.call('POST',f"/tickets/{a['id']}/tomar")
        self.call('POST',f"/tickets/{a['id']}/estado",{'estado':'resuelto','motivo':'Intento de salto','resolucion':'No basta texto'},expected=409)
        self.assertTrue(all(h['actor_id'] and h['fecha'] for h in detail['historial']))

    def test_sd_07_concesion_directa_revocacion_y_edicion(self):
        queue=self.call('POST','/colas',{'codigo':'SOLO-USUARIO','nombre':'Cola directa','proceso':'incidentes'},actor='admin',expected=201).json()
        grants=[{'usuario_id':self.ids['ag2'],'permiso':p} for p in ['consultar','atender']]
        self.call('PUT',f"/colas/{queue['id']}/permisos",{'permisos':grants},actor='admin')
        ticket=self.ticket(cola_id=queue['id'])
        self.call('GET',f"/tickets/{ticket['id']}",expected=403)
        self.call('POST',f"/tickets/{ticket['id']}/tomar",actor='ag2')
        self.call('PUT',f"/colas/{queue['id']}/permisos",{'permisos':[]},actor='admin',expected=403)
        self.call('PUT',f"/usuarios/{self.ids['ag2']}/roles",{'roles':[]},actor='admin',expected=403)
        changed=self.call('PUT',f"/tickets/{ticket['id']}",{'titulo':'Título editado','descripcion':'Información corregida',
            'servicio_id':self.service,'ci_ids':[],'motivo_sin_ci':'No aplica equipo','motivo':'Corrección validada'},actor='ag2').json()
        self.assertEqual(changed['titulo'],'Título editado')
        detail=self.call('GET',f"/tickets/{ticket['id']}",actor='ag2').json()
        self.assertEqual(detail['ci'],[])
        audit=next(h for h in detail['historial'] if h['accion']=='editar_ticket')
        self.assertEqual(audit['antes']['titulo'],ticket['titulo'])
        self.assertEqual(audit['despues']['titulo'],'Título editado')
        self.call('GET','/tickets?desde=2020-01-01T00:00:00&hasta=2030-01-01T00:00:00Z',actor='ag2')


if __name__=='__main__': unittest.main()
