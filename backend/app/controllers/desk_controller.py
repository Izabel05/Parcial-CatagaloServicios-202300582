from fastapi import HTTPException
from psycopg import IntegrityError
from backend.app.services.desk_service import DeskService, DeskError


class DeskController:
    def __init__(self, service=None):
        self.service=service or DeskService()

    def run(self, operation, *args, **kwargs):
        try:
            return getattr(self.service,operation)(*args,**kwargs)
        except DeskError as error:
            raise HTTPException(error.status,str(error)) from error
        except IntegrityError as error:
            raise HTTPException(409,'Referencia inválida, código duplicado o dependencia activa') from error
