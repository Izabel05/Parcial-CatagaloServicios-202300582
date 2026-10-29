from datetime import datetime, timezone
from backend.app.repositories.experience_repository import ExperienceRepository
from backend.app.services.desk_service import DeskService, DeskDenied, DeskError, DeskMissing
from backend.app.services.desk_metrics import calculate


class ExperienceService:
    def __init__(self, desk=None):
        self.desk=desk or DeskService()

    def spaces(self, actor):
        with self.desk.repository.transaction() as repo:
            user=self.desk.user(repo,actor)
            queues=repo.queues()
            console=user['role']=='administrador' or bool({'agente','aprobador','consulta'} & set(user['roles']))
            admin=user['role']!='consulta' and (user['role']=='administrador' or any(self.desk.can(repo,user,q['id'],'administrar') for q in queues))
            return {'portal':True,'consola':console,'administracion':admin,'administrador':user['role']=='administrador'}

    def dashboard(self, actor, scope, queue_id=None, process=None, page=1, size=25):
        with self.desk.repository.transaction() as repo:
            user=self.desk.user(repo,actor)
            queues=[q['id'] for q in repo.queues() if self.desk.can(repo,user,q['id'],'consultar')]
            rows=ExperienceRepository(repo.connection).metrics_rows(actor,queues,scope,queue_id,process)
            result=calculate(rows,datetime.now(timezone.utc))
            result.update(ambito=scope,detalle_total=len(result['tickets']),pagina=page,tamano=size)
            result['tickets']=result['tickets'][(page-1)*size:page*size]
            return result

    def faqs(self, actor, search='', admin=False):
        with self.desk.repository.transaction() as repo:
            user=self.desk.user(repo,actor)
            if admin and user['role']!='administrador': raise DeskDenied('Solo administrador consulta borradores FAQ')
            return ExperienceRepository(repo.connection).faqs(search,admin)

    def faq(self, actor, values, faq_id=None):
        with self.desk.repository.transaction(True) as repo:
            user=self.desk.user(repo,actor)
            if user['role']!='administrador': raise DeskDenied('Solo administrador mantiene el autoservicio')
            store=ExperienceRepository(repo.connection)
            before=store.faq(faq_id) if faq_id else None
            if faq_id and not before: raise DeskMissing('Artículo no encontrado')
            if values['servicio_id']:
                service=repo.reference('servicio',values['servicio_id'])
                if not service or not service['active'] or not service['nivel1_activo']: raise DeskError('Servicio inexistente o inactivo')
            after=store.save_faq(values,faq_id)
            repo.audit(actor,'editar_faq' if faq_id else 'crear_faq',before,after,internal=True)
            return after
