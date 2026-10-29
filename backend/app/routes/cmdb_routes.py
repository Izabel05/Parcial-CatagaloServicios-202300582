from typing import Literal

from fastapi import APIRouter, Depends, Query

from backend.app.controllers.cmdb_controller import CmdbController
from backend.app.models.user import AuthenticatedContext
from backend.app.schemas.cmdb_schema import CatalogPayload, CIPayload, RelationPayload, ServiceLinkPayload
from backend.app.security.dependencies import require_administrator, require_functional_reader

router = APIRouter(prefix='/cmdb', tags=['CMDB'])
Catalog = Literal['clasificaciones', 'ubicaciones']


def controller():
    return CmdbController()


@router.get('/catalogos/{entity}')
def catalogs(entity: Catalog, _: AuthenticatedContext = Depends(require_functional_reader), c=Depends(controller)):
    return c.run('catalogs', entity)


@router.post('/catalogos/{entity}', status_code=201)
def create_catalog(entity: Catalog, payload: CatalogPayload,
                   actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('save_catalog', entity, payload.model_dump(), actor.user.id)


@router.put('/catalogos/{entity}/{entity_id}')
def update_catalog(entity: Catalog, entity_id: int, payload: CatalogPayload,
                   actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('save_catalog', entity, payload.model_dump(), actor.user.id, entity_id)


@router.delete('/catalogos/{entity}/{entity_id}')
def delete_catalog(entity: Catalog, entity_id: int,
                   actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('deactivate', entity, entity_id, actor.user.id)


@router.get('/ci')
def list_ci(search: str = Query('', max_length=200), clasificacion_id: int | None = Query(None, gt=0),
            ubicacion_id: int | None = Query(None, gt=0), activo: bool | None = None,
            es_dispositivo: bool | None = None, page: int = Query(1, ge=1, le=1000000),
            page_size: int = Query(25, ge=1, le=100),
            _: AuthenticatedContext = Depends(require_functional_reader), c=Depends(controller)):
    return c.run('list_ci', search=search, class_id=clasificacion_id, location_id=ubicacion_id,
                 active=activo, device=es_dispositivo, page=page, page_size=page_size)


@router.post('/ci', status_code=201)
def create_ci(payload: CIPayload, actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('save_ci', payload.model_dump(), actor.user.id)


@router.get('/ci/{ci_id}')
def detail(ci_id: int, _: AuthenticatedContext = Depends(require_functional_reader), c=Depends(controller)):
    return c.run('detail', ci_id)


@router.put('/ci/{ci_id}')
def update_ci(ci_id: int, payload: CIPayload,
              actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('save_ci', payload.model_dump(), actor.user.id, ci_id)


@router.delete('/ci/{ci_id}')
def deactivate_ci(ci_id: int, actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('deactivate', 'ci', ci_id, actor.user.id)


@router.get('/ci/{ci_id}/dependencias')
def impact(ci_id: int, limit: int = Query(5000, ge=1, le=10000),
           _: AuthenticatedContext = Depends(require_functional_reader), c=Depends(controller)):
    return c.run('impact', ci_id, limit)


@router.post('/ci/{ci_id}/servicios')
def link(ci_id: int, payload: ServiceLinkPayload,
         actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('service_link', ci_id, payload.servicio_id, actor.user.id)


@router.delete('/ci/{ci_id}/servicios/{service_id}')
def unlink(ci_id: int, service_id: int,
           actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('service_link', ci_id, service_id, actor.user.id, False)


@router.get('/tipos-relacion')
def types(_: AuthenticatedContext = Depends(require_functional_reader), c=Depends(controller)):
    return c.run('types')


@router.post('/relaciones', status_code=201)
def relation(payload: RelationPayload, actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('save_relation', payload.model_dump(), actor.user.id)


@router.put('/relaciones/{relation_id}')
def update_relation(relation_id: int, payload: RelationPayload,
                    actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('save_relation', payload.model_dump(), actor.user.id, relation_id)


@router.delete('/relaciones/{relation_id}')
def deactivate_relation(relation_id: int,
                        actor: AuthenticatedContext = Depends(require_administrator), c=Depends(controller)):
    return c.run('deactivate', 'relaciones', relation_id, actor.user.id)


@router.get('/reporte')
def report(_: AuthenticatedContext = Depends(require_functional_reader), c=Depends(controller)):
    return c.run('report')
