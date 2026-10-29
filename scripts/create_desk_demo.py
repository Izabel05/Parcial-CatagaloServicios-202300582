"""Crea cuatro cuentas Service Desk y siete colas; no crea flujos especializados."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.create_demo_users import ensure_demo_position, upsert_demo_user, generated_password
from backend.app.database.migrate import migrate
from backend.app.config.settings import settings
from backend.app.security.passwords import PasswordService
from backend.app.security.encryption import AesGcmCipher
from backend.app.repositories.desk_repository import DeskRepository
from backend.app.services.desk_service import DeskService, PROCESSES


def main():
    migrate()
    repository=DeskRepository()
    with repository.transaction() as repo:
        admin=repo.user_by_username('demo-admin')
    if not admin:
        raise SystemExit('Ejecute primero scripts/create_demo_users.py')
    position,_=ensure_demo_position(None)
    passwords=PasswordService()
    cipher=AesGcmCipher(settings.app_encryption_key)
    accounts=[]
    for username,role in [('demo-solicitante','solicitante'),('demo-agente1','agente'),('demo-agente2','agente'),('demo-aprobador','aprobador')]:
        password=generated_password()
        user_id=upsert_demo_user(username,username+'@local.test',password,role,position,passwords,cipher,None)
        accounts.append((username,password,user_id))
    service=DeskService(repository)
    existing={q['codigo']:q for q in service.queues(admin['id'])}
    for process in PROCESSES:
        code='DEMO-'+process.upper()
        queue=existing.get(code)
        if not queue:
            queue=service.queue(admin['id'],dict(codigo=code,nombre=process.replace('_',' ').capitalize(),descripcion='Cola de demostración',
                proceso=process,activo=True,nivel_soporte=1,ordenamiento='prioridad_antiguedad',
                objetivo_primera_atencion_min=60,objetivo_resolucion_min=480,responsables_ids=[admin['id']]))
            grants=[{'rol':role,'usuario_id':None,'permiso':permission} for role,permissions in
                    [('agente',['consultar','atender','transferir']),('aprobador',['consultar','aprobar']),('consulta',['consultar'])]
                    for permission in permissions]
            service.permissions(admin['id'],queue['id'],grants)
    for username,password,user_id in accounts:
        print(f'username={username} password={password} id={user_id}')
    print('Siete colas disponibles. Las colas existentes y sus permisos no se sobrescriben.')


if __name__=='__main__': main()
