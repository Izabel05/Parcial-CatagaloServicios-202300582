from concurrent.futures import ThreadPoolExecutor
from tests.integration import test_desk as base


class ProcessIntegrationTest(base.DeskIntegrationTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.process_queues={q['proceso']:q['id'] for q in cls.queues}
        for process in ['nuevos_servicios','eventos','problemas','accesos','servicios_tecnologia']:
            response=cls.client.post('/api/v1/desk/colas',headers=cls.admin,json={'codigo':'P-'+process,'nombre':process,'proceso':process})
            assert response.status_code==201,response.text
            queue=response.json()['id'];cls.process_queues[process]=queue
            grants=[{'rol':role,'permiso':permission} for role,permissions in [('agente',['consultar','atender']),('aprobador',['consultar','aprobar']),('consulta',['consultar','atender','aprobar'])] for permission in permissions]
            response=cls.client.put(f'/api/v1/desk/colas/{queue}/permisos',headers=cls.admin,json={'permisos':grants})
            assert response.status_code==200,response.text

    def new(self, process):
        ticket=self.ticket(cola_id=self.process_queues[process])
        self.call('POST',f"/tickets/{ticket['id']}/tomar")
        return ticket['id']

    def data(self, ticket, data, expected=200, actor='ag1'):
        return self.call('PATCH',f'/tickets/{ticket}/proceso/datos',{'datos':data,'motivo':'Evidencia verificada'},expected=expected,actor=actor)

    def advance(self, ticket, *states):
        for state in states:
            self.call('POST',f'/tickets/{ticket}/proceso/transiciones',{'estado':state,'motivo':'Evidencia de transición '+state})

    def reject(self, ticket, state):
        return self.call('POST',f'/tickets/{ticket}/proceso/transiciones',{'estado':state,'motivo':'Intento rechazado'},expected=409)

    def approve(self, ticket, approved=True, actor='apr', expected=201):
        return self.call('POST',f'/tickets/{ticket}/aprobaciones',{'aprobado':approved,'motivo':'Decisión independiente'},actor=actor,expected=expected)

    def change(self):
        ticket=self.new('cambios')
        self.data(ticket,{'evaluacion_impacto':'CI y servicios afectados','riesgo':'medio','plan_pruebas':'Prueba de disponibilidad','plan_reversion':'Restaurar configuración'})
        self.advance(ticket,'evaluacion','pendiente_aprobacion')
        return ticket

    def test_p01_cambio_aprobacion_pruebas_reversion_y_reapertura(self):
        ticket=self.new('cambios')
        self.reject(ticket,'ejecucion');self.advance(ticket,'evaluacion');self.reject(ticket,'pendiente_aprobacion')
        self.data(ticket,{'evaluacion_impacto':'Impacto','riesgo':'alto','plan_pruebas':'HTTP 200','plan_reversion':'Restaurar copia'})
        self.advance(ticket,'pendiente_aprobacion');self.reject(ticket,'aprobado');self.reject(ticket,'ejecucion')
        self.approve(ticket)
        self.data(ticket,{'plan_reversion':'Cambiar después de aprobar'},expected=409)
        self.advance(ticket,'planificacion');self.reject(ticket,'ejecucion')
        self.data(ticket,{'programado_para':'2030-01-01T12:00:00Z'})
        self.advance(ticket,'ejecucion');self.reject(ticket,'validacion')
        self.data(ticket,{'resultado_ejecucion':'Aplicado','resultado_pruebas':'HTTP 200'})
        self.advance(ticket,'validacion');self.reject(ticket,'resuelto')
        self.data(ticket,{'validacion':'Servicio verificado'})
        self.advance(ticket,'resuelto','cerrado','abierto')
        flow=self.call('GET',f'/tickets/{ticket}').json()['flujo']
        self.assertEqual(flow['version'],2);self.assertEqual(flow['estado'],'solicitud')
        self.reject(ticket,'ejecucion')
        self.call('POST',f'/tickets/{ticket}/tomar')
        self.advance(ticket,'evaluacion','pendiente_aprobacion')
        self.reject(ticket,'planificacion')
        self.approve(ticket,False);self.reject(ticket,'ejecucion');self.advance(ticket,'cerrado')

    def test_p02_nuevo_servicio_sin_duplicados(self):
        ticket=self.new('nuevos_servicios')
        body={'servicio_id':self.service,'motivo':'Servicio existente'}
        self.call('POST',f'/tickets/{ticket}/proceso/servicio',body,expected=409)
        self.reject(ticket,'analisis')
        self.data(ticket,{'necesidad':'Nueva necesidad','analisis_viabilidad':'Capacidad disponible','viable':True,'plan_implementacion':'Configurar servicio'})
        self.advance(ticket,'analisis','pendiente_aprobacion');self.approve(ticket)
        first=self.call('POST',f'/tickets/{ticket}/proceso/servicio',body).json()
        second=self.call('POST',f'/tickets/{ticket}/proceso/servicio',body).json()
        self.assertEqual(first['servicio_resultado_id'],second['servicio_resultado_id'])
        self.advance(ticket,'implementacion');self.reject(ticket,'validacion')
        self.data(ticket,{'evidencia_implementacion':'Publicado','validacion':'Aceptación'})
        self.advance(ticket,'validacion','resuelto','cerrado')

    def test_p03_incidentes_categorias_y_evidencias(self):
        from backend.app.services.process_rules import incident_suggestion
        for duration,category in [(3,'I1'),(8,'I2'),(48,'I3'),(168,'I4'),(169,'I5'),(720,'I5')]:
            self.assertEqual(incident_suggestion({'interrupcion':True,'duracion_estimada_horas':duration}),category)
        for category in ['I0','I1','I2','I3','I4','I5','I6']:
            ticket=self.new('incidentes');self.advance(ticket,'clasificacion');self.reject(ticket,'diagnostico')
            self.data(ticket,{'categoria':category,'interrupcion':category!='I0','seguridad':category=='I6',
                'redundancia_disponible':category=='I0',
                'duracion_estimada_horas':{'I0':0,'I1':2,'I2':7,'I3':24,'I4':72,'I5':800,'I6':1}[category]})
            self.advance(ticket,'diagnostico');self.reject(ticket,'atencion')
            detail=self.call('GET',f'/tickets/{ticket}').json()
            self.assertEqual(detail['prioridad'],{'I0':4,'I1':3,'I2':3,'I3':1,'I4':1,'I5':1,'I6':1}[category])
            self.assertEqual(detail['flujo']['datos']['redundancia_disponible'],category=='I0')
            self.data(ticket,{'diagnostico':'Causa identificada'})
            self.advance(ticket,'atencion');self.reject(ticket,'recuperado')
            self.data(ticket,{'evidencia_recuperacion':'Monitor disponible','duracion_real_horas':0,'solucion':'Corrección aplicada'})
            self.advance(ticket,'recuperado','resuelto','cerrado')
            self.data(ticket,{'solucion':'Alteración posterior'},expected=409)

    def test_p04_eventos_idempotentes_y_cola_correcta(self):
        for category in ['E0','E1','E2','E3']:
            ticket=self.new('eventos')
            self.data(ticket,{'categoria':category,'evaluacion':'Evaluación del umbral','cola_incidente_id':self.process_queues['cambios']})
            self.advance(ticket,'clasificacion','evaluacion')
            if category in ('E0','E1'):
                self.call('POST',f'/tickets/{ticket}/proceso/incidente',expected=409)
            else:
                self.call('POST',f'/tickets/{ticket}/proceso/incidente',expected=409)
                self.data(ticket,{'cola_incidente_id':self.process_queues['incidentes']})
                def generate(_):
                    response=self.client.post(f'/api/v1/desk/tickets/{ticket}/proceso/incidente',headers=self.headers['ag1'])
                    return response.status_code,response.json()
                with ThreadPoolExecutor(max_workers=2) as executor: results=list(executor.map(generate,range(2)))
                self.assertEqual([r[0] for r in results],[200,200])
                self.assertEqual(results[0][1]['incidente_id'],results[1][1]['incidente_id'])
                self.data(ticket,{'categoria':'E0'},expected=409)
                incident=self.call('GET',f"/tickets/{results[0][1]['incidente_id']}").json()
                self.assertEqual(incident['proceso'],'incidentes')
                self.assertNotIn('seguridad',incident['flujo']['datos'])
            self.advance(ticket,'respondido')
            self.data(ticket,{'categoria':'E2' if category in ('E0','E1') else 'E0'},expected=409)
            self.advance(ticket,'resuelto','cerrado')

    def test_p05_evento_vincula_incidente_existente(self):
        incident=self.new('incidentes');event=self.new('eventos')
        self.data(event,{'categoria':'E2','evaluacion':'Coincide con incidente activo','incidente_id':incident})
        self.advance(event,'clasificacion','evaluacion','respondido')
        result=self.call('POST',f'/tickets/{event}/proceso/incidente').json()
        self.assertEqual(result['incidente_id'],incident)

    def test_p06_problema_causa_raiz_y_cambio(self):
        ticket=self.new('problemas');self.reject(ticket,'investigacion')
        incident=self.new('incidentes');change=self.change()
        self.data(ticket,{'incidentes_ids':[change]},expected=409)
        self.data(ticket,{'incidentes_ids':[incident]});self.advance(ticket,'investigacion')
        self.reject(ticket,'error_conocido')
        self.data(ticket,{'causa_raiz':'Configuración','solucion_temporal':'Reinicio','error_conocido':True})
        self.advance(ticket,'error_conocido')
        self.data(ticket,{'solucion_definitiva':'Actualizar'})
        self.reject(ticket,'solucion_definitiva')
        self.data(ticket,{'cambio_correctivo_id':change})
        self.advance(ticket,'solucion_definitiva');self.reject(ticket,'resuelto')
        self.approve(change);self.advance(change,'planificacion')
        self.data(change,{'programado_para':'2030-01-01T00:00:00Z','resultado_ejecucion':'Aplicado','resultado_pruebas':'Correctas','validacion':'Estable'})
        self.advance(change,'ejecucion','validacion','resuelto')
        self.advance(ticket,'resuelto','cerrado')
        links=self.call('GET',f'/tickets/{ticket}').json()['vinculos']
        self.assertEqual({link['tipo'] for link in links},{'incidente_problema','problema_cambio'})

    def test_p07_acceso_impide_autoaprobacion_beneficiario(self):
        ticket=self.new('accesos')
        self.data(ticket,{'beneficiario_id':self.ids['apr'],'recurso':'VPN','permiso_solicitado':'Conectar','validacion_solicitud':'Jefatura validada'})
        self.advance(ticket,'validacion','pendiente_aprobacion')
        self.approve(ticket,actor='apr',expected=403)
        self.approve(ticket,actor='admin')
        self.data(ticket,{'beneficiario_id':self.ids['sol2']},expected=409)
        self.advance(ticket,'provision');self.reject(ticket,'verificacion')
        self.data(ticket,{'evidencia_provision':'Permiso asignado'})
        self.advance(ticket,'verificacion');self.reject(ticket,'resuelto')
        self.data(ticket,{'validacion':'Acceso comprobado'})
        self.advance(ticket,'resuelto','cerrado')

    def test_p08_tecnologia_solo_solicitante_confirma(self):
        ticket=self.new('servicios_tecnologia')
        self.advance(ticket,'validacion');self.reject(ticket,'asignacion')
        self.data(ticket,{'detalle_solicitud':'Instalar cliente del servicio','validacion':'Servicio vigente'})
        self.advance(ticket,'asignacion','cumplimiento');self.reject(ticket,'confirmacion')
        self.data(ticket,{'evidencia_cumplimiento':'Cliente instalado'})
        self.advance(ticket,'confirmacion');self.reject(ticket,'resuelto')
        self.data(ticket,{'confirmacion':'Falsificada'},expected=409)
        self.call('POST',f'/tickets/{ticket}/proceso/confirmacion',{'texto':'Agente'},expected=403)
        self.call('POST',f'/tickets/{ticket}/proceso/confirmacion',{'texto':'Acepto'},actor='sol1')
        self.advance(ticket,'cerrado')

    def test_p09_consulta_bloqueada_en_todas_operaciones(self):
        ticket=self.new('accesos')
        self.data(ticket,{'recurso':'No autorizado'},actor='reader',expected=403)
        for path,body in [('transiciones',{'estado':'validacion','motivo':'Intento'}),('incidente',None),('servicio',{'servicio_id':self.service,'motivo':'Intento'}),('confirmacion',{'texto':'Intento'})]:
            self.call('POST',f'/tickets/{ticket}/proceso/{path}',body,actor='reader',expected=403)

    def test_p10_creacion_catalogo_y_reintento(self):
        ticket=self.new('nuevos_servicios')
        self.data(ticket,{'necesidad':'Servicio nuevo','analisis_viabilidad':'Apto','viable':True,'plan_implementacion':'Publicar'})
        self.advance(ticket,'analisis','pendiente_aprobacion');self.approve(ticket)
        options=self.client.get('/api/v1/services/catalog-options',headers=self.admin).json()
        level=self.client.get('/api/v1/services/level-1',headers=self.admin).json()[0]['code']
        new={'code':'PROCESO-NUEVO','name':'Servicio de proceso','level_1_code':level,
            'service_class_id':options['service_classes'][0]['id'],'criticality_id':options['criticalities'][0]['id'],
            'service_type_id':options['service_types'][0]['id'],'responsible_section_id':self.test_section}
        body={'nuevo':new,'motivo':'Publicación aprobada'}
        first=self.call('POST',f'/tickets/{ticket}/proceso/servicio',body).json()
        second=self.call('POST',f'/tickets/{ticket}/proceso/servicio',body).json()
        self.assertEqual(first['servicio_resultado_id'],second['servicio_resultado_id'])
        result=self.client.get('/api/v1/services?search=PROCESO-NUEVO',headers=self.admin).json()
        self.assertEqual(result['total'],1)
        self.call('POST',f'/tickets/{ticket}/proceso/servicio',{'nuevo':{**new,'name':'Otro nombre'},'motivo':'Conflicto'},expected=409)

    def test_p11_categoria_justificada_y_creador_no_aprueba(self):
        ticket=self.new('incidentes')
        self.data(ticket,{'categoria':'I2','interrupcion':True,'duracion_estimada_horas':1})
        self.advance(ticket,'clasificacion');self.reject(ticket,'diagnostico')
        self.data(ticket,{'justificacion_categoria':'Impacto adicional confirmado'})
        self.advance(ticket,'diagnostico')
        self.data(ticket,{'categoria':'I6'},expected=409)
        self.data(ticket,{'campo_inventado':'No admitido'},expected=409)
        own=self.call('POST','/tickets',{'titulo':'Cambio propio','descripcion':'Separación de funciones',
            'cola_id':self.process_queues['cambios'],'servicio_id':self.service,'ci_ids':[self.ci]},actor='admin',expected=201).json()['id']
        self.call('POST',f'/tickets/{own}/tomar')
        self.data(own,{'evaluacion_impacto':'Impacto','riesgo':'bajo','plan_pruebas':'Pruebas','plan_reversion':'Reversión'})
        self.advance(own,'evaluacion','pendiente_aprobacion')
        self.approve(own,actor='admin',expected=403)
        self.approve(own)
