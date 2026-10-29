"""Datos sintéticos identificados por semilla; nunca borra ni reinicia tickets existentes."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import os

from backend.app.database.connection import get_connection
from backend.app.repositories.demo_repository import DemoRepository
from backend.app.repositories.desk_repository import DeskRepository
from backend.app.services.cmdb_generator import generate_devices
from backend.app.services.cmdb_service import CmdbService
from backend.app.services.desk_service import DeskService, PROCESSES
from backend.app.services.process_service import ProcessService
from backend.app.services.process_rules import PATHS, INCIDENT_PRIORITY

VERSION='procesos-v1'
ACCOUNTS=[('demo-admin','administrador'),('demo-consulta','consulta'),('demo-solicitante','solicitante'),
          ('demo-agente1','agente'),('demo-agente2','agente'),('demo-aprobador','aprobador')]


def ensure_accounts(rotate=False):
    from scripts.create_demo_users import ensure_demo_position,upsert_demo_user,generated_password
    from backend.app.security.passwords import PasswordService
    from backend.app.security.encryption import AesGcmCipher
    from backend.app.config.settings import settings
    position,_=ensure_demo_position(None)
    desk=DeskService();accounts={};credentials=[]
    for name,role in ACCOUNTS:
        with desk.repository.transaction() as repo:
            found=repo.user_by_username(name)
            current=repo.user(found['id']) if found else None
        if current and (current['role']!=role or not current['is_active']):
            raise ValueError('La cuenta '+name+' existe con otro rol o está inactiva; no se sobrescribe')
        if current is None or rotate:
            password=generated_password()
            user_id=upsert_demo_user(name,name+'@local.test',password,role,position,PasswordService(),AesGcmCipher(settings.app_encryption_key),None)
            credentials.append({'usuario':name,'rol':role,'clave':password})
        else: user_id=current['id']
        accounts[name]=user_id
    return accounts,credentials


def ensure_queues(accounts):
    service=DeskService();admin=accounts['demo-admin']
    existing={q['codigo']:q for q in service.queues(admin)};result={}
    required=[{'rol':role,'usuario_id':None,'permiso':permission} for role,permissions in
              [('agente',['consultar','atender','transferir']),('aprobador',['consultar','aprobar']),('consulta',['consultar'])]
              for permission in permissions]
    for process in PROCESSES:
        code='DEMO-'+process.upper();queue=existing.get(code)
        if queue and (queue['proceso']!=process or not queue['activo']):
            raise ValueError('La cola '+code+' fue modificada; no se sobrescribe')
        if not queue:
            queue=service.queue(admin,dict(codigo=code,nombre=process.replace('_',' ').capitalize(),descripcion='Datos sintéticos de demostración',
                proceso=process,activo=True,nivel_soporte=1,ordenamiento='prioridad_antiguedad',
                objetivo_primera_atencion_min=60,objetivo_resolucion_min=480,responsables_ids=[admin]))
        with service.repository.transaction() as repo: grants=repo.grants(queue['id'])
        merged=list(grants)
        for grant in required:
            if grant not in merged: merged.append(grant)
        if merged!=grants: service.permissions(admin,queue['id'],merged)
        result[process]=queue['id']
    return result


class DemoGenerator:
    def __init__(self, desk, accounts, queues, context, store, lot, seed):
        self.desk=desk;self.flow=ProcessService(desk);self.accounts=accounts;self.queues=queues
        self.context=context;self.store=store;self.lot=lot;self.seed=seed
        self.ids=store.mapped(lot);self.created=0
        self.agent=accounts['demo-agente1'];self.requester=accounts['demo-solicitante'];self.approver=accounts['demo-aprobador']

    def ticket(self, process, index, data, target):
        if (process,index) in self.ids: return self.ids[process,index]
        payload=dict(titulo=f'[DEMO {self.seed}] {process} {index:02}',descripcion='Caso sintético reproducible; no representa una operación real.',
            cola_id=self.queues[process],servicio_id=self.context['servicio_id'],ci_ids=[self.context['ci_id']],
            solicitante_id=None,prioridad=3,impacto='medio',urgencia='media',canal='portal',motivo_sin_ci=None)
        if process=='incidentes': payload['prioridad']=INCIDENT_PRIORITY[data['categoria']]
        if process=='eventos' and data['categoria']=='E3': payload['prioridad']=1
        ticket=self.desk.create(self.requester,payload);tid=ticket['id']
        self.store.register(self.lot,process,index,tid);self.ids[process,index]=tid;self.created+=1
        self.flow.patch(self.agent,tid,data,'Datos sintéticos del escenario')
        path=PATHS[process]
        if target==path[0]: return tid
        self.desk.assign(self.agent,tid)
        for state in path[1:path.index(target)+1]:
            if state=='aprobado': self.flow.approval(self.approver,tid,True,'Aprobación sintética independiente')
            elif process=='servicios_tecnologia' and state=='resuelto':
                self.flow.confirm(self.requester,tid,'Cumplimiento sintético confirmado por solicitante')
            else:
                if process=='nuevos_servicios' and state=='implementacion':
                    self.flow.publish(self.agent,tid,self.context['servicio_id'],None,'Vincular servicio existente sin duplicar catálogo')
                self.flow.transition(self.agent,tid,state,'Evidencia sintética de transición a '+state)
        return tid

    def run(self):
        change={'evaluacion_impacto':'Servicio y CI identificados','riesgo':'medio','plan_pruebas':'Verificar disponibilidad y permisos',
            'plan_reversion':'Restaurar configuración anterior','programado_para':'2030-01-01T12:00:00Z',
            'resultado_ejecucion':'Simulación completada','resultado_pruebas':'Simulación de pruebas satisfactoria','validacion':'Resultado sintético validado'}
        for i,state in enumerate(['solicitud','evaluacion','pendiente_aprobacion','ejecucion','cerrado'],1):
            self.ticket('cambios',i,change,state)
        durations=[0,2,6,24,72,800,1]
        for i,state in enumerate(['registro','clasificacion','diagnostico','atencion','recuperado','resuelto','cerrado'],1):
            self.ticket('incidentes',i,{'categoria':'I'+str(i-1),'interrupcion':i!=1,'seguridad':i==7,
                'duracion_estimada_horas':durations[i-1],'redundancia_disponible':i==1,'duracion_real_horas':durations[i-1],
                'diagnostico':'Diagnóstico sintético registrado','evidencia_recuperacion':'Disponibilidad verificada en simulación',
                'solucion':'Solución sintética validada'},state)
        for i,(category,state) in enumerate(zip(['E0','E1','E2','E3','E2'],['registro','evaluacion','respondido','cerrado','clasificacion']),1):
            data={'categoria':category,'evaluacion':'Evaluación sintética: '+category}
            if category in ('E2','E3'): data['incidente_id']=self.ids['incidentes',7 if category=='E3' else 4]
            self.ticket('eventos',i,data,state)
        for i,state in enumerate(['registro','investigacion','error_conocido','solucion_definitiva','cerrado'],1):
            self.ticket('problemas',i,{'incidentes_ids':[self.ids['incidentes',4],self.ids['incidentes',6]],
                'causa_raiz':'Configuración sintética incorrecta','solucion_temporal':'Procedimiento temporal sintético','error_conocido':True,
                'solucion_definitiva':'Configuración corregida en simulación','cambio_correctivo_id':self.ids['cambios',5]},state)
        for i,state in enumerate(['solicitud','analisis','pendiente_aprobacion','implementacion','cerrado'],1):
            self.ticket('nuevos_servicios',i,{'necesidad':'Necesidad sintética de servicio','analisis_viabilidad':'Recursos de demostración disponibles',
                'viable':True,'plan_implementacion':'Vincular capacidad ya existente','evidencia_implementacion':'Vínculo de catálogo verificado',
                'validacion':'Servicio de demostración validado'},state)
        for i,state in enumerate(['solicitud','validacion','pendiente_aprobacion','provision','cerrado'],1):
            self.ticket('accesos',i,{'beneficiario_id':self.requester,'recurso':'Portal sintético','permiso_solicitado':'Consultar información de prueba',
                'accion':'revocar' if i==5 else 'provisionar','validacion_solicitud':'Necesidad sintética validada',
                'evidencia_provision':'Permiso simulado; no se modificaron accesos reales','validacion':'Resultado sintético comprobado'},state)
        for i,state in enumerate(['solicitud','validacion','cumplimiento','confirmacion','cerrado'],1):
            self.ticket('servicios_tecnologia',i,{'detalle_solicitud':'Atender solicitud sobre servicio existente','validacion':'Solicitud sintética válida',
                'evidencia_cumplimiento':'Cumplimiento simulado del servicio'},state)


def prepare_demo(seed=202300582, rotate=False):
    from backend.app.database.migrate import migrate
    from backend.app.importer.catalog_importer import run_import
    from backend.app.config.settings import settings
    imported=run_import(Path('data/CatalogoServicios.xlsx'),'Servicios Externos',os.getenv('DATABASE_URL') or settings.database_url)
    migrate()
    with get_connection() as connection:
        connection.execute('SELECT pg_advisory_xact_lock(7200587)')
        accounts,credentials=ensure_accounts(rotate)
        queues=ensure_queues(accounts)
        devices=generate_devices(seed,5000,accounts['demo-admin'])
        store=DemoRepository(connection)
        vertices=store.graph_devices(seed)
        for a,b in zip(vertices,vertices[1:]):
            if not store.relation_exists(a,b):
                CmdbService().save_relation({'origen_ci_id':a,'destino_ci_id':b,'tipo':'depende_de','justificacion':'Dependencia sintética para demostración'},accounts['demo-admin'])
        lot=store.lot(seed,VERSION);context=store.context(seed)
        if not context: raise ValueError('No hay servicio activo vinculado al lote CMDB')
        generator=DemoGenerator(DeskService(DeskRepository(connection)),accounts,queues,context,store,lot,seed)
        generator.run();report=store.report(lot)
        report.update(semilla=seed,version=VERSION,lote_id=lot,tickets_creados=generator.created,
            por_proceso=dict(Counter(r['proceso'] for r in report['tickets'])),colas=queues,
            usuarios=[{'usuario':name,'rol':role,'id':accounts[name]} for name,role in ACCOUNTS],
            generacion_cmdb=devices,fecha=datetime.now(timezone.utc),jerarquia_multinivel_verificada=False)
        report['importacion']=imported
        return report,credentials
