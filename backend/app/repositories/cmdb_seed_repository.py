import json

from psycopg.types.json import Jsonb


class CmdbSeedRepository:
    """Escritura en lote; se usa dentro de la transacción serializada de CMDB."""

    def __init__(self, connection):
        self.connection = connection

    def references(self, actor, seed, version):
        user = self.connection.execute('SELECT id FROM users WHERE id=%s AND is_active FOR SHARE', (actor,)).fetchone()
        if not user:
            raise ValueError('El responsable debe ser un usuario activo existente')
        services = self.connection.execute('SELECT id FROM services WHERE active IS TRUE ORDER BY code FOR SHARE').fetchall()
        if not services:
            raise ValueError('Importe primero el catálogo con servicios activos')
        for code, name, cell in [('FUENTE-HARDWARE', 'Hardware', 'CMDB!C5'), ('FUENTE-SOFTWARE', 'Software', 'CMDB!C6')]:
            self.connection.execute('''INSERT INTO cmdb_clasificaciones(codigo,nombre,origen,referencia_fuente)
                VALUES (%s,%s,'fuente',%s) ON CONFLICT(codigo) DO NOTHING''', (code, name, cell))
        classification = self.connection.execute("SELECT * FROM cmdb_clasificaciones WHERE codigo='FUENTE-HARDWARE' FOR SHARE").fetchone()
        if not classification['activo'] or classification['nombre'] != 'Hardware':
            raise ValueError('La clasificación Hardware de fuente debe estar activa y conservar su etiqueta')
        # Se validan también ancestros si el administrador documentó y configuró una ruta.
        invalid = self.connection.execute('''WITH RECURSIVE path AS (
            SELECT id,padre_id,activo,ARRAY[id] AS ids FROM cmdb_clasificaciones WHERE id=%s
            UNION ALL SELECT c.id,c.padre_id,c.activo,p.ids||c.id FROM cmdb_clasificaciones c
            JOIN path p ON p.padre_id=c.id WHERE NOT c.id=ANY(p.ids)
        ) SELECT bool_and(activo) AS valid FROM path''', (classification['id'],)).fetchone()
        if not invalid['valid']:
            raise ValueError('Hardware tiene ancestros inactivos')
        location = self.connection.execute('''INSERT INTO cmdb_ubicaciones(codigo,nombre)
            VALUES ('SINTETICA','Sala de demostración sintética') ON CONFLICT(codigo)
            DO UPDATE SET codigo=EXCLUDED.codigo RETURNING *''').fetchone()
        if not location['activo']:
            raise ValueError('La ubicación de demostración está desactivada')
        lot = self.connection.execute('''INSERT INTO cmdb_lotes_sinteticos(semilla,version) VALUES (%s,%s)
            ON CONFLICT(semilla,version) DO UPDATE SET version=EXCLUDED.version RETURNING id''', (seed, version)).fetchone()['id']
        return classification['id'], location['id'], lot, [r['id'] for r in services]

    def save_batch(self, rows, lot, actor, service_ids):
        previous = {row['codigo']: row for row in self.connection.execute(
            'SELECT * FROM cmdb_ci WHERE codigo=ANY(%s)', ([r[0] for r in rows],)).fetchall()}
        with self.connection.cursor() as cursor:
            cursor.executemany('''INSERT INTO cmdb_ci
                (codigo,nombre,clasificacion_id,ubicacion_id,responsable_usuario_id,numero_serie,atributos_tecnicos)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(codigo) DO UPDATE SET
                nombre=EXCLUDED.nombre,clasificacion_id=EXCLUDED.clasificacion_id,
                ubicacion_id=EXCLUDED.ubicacion_id,responsable_usuario_id=EXCLUDED.responsable_usuario_id,
                numero_serie=EXCLUDED.numero_serie,atributos_tecnicos=EXCLUDED.atributos_tecnicos,
                activo=TRUE,updated_at=CURRENT_TIMESTAMP''',
                [(*r[:6], Jsonb(r[6])) for r in rows])
        ids = self.connection.execute('SELECT * FROM cmdb_ci WHERE codigo=ANY(%s)',
                                      ([r[0] for r in rows],)).fetchall()
        lookup = {r['codigo']: r['id'] for r in ids}
        after = {r['codigo']: r for r in ids}
        devices, links, audits = [], [], []
        for index, row in enumerate(rows, 1):
            ci_id = lookup[row[0]]
            devices.append((ci_id, row[0], lot, index))
            links.append((ci_id, service_ids[(index - 1) % len(service_ids)]))
            old = previous.get(row[0])
            snapshot = {**after[row[0]], 'lote_id': lot, 'indice': index,
                        'servicio_generado_id': service_ids[(index - 1) % len(service_ids)]}
            audits.append((ci_id, actor, Jsonb(json.loads(json.dumps(old, default=str))) if old else None,
                           Jsonb(json.loads(json.dumps(snapshot, default=str)))))
        with self.connection.cursor() as cursor:
            cursor.executemany('''INSERT INTO cmdb_dispositivos(ci_id,etiqueta,lote_id,indice_sintetico)
                VALUES (%s,%s,%s,%s) ON CONFLICT(ci_id) DO UPDATE SET
                etiqueta=EXCLUDED.etiqueta,lote_id=EXCLUDED.lote_id,indice_sintetico=EXCLUDED.indice_sintetico''', devices)
            cursor.executemany('''INSERT INTO cmdb_ci_servicios(ci_id,servicio_id) VALUES (%s,%s)
                ON CONFLICT(ci_id,servicio_id) DO UPDATE SET activo=TRUE''', links)
            cursor.executemany('''INSERT INTO cmdb_auditoria(entidad,entidad_id,actor_id,accion,antes,despues)
                VALUES ('ci',%s,%s,'generacion_sintetica',%s,%s)''', audits)
        return lookup

    def count_lot(self, lot):
        return self.connection.execute('SELECT count(*) AS total FROM cmdb_dispositivos WHERE lote_id=%s', (lot,)).fetchone()['total']
