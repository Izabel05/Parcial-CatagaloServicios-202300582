from datetime import datetime, timezone
from pydantic import ValidationError

from backend.app.repositories.process_repository import ProcessRepository
from backend.app.schemas.process_schema import SCHEMAS
from backend.app.services.process_rules import INITIAL, PATHS, APPROVAL_PROCESSES, OUTPUTS, successors, incident_suggestion, INCIDENT_PRIORITY
from backend.app.services.desk_service import DeskService, DeskError, DeskDenied


class ProcessService:
    def __init__(self, desk=None):
        self.desk = desk or DeskService()

    def context(self, repo, actor, ticket_id, permission='atender'):
        user = self.desk.user(repo,actor)
        ticket = self.desk.writable(repo,user,ticket_id,permission)
        process = self.desk.get(repo,'cola',ticket['cola_id'])['proceso']
        store = ProcessRepository(repo.connection)
        flow = store.get(ticket_id,INITIAL[process])
        return user,ticket,process,store,flow

    @staticmethod
    def required(data, *fields):
        missing = [field for field in fields if data.get(field) is None or data.get(field)==[] or isinstance(data.get(field),str) and not data[field].strip()]
        if missing:
            raise DeskError('Complete: '+', '.join(missing))

    @staticmethod
    def assigned(ticket):
        if not ticket['responsable_id'] or ticket['estado']!='en_atencion':
            raise DeskError('Asigne o tome el ticket antes de avanzar')

    def persist(self, repo, store, flow, actor, state, data, reason, version=None, service_id=None):
        after = store.update(flow['ticket_id'],state,data,version or flow['version'],
                             service_id if service_id is not None else flow['servicio_resultado_id'])
        repo.audit(actor,'proceso',flow,{**after,'motivo':reason},ticket_id=flow['ticket_id'])
        return after

    def patch(self, actor, ticket_id, data, reason):
        with self.desk.repository.transaction(True) as repo:
            user,ticket,process,store,flow = self.context(repo,actor,ticket_id)
            if ticket['estado'] in ('resuelto','cerrado') or flow['estado']=='rechazado':
                raise DeskError('Reabra el proceso antes de modificar sus datos')
            if 'confirmacion' in data:
                raise DeskError('La confirmación pertenece al solicitante y usa su operación específica')
            if any(value is None or isinstance(value,str) and not value.strip() or value==[] for key,value in data.items() if flow['datos'].get(key) not in (None,'',[])):
                raise DeskError('No se puede borrar una evidencia registrada; reabra el proceso para corregirla')
            if process=='incidentes' and flow['estado'] not in ('registro','clasificacion'):
                classification={'categoria','interrupcion','degradacion','seguridad','duracion_estimada_horas','justificacion_categoria'}
                if any(key in classification and value!=flow['datos'].get(key) for key,value in data.items()):
                    raise DeskError('La clasificación ya fue registrada; reabra el incidente para reclasificarlo')
            # La aprobación cubre los datos previos; quedan congelados al enviarlos.
            frozen = {
                'nuevos_servicios':{'necesidad','analisis_viabilidad','viable','plan_implementacion'},
                'cambios':{'evaluacion_impacto','riesgo','plan_pruebas','plan_reversion'},
                'accesos':{'beneficiario_id','recurso','permiso_solicitado','accion','validacion_solicitud'},
            }
            if process in frozen and (flow['estado'] in ('pendiente_aprobacion','rechazado') or store.approval(ticket_id,flow['version'])):
                if any(key in frozen[process] and value!=flow['datos'].get(key) for key,value in data.items()):
                    raise DeskError('Los datos sometidos a aprobación están congelados; reabra para cambiarlos')
            if process=='eventos' and store.event_incident(ticket_id) and any(
                    key in data and data[key]!=flow['datos'].get(key) for key in ('categoria','incidente_id','cola_incidente_id')):
                raise DeskError('El evento ya tiene un incidente; no puede cambiar su correlación')
            if process=='eventos' and flow['estado']=='respondido' and data.get('categoria',flow['datos'].get('categoria'))!=flow['datos'].get('categoria'):
                raise DeskError('El evento ya fue respondido; reabra para reclasificarlo')
            try:
                clean = SCHEMAS[process].model_validate({**flow['datos'],**data}).model_dump(mode='json')
            except ValidationError as error:
                raise DeskError(str(error)) from error
            if process=='accesos' and clean.get('beneficiario_id'):
                self.desk.user(repo,clean['beneficiario_id'])
            if process=='problemas':
                for incident in clean['incidentes_ids']:
                    self.related(repo,user,incident,'incidentes')
                if clean.get('cambio_correctivo_id'):
                    self.related(repo,user,clean['cambio_correctivo_id'],'cambios')
            return self.persist(repo,store,flow,actor,flow['estado'],clean,reason)

    def related(self, repo, user, ticket_id, process):
        ticket = self.desk.readable(repo,user,ticket_id)
        if self.desk.get(repo,'cola',ticket['cola_id'])['proceso']!=process:
            raise DeskError('El ticket relacionado debe pertenecer al proceso '+process)
        return ticket

    def guard(self, repo, user, ticket, process, store, flow, target):
        data = flow['datos']
        if target=='resuelto':
            final_fields={
                'nuevos_servicios':('evidencia_implementacion','validacion'),
                'cambios':('resultado_ejecucion','resultado_pruebas','validacion'),
                'incidentes':('categoria','diagnostico','evidencia_recuperacion','duracion_real_horas','solucion'),
                'eventos':('categoria',),
                'problemas':('incidentes_ids','causa_raiz','solucion_definitiva'),
                'accesos':('beneficiario_id','permiso_solicitado','evidencia_provision','validacion'),
                'servicios_tecnologia':('evidencia_cumplimiento',),
            }
            self.required(data,*final_fields[process])
        if target in ('aprobado','rechazado'):
            raise DeskError('Use la operación de aprobación con un aprobador independiente')
        if process=='nuevos_servicios':
            if target=='analisis': self.required(data,'necesidad')
            if target=='pendiente_aprobacion':
                self.required(data,'analisis_viabilidad','viable','plan_implementacion')
                if data['viable'] is not True: raise DeskError('El servicio no es viable')
            if target=='implementacion' and not flow['servicio_resultado_id']:
                raise DeskError('Cree o vincule el servicio aprobado antes de implementarlo')
            if target=='validacion': self.required(data,'evidencia_implementacion')
            if target=='resuelto': self.required(data,'validacion')
        elif process=='cambios':
            if target=='pendiente_aprobacion':
                self.required(data,'evaluacion_impacto','riesgo','plan_pruebas','plan_reversion')
                if not repo.cis(ticket['id']): raise DeskError('El cambio debe identificar al menos un CI')
            if target=='ejecucion':
                self.required(data,'programado_para','plan_pruebas','plan_reversion')
                approval=store.approval(ticket['id'],flow['version'])
                if not approval or not approval['aprobado']: raise DeskError('El cambio requiere aprobación vigente')
            if target=='validacion': self.required(data,'resultado_ejecucion','resultado_pruebas')
            if target=='resuelto': self.required(data,'validacion')
        elif process=='incidentes':
            if target=='diagnostico':
                self.required(data,'categoria','interrupcion')
                suggestion=incident_suggestion(data)
                if suggestion is None: raise DeskError('Indique duración estimada o incidente de seguridad')
                if data['categoria']!=suggestion and not (data.get('justificacion_categoria') or '').strip():
                    raise DeskError('La categoría difiere de la duración/condición; justifíquela')
                if data['categoria']=='I6' and not data.get('seguridad'): raise DeskError('I6 requiere seguridad')
                if data['categoria']=='I0' and (data['interrupcion'] or data.get('degradacion') or data.get('seguridad')):
                    raise DeskError('I0 requiere ausencia de interrupción, degradación y seguridad')
                repo.save('ticket',{'prioridad':INCIDENT_PRIORITY[data['categoria']]},ticket['id'])
            if target=='atencion': self.required(data,'diagnostico')
            if target=='recuperado': self.required(data,'evidencia_recuperacion','duracion_real_horas')
            if target=='resuelto': self.required(data,'solucion')
        elif process=='eventos':
            if target=='resuelto' and data.get('categoria') in ('E2','E3') and not store.event_incident(ticket['id']):
                raise DeskError('E2/E3 requieren un incidente correlacionado')
            if target=='evaluacion': self.required(data,'categoria')
            if target=='respondido':
                self.required(data,'categoria')
                if data['categoria']!='E0': self.required(data,'evaluacion')
                if data['categoria'] in ('E2','E3'):
                    self.event_in_transaction(repo,user,ticket,store,flow)
        elif process=='problemas':
            if target in ('investigacion','error_conocido','solucion_definitiva','resuelto'):
                self.required(data,'incidentes_ids')
                for incident in data['incidentes_ids']:
                    self.related(repo,user,incident,'incidentes')
                    store.link(incident,ticket['id'],'incidente_problema')
            if target=='error_conocido':
                self.required(data,'causa_raiz','solucion_temporal')
                if data.get('error_conocido') is not True: raise DeskError('Identifique el error conocido')
            if target in ('solucion_definitiva','resuelto'):
                self.required(data,'causa_raiz','solucion_definitiva','cambio_correctivo_id')
                change=self.related(repo,user,data['cambio_correctivo_id'],'cambios')
                store.link(ticket['id'],change['id'],'problema_cambio')
                if target=='resuelto' and change['estado'] not in ('resuelto','cerrado'):
                    raise DeskError('El cambio correctivo debe estar resuelto')
        elif process=='accesos':
            if target=='pendiente_aprobacion':
                self.required(data,'beneficiario_id','recurso','permiso_solicitado','validacion_solicitud')
                self.desk.user(repo,data['beneficiario_id'])
            if target=='verificacion': self.required(data,'evidencia_provision')
            if target=='resuelto': self.required(data,'validacion')
        elif process=='servicios_tecnologia':
            service=repo.reference('servicio',ticket['servicio_id'])
            if not service or not service['active'] or not service['nivel1_activo']:
                raise DeskError('La solicitud requiere un servicio existente y activo')
            if target=='asignacion': self.required(data,'detalle_solicitud','validacion')
            if target=='confirmacion': self.required(data,'evidencia_cumplimiento')
            if target=='resuelto': raise DeskError('El solicitante debe confirmar el cumplimiento')
        if process in APPROVAL_PROCESSES and target not in ('solicitud','analisis','evaluacion','validacion','pendiente_aprobacion','cerrado'):
            approval=store.approval(ticket['id'],flow['version'])
            if not approval or not approval['aprobado']: raise DeskError('Se requiere aprobación vigente')

    def transition(self, actor, ticket_id, target, reason):
        with self.desk.repository.transaction(True) as repo:
            user,ticket,process,store,flow=self.context(repo,actor,ticket_id)
            if target in ('abierto','en_atencion') and ticket['estado'] in ('resuelto','cerrado'):
                data={key:value for key,value in flow['datos'].items() if key not in OUTPUTS}
                repo.save('ticket',{'estado':'abierto','responsable_id':None,'resolucion':None,
                    'resuelto_at':None,'cerrado_at':None,'updated_at':datetime.now(timezone.utc)},ticket_id)
                from backend.app.repositories.experience_repository import ExperienceRepository
                ExperienceRepository(repo.connection).begin_cycle(ticket,flow['version']+1)
                return self.persist(repo,store,flow,actor,INITIAL[process],data,reason,flow['version']+1)
            if target not in successors(process,flow['estado']):
                raise DeskError('Transición no permitida: '+flow['estado']+' → '+target)
            if target!='cerrado': self.assigned(ticket)
            self.guard(repo,user,ticket,process,store,flow,target)
            if target in ('resuelto','cerrado'):
                self.finish(repo,ticket_id,target,reason)
            return self.persist(repo,store,flow,actor,target,flow['datos'],reason)

    @staticmethod
    def finish(repo, ticket_id, target, reason):
        from backend.app.repositories.experience_repository import ExperienceRepository
        ExperienceRepository(repo.connection).finish_cycle(ticket_id,target)
        repo.save('ticket',{'estado':target,'resolucion':reason,
            'resuelto_at' if target=='resuelto' else 'cerrado_at':datetime.now(timezone.utc),
            'updated_at':datetime.now(timezone.utc)},ticket_id)

    def approval(self, actor, ticket_id, approved, reason):
        with self.desk.repository.transaction(True) as repo:
            user,ticket,process,store,flow=self.context(repo,actor,ticket_id,'aprobar')
            if process not in APPROVAL_PROCESSES or flow['estado']!='pendiente_aprobacion':
                raise DeskError('Este proceso no espera aprobación')
            if actor in (ticket['solicitante_id'],ticket['creador_id'],flow['datos'].get('beneficiario_id')):
                raise DeskDenied('El solicitante, creador o beneficiario no puede autoaprobar')
            result=repo.save('aprobacion',{'ticket_id':ticket_id,'actor_id':actor,'aprobado':approved,
                'motivo':reason,'version_proceso':flow['version']})
            repo.audit(actor,'aprobacion',None,result,ticket_id=ticket_id)
            self.persist(repo,store,flow,actor,'aprobado' if approved else 'rechazado',flow['datos'],reason)
            return result

    def event_in_transaction(self, repo, user, ticket, store, flow):
        if store.event_incident(ticket['id']): return store.event_incident(ticket['id'])
        data=flow['datos']
        if data.get('categoria') not in ('E2','E3'): raise DeskError('Solo E2/E3 generan o vinculan incidentes')
        self.required(data,'evaluacion')
        if data.get('incidente_id'):
            incident=self.related(repo,user,data['incidente_id'],'incidentes')
            if incident['servicio_id']!=ticket['servicio_id']: raise DeskError('El incidente debe corresponder al mismo servicio')
        else:
            self.required(data,'cola_incidente_id')
            queue=self.desk.get(repo,'cola',data['cola_incidente_id'])
            if not queue['activo'] or queue['proceso']!='incidentes': raise DeskError('Seleccione una cola activa de incidentes')
            self.desk.allow(repo,user,queue['id'],'atender')
            incident=repo.save('ticket',{'titulo':'Incidente de '+ticket['numero'],'descripcion':ticket['descripcion'],
                'solicitante_id':ticket['solicitante_id'],'creador_id':user['id'],'servicio_id':ticket['servicio_id'],
                'cola_id':queue['id'],'prioridad':1 if data['categoria']=='E3' else ticket['prioridad'],
                'motivo_sin_ci':ticket['motivo_sin_ci']})
            repo.replace_ci(incident['id'],[ci['id'] for ci in repo.cis(ticket['id'])])
            store.get(incident['id'],'registro')
            from backend.app.repositories.experience_repository import ExperienceRepository
            ExperienceRepository(repo.connection).begin_cycle(incident)
            repo.audit(user['id'],'crear_incidente_evento',None,incident,ticket_id=incident['id'])
        store.register_event(ticket['id'],incident['id'],user['id'])
        result=store.event_incident(ticket['id'])
        repo.audit(user['id'],'correlacionar_evento',None,result,ticket_id=ticket['id'])
        return result

    def event(self, actor, ticket_id):
        with self.desk.repository.transaction(True) as repo:
            user,ticket,process,store,flow=self.context(repo,actor,ticket_id)
            if process!='eventos': raise DeskError('El ticket no es un evento')
            if store.event_incident(ticket_id): return store.event_incident(ticket_id)
            self.assigned(ticket)
            if flow['estado']!='evaluacion': raise DeskError('Evalúe el evento antes de responder')
            return self.event_in_transaction(repo,user,ticket,store,flow)

    def confirm(self, actor, ticket_id, text):
        with self.desk.repository.transaction(True) as repo:
            user=self.desk.user(repo,actor)
            ticket=self.desk.readable(repo,user,ticket_id,True)
            if user['role']=='consulta' or actor!=ticket['solicitante_id']:
                raise DeskDenied('Solo el solicitante puede confirmar el cumplimiento')
            process=self.desk.get(repo,'cola',ticket['cola_id'])['proceso']
            store=ProcessRepository(repo.connection);flow=store.get(ticket_id,INITIAL[process])
            if process!='servicios_tecnologia' or flow['estado']!='confirmacion':
                raise DeskError('El servicio no espera confirmación')
            self.assigned(ticket)
            if not self.desk.get(repo,'cola',ticket['cola_id'])['activo']:
                raise DeskError('La cola está inactiva')
            self.required(flow['datos'],'evidencia_cumplimiento')
            self.finish(repo,ticket_id,'resuelto',text)
            return self.persist(repo,store,flow,actor,'resuelto',{**flow['datos'],'confirmacion':text},text)

    def publish(self, actor, ticket_id, service_id, new, reason):
        from backend.app.repositories.service_repository import ServiceRepository
        from backend.app.services.service_service import ServiceService, ServiceOperationError
        with self.desk.repository.transaction(True) as repo:
            user,ticket,process,store,flow=self.context(repo,actor,ticket_id)
            if process!='nuevos_servicios' or flow['estado'] not in ('aprobado','implementacion','validacion','resuelto','cerrado'):
                raise DeskError('Primero debe aprobarse el nuevo servicio')
            approval=store.approval(ticket_id,flow['version'])
            if not approval or not approval['aprobado']: raise DeskError('Se requiere aprobación vigente')
            if (service_id is None)==(new is None): raise DeskError('Indique servicio existente o datos de uno nuevo')
            if new is not None:
                existing=store.service_by_code(new['code'].strip())
                if existing:
                    if existing['name']!=new['name'].strip() or existing['level_1_code']!=new['level_1_code'].strip():
                        raise DeskError('Código ocupado por otro servicio; seleccione explícitamente el existente')
                    service_id=existing['id']
                else:
                    try:
                        with repo.connection.transaction():
                            service_id=ServiceService(ServiceRepository(repo.connection)).create_service(new).id
                    except ServiceOperationError as error:
                        raise DeskError(str(error)) from error
            service=repo.reference('servicio',service_id)
            if not service or not service['active'] or not service['nivel1_activo']: raise DeskError('Servicio inexistente o inactivo')
            if flow['servicio_resultado_id'] and flow['servicio_resultado_id']!=service_id:
                raise DeskError('El proceso ya produjo otro servicio')
            return self.persist(repo,store,flow,actor,flow['estado'],flow['datos'],reason,service_id=service_id)
