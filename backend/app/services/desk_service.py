from datetime import datetime, timezone
import hashlib
from pathlib import PurePath

from backend.app.repositories.desk_repository import DeskRepository

PROCESSES = ['nuevos_servicios','cambios','incidentes','eventos','problemas','accesos','servicios_tecnologia']
PERMISSIONS = ['consultar','atender','transferir','aprobar','administrar']
TYPE_MAP = dict(zip(PROCESSES, ['requisicion_servicio','solicitud_cambio','incidente','evento','problema','solicitud_acceso','requisicion_servicio']))
MAX_ATTACHMENT = 5 * 1024 * 1024


class DeskError(ValueError):
    status = 409


class DeskDenied(DeskError):
    status = 403


class DeskMissing(DeskError):
    status = 404


class DeskService:
    def __init__(self, repository=None):
        self.repository = repository or DeskRepository()

    @staticmethod
    def user(repo, user_id):
        user = repo.user(user_id)
        if not user or not user['is_active']:
            raise DeskDenied('Usuario inexistente o inactivo')
        return user

    @staticmethod
    def can(repo, user, queue_id, permission):
        if user['role'] == 'consulta' and permission != 'consultar':
            return False
        if user['role'] == 'administrador':
            return True
        return any(g['permiso'] == permission and (g['usuario_id'] == user['id'] or g['rol'] in user['roles'])
                   for g in repo.grants(queue_id))

    def allow(self, repo, user, queue_id, permission):
        if not self.can(repo,user,queue_id,permission):
            raise DeskDenied('No tiene el permiso requerido en esta cola')
        if permission in ('atender','transferir') and not ({'administrador','agente'} & set(user['roles'])):
            raise DeskDenied('Se requiere el rol agente además del permiso de cola')
        if permission == 'aprobar' and not ({'administrador','aprobador'} & set(user['roles'])):
            raise DeskDenied('Se requiere el rol aprobador además del permiso de cola')

    @staticmethod
    def get(repo, entity, entity_id, lock=False):
        row = repo.get(entity, entity_id, lock)
        if not row:
            raise DeskMissing('Registro no encontrado')
        return row

    def readable(self, repo, user, ticket_id, lock=False):
        ticket = self.get(repo,'ticket',ticket_id,lock)
        if ticket['solicitante_id'] != user['id']:
            self.allow(repo,user,ticket['cola_id'],'consultar')
        return ticket

    def writable(self, repo, user, ticket_id, permission='atender'):
        ticket = self.readable(repo,user,ticket_id,True)
        self.allow(repo,user,ticket['cola_id'],permission)
        if not self.get(repo,'cola',ticket['cola_id'])['activo']:
            raise DeskError('La cola está inactiva')
        return ticket

    def internal(self, repo, user, ticket):
        return user['role'] != 'consulta' and bool({'agente','administrador'} & set(user['roles'])) and self.can(repo,user,ticket['cola_id'],'atender')

    def eligible(self, repo, user_id, queue_id):
        user = self.user(repo,user_id)
        self.allow(repo,user,queue_id,'consultar')
        self.allow(repo,user,queue_id,'atender')
        return user

    def me(self, actor):
        with self.repository.transaction() as repo:
            return self.user(repo,actor)

    def roles(self, actor, user_id, roles):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            if user['role'] != 'administrador':
                raise DeskDenied('Solo administrador puede asignar roles')
            before = self.user(repo,user_id)
            repo.roles(user_id,roles)
            for ticket in repo.assigned(user_id=user_id):
                self.eligible(repo,user_id,ticket['cola_id'])
            after = self.user(repo,user_id)
            repo.audit(actor,'roles_usuario',before,after,internal=True)
            return after

    def user_roles(self, actor, user_id):
        with self.repository.transaction() as repo:
            if self.user(repo,actor)['role']!='administrador':
                raise DeskDenied('Solo administrador consulta roles de otras cuentas')
            return self.user(repo,user_id)

    def queues(self, actor):
        with self.repository.transaction() as repo:
            user = self.user(repo,actor)
            result = []
            for q in repo.queues():
                if q['activo'] or user['role']=='administrador':
                    q['mis_permisos'] = [p for p in PERMISSIONS if self.can(repo,user,q['id'],p)]
                    q['responsables_ids'] = repo.managers(q['id'])
                    if self.can(repo,user,q['id'],'administrar'):
                        q['permisos'] = repo.grants(q['id'])
                    result.append(q)
            return result

    def queue(self, actor, values, queue_id=None):
        values = dict(values)
        managers = values.pop('responsables_ids')
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            before = self.get(repo,'cola',queue_id,True) if queue_id else None
            if before:
                self.allow(repo,user,queue_id,'administrar')
                if not values['activo'] and repo.queue_has_open(queue_id):
                    raise DeskError('Transfiera o cierre todos los tickets antes de desactivar la cola')
                if values['proceso'] != before['proceso'] and repo.queue_has_tickets(queue_id):
                    raise DeskError('No se cambia el proceso de una cola con historial de tickets')
            elif user['role'] != 'administrador':
                raise DeskDenied('Solo administrador crea colas')
            for manager in managers:
                self.user(repo,manager)
            after = repo.save('cola',values,queue_id)
            old_managers = repo.managers(after['id'])
            repo.managers(after['id'], managers)
            repo.audit(actor,'editar_cola' if before else 'crear_cola',
                       {**before,'responsables_ids':old_managers} if before else None,
                       {**after,'responsables_ids':managers},queue_id=after['id'])
            return after

    def deactivate_queue(self, actor, queue_id):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            before = self.get(repo,'cola',queue_id,True)
            self.allow(repo,user,queue_id,'administrar')
            if repo.queue_has_open(queue_id):
                raise DeskError('Transfiera o cierre los tickets antes de desactivar la cola')
            after = repo.save('cola',{'activo':False},queue_id)
            repo.audit(actor,'desactivar_cola',before,after,queue_id=queue_id)
            return after

    def permissions(self, actor, queue_id, grants):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            self.get(repo,'cola',queue_id,True)
            self.allow(repo,user,queue_id,'administrar')
            for grant in grants:
                if grant['usuario_id'] is not None:
                    self.user(repo,grant['usuario_id'])
            before = repo.grants(queue_id)
            repo.save_grants(queue_id,grants)
            for ticket in repo.assigned(queue_id=queue_id):
                if ticket['responsable_id']:
                    self.eligible(repo,ticket['responsable_id'],queue_id)
            after = repo.grants(queue_id)
            repo.audit(actor,'permisos_cola',before,after,queue_id=queue_id,internal=True)
            return after

    def queue_history(self, actor, queue_id):
        with self.repository.transaction() as repo:
            user=self.user(repo,actor)
            self.get(repo,'cola',queue_id)
            self.allow(repo,user,queue_id,'administrar')
            return repo.queue_history(queue_id)

    def create(self, actor, values):
        values = dict(values)
        ci_ids = values.pop('ci_ids')
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            if user['role']=='consulta' or not ({'administrador','solicitante'} & set(user['roles'])):
                raise DeskDenied('Se requiere rol solicitante para crear tickets')
            requester = values.pop('solicitante_id') or actor
            if requester != actor and user['role'] != 'administrador':
                raise DeskDenied('Solo administrador registra por otro solicitante')
            self.user(repo,requester)
            queue = self.get(repo,'cola',values['cola_id'])
            if not queue['activo']:
                raise DeskError('La cola está inactiva')
            service = repo.reference('servicio',values['servicio_id'])
            if not service or service['active'] is not True or service['nivel1_activo'] is not True:
                raise DeskError('Servicio inexistente o inactivo')
            self.validate_ci(repo,ci_ids)
            ticket = repo.save('ticket',{**values,'solicitante_id':requester,'creador_id':actor})
            from backend.app.repositories.process_repository import ProcessRepository
            from backend.app.services.process_rules import INITIAL
            ProcessRepository(repo.connection).get(ticket['id'],INITIAL[queue['proceso']])
            from backend.app.repositories.experience_repository import ExperienceRepository
            ExperienceRepository(repo.connection).begin_cycle(ticket)
            repo.replace_ci(ticket['id'],ci_ids)
            repo.audit(actor,'crear_ticket',None,{**ticket,'ci_ids':sorted(set(ci_ids))},ticket_id=ticket['id'])
            return ticket

    @staticmethod
    def validate_ci(repo, ci_ids):
        for ci_id in ci_ids:
            ci = repo.reference('ci',ci_id)
            if not ci or not ci['activo']:
                raise DeskError('CI inexistente o inactivo')

    def edit(self, actor, ticket_id, values):
        values=dict(values)
        ci_ids,reason=values.pop('ci_ids'),values.pop('motivo')
        with self.repository.transaction(True) as repo:
            user=self.user(repo,actor)
            before=self.writable(repo,user,ticket_id)
            if before['estado'] in ('resuelto','cerrado'):
                raise DeskError('Reabra la atención antes de editar el ticket')
            service=repo.reference('servicio',values['servicio_id'])
            if not service or service['active'] is not True or service['nivel1_activo'] is not True:
                raise DeskError('Servicio inexistente o inactivo')
            self.validate_ci(repo,ci_ids)
            from backend.app.repositories.process_repository import ProcessRepository
            from backend.app.services.process_rules import INITIAL
            process=self.get(repo,'cola',before['cola_id'])['proceso']
            store=ProcessRepository(repo.connection)
            flow=store.get(ticket_id,INITIAL[process])
            if flow['estado']=='pendiente_aprobacion' or store.approval(ticket_id,flow['version']):
                raise DeskError('Reabra el proceso para modificar los datos sometidos a aprobación')
            old_ci=repo.cis(ticket_id)
            if process=='eventos' and store.event_incident(ticket_id) and (
                    values['servicio_id']!=before['servicio_id'] or sorted(set(ci_ids))!=sorted(c['id'] for c in old_ci)):
                raise DeskError('El evento ya está correlacionado; conserve su servicio y CI para mantener la trazabilidad')
            after=repo.save('ticket',{**values,'updated_at':datetime.now(timezone.utc)},ticket_id)
            repo.replace_ci(ticket_id,ci_ids)
            repo.audit(actor,'editar_ticket',{**before,'ci':old_ci},
                       {**after,'ci_ids':ci_ids,'motivo':reason},ticket_id=ticket_id)
            return after

    def list_tickets(self, actor, filters, page=1, size=25):
        with self.repository.transaction() as repo:
            user = self.user(repo,actor)
            allowed = [q['id'] for q in repo.queues() if self.can(repo,user,q['id'],'consultar')]
            return repo.list_tickets(actor,allowed,user['role']=='administrador',filters,page,size)

    def tickets_for_ci(self, actor, ci_id, page=1, size=25):
        with self.repository.transaction() as repo:
            user=self.user(repo,actor)
            if not repo.reference('ci',ci_id): raise DeskMissing('CI no encontrado')
            allowed=[q['id'] for q in repo.queues() if self.can(repo,user,q['id'],'consultar')]
            return repo.list_tickets(actor,allowed,user['role']=='administrador',
                                     {'ci_id':ci_id,'recientes':True},page,size)

    def detail(self, actor, ticket_id, scope='visibles'):
        with self.repository.transaction() as repo:
            user = self.user(repo,actor)
            ticket = self.readable(repo,user,ticket_id)
            if scope=='propios' and ticket['solicitante_id']!=actor:
                raise DeskDenied('El portal solo permite consultar tickets propios')
            if scope=='colas': self.allow(repo,user,ticket['cola_id'],'consultar')
            queue = self.get(repo,'cola',ticket['cola_id'])
            service = repo.reference('servicio',ticket['servicio_id'])
            links = []
            for link in repo.links(ticket_id):
                other = link['destino_id'] if link['origen_id']==ticket_id else link['origen_id']
                try:
                    neighbor = self.readable(repo,user,other)
                    if scope=='propios' and neighbor['solicitante_id']!=actor: continue
                    if scope=='colas': self.allow(repo,user,neighbor['cola_id'],'consultar')
                    links.append({**link,'otro_numero':neighbor['numero'],'otro_id':other})
                except DeskDenied:
                    pass
            from backend.app.repositories.process_repository import ProcessRepository
            from backend.app.services.process_rules import INITIAL, successors
            flow = ProcessRepository(repo.connection).read(ticket_id)
            if flow is None:
                # Compatibilidad de lectura con registros heredados incompletos; GET no escribe.
                flow={'ticket_id':ticket_id,'estado':ticket['estado'] if ticket['estado'] in ('resuelto','cerrado') else INITIAL[queue['proceso']],
                      'datos':{},'version':1,'servicio_resultado_id':None,'updated_at':ticket['updated_at']}
            details=repo.details(ticket_id,self.internal(repo,user,ticket))
            visible={link['otro_id']:link['otro_numero'] for link in links}
            details['notificaciones']=[{**n,'incidente_id':n['incidente_id'] if n['incidente_id'] in visible else None,
                'incidente_numero':visible.get(n['incidente_id'])} for n in details['notificaciones']]
            return {**ticket,'flujo':{**flow,'transiciones':successors(queue['proceso'],flow['estado'])},'proceso':queue['proceso'],'tipo':TYPE_MAP[queue['proceso']],
                    'level_1_code':service['level_1_code'],'cola_nombre':queue['nombre'],
                    'ci':repo.cis(ticket_id),'vinculos':links,
                    **details}

    def assign(self, actor, ticket_id, target=None, reason='Tomar ticket'):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            before = self.writable(repo,user,ticket_id)
            self.eligible(repo,target or actor,before['cola_id'])
            if target is None:
                after = repo.claim(ticket_id,actor)
                if not after:
                    raise DeskError('El ticket ya fue tomado o no está abierto')
            else:
                if before['estado'] not in ('abierto','en_atencion'):
                    raise DeskError('El ticket no admite asignación en este estado')
                after = repo.save('ticket',{'responsable_id':target,'estado':'en_atencion',
                    'primera_atencion_at':before['primera_atencion_at'] or datetime.now(timezone.utc),
                    'updated_at':datetime.now(timezone.utc)},ticket_id)
            repo.audit(actor,'tomar' if target is None else 'asignar',before,{**after,'motivo':reason},ticket_id=ticket_id)
            from backend.app.repositories.experience_repository import ExperienceRepository
            ExperienceRepository(repo.connection).attend(ticket_id)
            return after

    def transfer(self, actor, ticket_id, queue_id, reason, escalate=False):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            before = self.writable(repo,user,ticket_id,'transferir')
            source = self.get(repo,'cola',before['cola_id'])
            destination = self.get(repo,'cola',queue_id)
            self.allow(repo,user,queue_id,'consultar')
            if not destination['activo'] or queue_id==source['id'] or source['proceso']!=destination['proceso']:
                raise DeskError('Destino debe ser otra cola activa del mismo proceso')
            if escalate and destination['nivel_soporte'] <= source['nivel_soporte']:
                raise DeskError('Escalar requiere un nivel de soporte superior')
            if before['estado'] not in ('abierto','en_atencion'):
                raise DeskError('Reabra la atención antes de transferir')
            after = repo.save('ticket',{'cola_id':queue_id,'responsable_id':None,'estado':'abierto',
                                       'updated_at':datetime.now(timezone.utc)},ticket_id)
            repo.audit(actor,'escalar' if escalate else 'transferir',before,{**after,'motivo':reason},ticket_id=ticket_id)
            return after

    def state(self, actor, ticket_id, state, reason, resolution=None):
        from backend.app.services.process_service import ProcessService
        return ProcessService(self).transition(actor,ticket_id,state,resolution or reason)

    def comment(self, actor, ticket_id, text, internal=False):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            ticket = self.readable(repo,user,ticket_id,True)
            self.contribute(repo,user,ticket,internal)
            result = repo.save('comentario',{'ticket_id':ticket_id,'actor_id':actor,'texto':text,'interno':internal})
            repo.audit(actor,'nota_interna' if internal else 'comentario',None,result,ticket_id=ticket_id,internal=internal)
            return result

    def contribute(self, repo, user, ticket, internal):
        if user['role']=='consulta':
            raise DeskDenied('Consulta solo puede leer')
        if ticket['estado']=='cerrado':
            raise DeskError('Reabra el ticket antes de agregar contenido')
        if internal or ticket['solicitante_id']!=user['id']:
            self.allow(repo,user,ticket['cola_id'],'atender')
            if not self.internal(repo,user,ticket):
                raise DeskDenied('Sin acceso a notas internas')

    def link(self, actor, ticket_id, other_id, kind):
        with self.repository.transaction(True) as repo:
            user = self.user(repo,actor)
            self.writable(repo,user,ticket_id)
            self.writable(repo,user,other_id)
            expected={'incidente_problema':('incidentes','problemas'),'problema_cambio':('problemas','cambios')}
            if kind in expected:
                actual=tuple(self.get(repo,'cola',self.get(repo,'ticket',i)['cola_id'])['proceso'] for i in (ticket_id,other_id))
                if actual!=expected[kind]: raise DeskError('Tipos de procesos incompatibles con el vínculo')
            if ticket_id==other_id:
                raise DeskError('Un ticket no se relaciona consigo mismo')
            if kind=='relacionado':
                a,b=sorted((ticket_id,other_id))
            else:
                a,b=ticket_id,other_id
            result=repo.save('vinculo',{'origen_id':a,'destino_id':b,'tipo':kind})
            for current in (ticket_id,other_id):
                repo.audit(actor,'vincular_ticket',None,result,ticket_id=current)
            return result

    def approval(self, actor, ticket_id, approved, reason):
        from backend.app.services.process_service import ProcessService
        return ProcessService(self).approval(actor,ticket_id,approved,reason)

    @staticmethod
    def validate_file(name, mime, data):
        if not 0 < len(data) <= MAX_ATTACHMENT:
            raise DeskError('Adjunto vacío o mayor de 5 MiB')
        if not name or len(name)>150 or any(c in name for c in '/\\\r\n\x00') or name in ('.','..'):
            raise DeskError('Nombre de archivo inválido')
        types = {'text/plain':{'.txt'},'image/png':{'.png'},'image/jpeg':{'.jpg','.jpeg'},'application/pdf':{'.pdf'}}
        if mime not in types or PurePath(name).suffix.lower() not in types[mime]:
            raise DeskError('Tipo o extensión no permitidos')
        if mime=='text/plain':
            try: data.decode('utf-8')
            except UnicodeDecodeError as error: raise DeskError('Texto debe ser UTF-8') from error
            if b'\0' in data: raise DeskError('Texto binario rechazado')
        elif not data.startswith({'image/png':b'\x89PNG\r\n\x1a\n','image/jpeg':b'\xff\xd8\xff','application/pdf':b'%PDF-'}[mime]):
            raise DeskError('El contenido no coincide con el tipo declarado')

    def upload(self, actor, ticket_id, name, mime, data, internal=False):
        self.validate_file(name,mime,data)
        with self.repository.transaction(True) as repo:
            user=self.user(repo,actor)
            ticket=self.readable(repo,user,ticket_id,True)
            self.contribute(repo,user,ticket,internal)
            result=repo.add_attachment(ticket_id,actor,name,mime,data,hashlib.sha256(data).hexdigest(),internal)
            repo.audit(actor,'adjunto',None,result,ticket_id=ticket_id,internal=internal)
            return result

    def download(self, actor, attachment_id):
        with self.repository.transaction() as repo:
            user=self.user(repo,actor)
            file=repo.attachment(attachment_id)
            if not file: raise DeskMissing('Adjunto no encontrado')
            ticket=self.readable(repo,user,file['ticket_id'])
            if file['interno'] and not self.internal(repo,user,ticket):
                raise DeskDenied('Adjunto interno no autorizado')
            return repo.attachment(attachment_id,True)
