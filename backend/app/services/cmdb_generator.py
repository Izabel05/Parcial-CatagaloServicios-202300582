import random

from backend.app.repositories.cmdb_repository import CmdbRepository
from backend.app.repositories.cmdb_seed_repository import CmdbSeedRepository
from backend.app.services.cmdb_service import CmdbService

GENERATOR_VERSION = 'hardware-v1'


def generate_devices(seed, count, actor, database_url=None):
    if count < 1 or count > 100000:
        raise ValueError('Cantidad permitida: 1 a 100000 dispositivos')
    if not -(2**63) <= seed < 2**63:
        raise ValueError('Semilla fuera del rango BIGINT')
    randomizer = random.Random(seed)
    service = CmdbService(CmdbRepository(database_url=database_url))
    with service.repository.transaction(write=True) as repo:
        seed_repo = CmdbSeedRepository(repo.connection)
        class_id, location_id, lot, services = seed_repo.references(actor, seed, GENERATOR_VERSION)
        previous = seed_repo.count_lot(lot)
        if previous > count:
            raise ValueError('No se reduce un lote existente: requiere limpieza explícita de datos de prueba')
        rows = []
        for index in range(1, count + 1):
            code = f'SYN-{GENERATOR_VERSION}-{seed}-{index:06}'
            attributes = {'memoria_gb': randomizer.choice([8, 16, 32, 64]),
                          'almacenamiento_gb': randomizer.choice([256, 512, 1024, 2048]),
                          'sistema_operativo': randomizer.choice(['Linux sintético', 'Windows sintético'])}
            # IP no obligatoria; rango privado, sin conexión con equipos reales.
            if index % 3 == 0:
                attributes['ip'] = f'10.{(index // 65025) % 256}.{(index // 255) % 255}.{index % 255 + 1}'
            rows.append((code, f'Dispositivo sintético {index:06}', class_id, location_id,
                         actor, f'SERIE-SYN-{seed}-{index:06}', attributes))
        seed_repo.save_batch(rows, lot, actor, services)
        return {'semilla': seed, 'version': GENERATOR_VERSION, 'lote_id': lot,
                'dispositivos_lote': seed_repo.count_lot(lot),
                'creados': count - previous, 'actualizados': min(previous, count),
                'clasificacion': 'Hardware', 'jerarquia_multinivel_verificada': False}
