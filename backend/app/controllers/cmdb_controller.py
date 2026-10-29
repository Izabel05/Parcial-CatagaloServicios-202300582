from fastapi import HTTPException
from psycopg import IntegrityError

from backend.app.services.cmdb_service import CmdbService, CmdbError, CmdbNotFound


class CmdbController:
    def __init__(self, service=None):
        self.service = service or CmdbService()

    def run(self, operation, *args, **kwargs):
        try:
            return getattr(self.service, operation)(*args, **kwargs)
        except CmdbNotFound as error:
            raise HTTPException(404, str(error)) from error
        except CmdbError as error:
            raise HTTPException(409, str(error)) from error
        except IntegrityError as error:
            raise HTTPException(409, 'Código o etiqueta duplicados, o referencia inválida') from error
