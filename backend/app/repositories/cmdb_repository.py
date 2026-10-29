from contextlib import contextmanager
import json

from psycopg import sql
from psycopg.types.json import Jsonb

from backend.app.database.connection import get_connection


TABLES = {
    'clasificaciones': 'cmdb_clasificaciones', 'ubicaciones': 'cmdb_ubicaciones',
    'ci': 'cmdb_ci', 'relaciones': 'cmdb_relaciones', 'users': 'users',
    'services': 'services',
}
JSON_FIELDS = {'atributos_tecnicos'}


class CmdbRepository:
    def __init__(self, connection=None, database_url=None):
        self.connection = connection
        self.database_url = database_url

    @contextmanager
    def transaction(self, write=False):
        with get_connection(self.database_url) as connection:
            if write:
                # Un único cerrojo del grafo coordina también generación y bajas.
                connection.execute('SELECT pg_advisory_xact_lock(7200583)')
            yield CmdbRepository(connection, self.database_url)

    def get(self, entity, entity_id):
        fields = 'id,is_active' if entity == 'users' else 'id,active' if entity == 'services' else '*'
        return self.connection.execute(
            sql.SQL('SELECT {} FROM {} WHERE id=%s FOR SHARE').format(
                sql.SQL(fields), sql.Identifier(TABLES[entity])), (entity_id,)
        ).fetchone()

    def catalogs(self, entity):
        return self.connection.execute(sql.SQL('SELECT * FROM {} ORDER BY nombre,id').format(
            sql.Identifier(TABLES[entity]))).fetchall()

    def save(self, entity, values, entity_id=None):
        table = sql.Identifier(TABLES[entity])
        values = {k: Jsonb(v) if k in JSON_FIELDS else v for k, v in values.items()}
        if entity_id is None:
            statement = sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING *').format(
                table, sql.SQL(',').join(map(sql.Identifier, values)),
                sql.SQL(',').join(sql.Placeholder() for _ in values))
            params = tuple(values.values())
        else:
            statement = sql.SQL('UPDATE {} SET {} WHERE id=%s RETURNING *').format(
                table, sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in values))
            params = (*values.values(), entity_id)
        return self.connection.execute(statement, params).fetchone()

    def audit(self, entity, entity_id, actor, action, before, after):
        normalize = lambda x: Jsonb(json.loads(json.dumps(x, default=str))) if x is not None else None
        self.connection.execute('''INSERT INTO cmdb_auditoria
            (entidad,entidad_id,actor_id,accion,antes,despues) VALUES (%s,%s,%s,%s,%s,%s)''',
            (entity, entity_id, actor, action, normalize(before), normalize(after)))

    def history(self, entity, entity_id):
        return self.connection.execute('''SELECT a.*,u.username AS actor
            FROM cmdb_auditoria a JOIN users u ON u.id=a.actor_id
            WHERE a.entidad=%s AND a.entidad_id=%s ORDER BY a.id DESC LIMIT 100''',
            (entity, entity_id)).fetchall()

    def ancestors(self, class_id):
        return self.connection.execute('''WITH RECURSIVE path AS (
            SELECT id,codigo,nombre,padre_id,activo,ARRAY[id] AS ruta FROM cmdb_clasificaciones WHERE id=%s
            UNION ALL
            SELECT c.id,c.codigo,c.nombre,c.padre_id,c.activo,p.ruta||c.id
            FROM cmdb_clasificaciones c JOIN path p ON c.id=p.padre_id
            WHERE NOT c.id=ANY(p.ruta)
        ) SELECT id,codigo,nombre,padre_id,activo FROM path ORDER BY cardinality(ruta) DESC''',
            (class_id,)).fetchall()

    def dependencies(self, entity, entity_id):
        if entity == 'clasificaciones':
            query = '''SELECT EXISTS(SELECT 1 FROM cmdb_clasificaciones WHERE padre_id=%s AND activo)
                OR EXISTS(SELECT 1 FROM cmdb_ci WHERE clasificacion_id=%s AND activo) AS blocked'''
            args = (entity_id, entity_id)
        elif entity == 'ubicaciones':
            query = 'SELECT EXISTS(SELECT 1 FROM cmdb_ci WHERE ubicacion_id=%s AND activo) AS blocked'
            args = (entity_id,)
        else:
            query = '''SELECT EXISTS(SELECT 1 FROM cmdb_relaciones WHERE activo AND (origen_ci_id=%s OR destino_ci_id=%s))
                OR EXISTS(SELECT 1 FROM cmdb_ci_servicios WHERE ci_id=%s AND activo) AS blocked'''
            args = (entity_id, entity_id, entity_id)
        return self.connection.execute(query, args).fetchone()['blocked']

    def device(self, ci_id):
        return self.connection.execute('SELECT * FROM cmdb_dispositivos WHERE ci_id=%s', (ci_id,)).fetchone()

    def save_device(self, ci_id, etiqueta):
        return self.connection.execute('''INSERT INTO cmdb_dispositivos(ci_id,etiqueta) VALUES (%s,%s)
            ON CONFLICT(ci_id) DO UPDATE SET etiqueta=EXCLUDED.etiqueta RETURNING *''', (ci_id, etiqueta)).fetchone()

    def list_ci(self, search, class_id, location_id, active, device, page, page_size):
        conditions, params = [], []
        if search:
            conditions.append('(c.codigo ILIKE %s OR c.nombre ILIKE %s)')
            pattern = '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            params.extend([pattern, pattern])
        for column, value in [('clasificacion_id', class_id), ('ubicacion_id', location_id), ('activo', active)]:
            if value is not None:
                conditions.append(f'c.{column}=%s')
                params.append(value)
        if device is not None:
            conditions.append('EXISTS(SELECT 1 FROM cmdb_dispositivos d WHERE d.ci_id=c.id)=%s')
            params.append(device)
        where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
        total = self.connection.execute('SELECT count(*) AS total FROM cmdb_ci c' + where, params).fetchone()['total']
        rows = self.connection.execute('''SELECT c.*,cl.nombre AS clasificacion_nombre,
            ub.nombre AS ubicacion_nombre,d.etiqueta,(d.ci_id IS NOT NULL) AS es_dispositivo
            FROM cmdb_ci c JOIN cmdb_clasificaciones cl ON cl.id=c.clasificacion_id
            LEFT JOIN cmdb_ubicaciones ub ON ub.id=c.ubicacion_id
            LEFT JOIN cmdb_dispositivos d ON d.ci_id=c.id''' + where +
            ' ORDER BY c.codigo,c.id LIMIT %s OFFSET %s', (*params, page_size, (page - 1) * page_size)).fetchall()
        return {'items': rows, 'total': total, 'page': page, 'page_size': page_size}

    def relations(self, ci_id):
        return self.connection.execute('''SELECT r.*,a.codigo AS origen_codigo,b.codigo AS destino_codigo
            FROM cmdb_relaciones r JOIN cmdb_ci a ON a.id=r.origen_ci_id JOIN cmdb_ci b ON b.id=r.destino_ci_id
            WHERE r.activo AND (r.origen_ci_id=%s OR r.destino_ci_id=%s) ORDER BY r.id''', (ci_id, ci_id)).fetchall()

    def relation_types(self):
        return self.connection.execute('SELECT * FROM cmdb_tipos_relacion ORDER BY codigo').fetchall()

    def graph(self, types):
        return self.connection.execute('''SELECT r.origen_ci_id,r.destino_ci_id,r.tipo FROM cmdb_relaciones r
            JOIN cmdb_ci a ON a.id=r.origen_ci_id JOIN cmdb_ci b ON b.id=r.destino_ci_id
            WHERE r.activo AND a.activo AND b.activo AND tipo=ANY(%s) ORDER BY r.id''', (types,)).fetchall()

    def impact_services(self, ci_ids):
        return self.connection.execute('''SELECT s.id,s.code,s.name,s.level_1_code,l.ci_id
            FROM services s JOIN cmdb_ci_servicios l ON s.id=l.servicio_id
            WHERE s.active IS TRUE AND l.activo AND l.ci_id=ANY(%s) ORDER BY s.code,l.ci_id''', (ci_ids,)).fetchall()

    def linked_services(self, ci_id):
        return self.connection.execute('''SELECT s.id,s.code,s.name,s.level_1_code,s.active
            FROM services s JOIN cmdb_ci_servicios l ON s.id=l.servicio_id
            WHERE l.ci_id=%s AND l.activo ORDER BY s.code''', (ci_id,)).fetchall()

    def link_service(self, ci_id, service_id, active=True):
        return self.connection.execute('''INSERT INTO cmdb_ci_servicios(ci_id,servicio_id,activo)
            VALUES (%s,%s,%s) ON CONFLICT(ci_id,servicio_id) DO UPDATE SET activo=EXCLUDED.activo RETURNING *''',
            (ci_id, service_id, active)).fetchone()

    def report(self):
        return self.connection.execute('''WITH RECURSIVE assignments AS (
            SELECT cl.id,cl.padre_id,cl.codigo,cl.nombre,c.id AS ci_id,ARRAY[cl.id] AS ruta
            FROM cmdb_clasificaciones cl JOIN cmdb_ci c ON c.clasificacion_id=cl.id
            JOIN cmdb_dispositivos d ON d.ci_id=c.id WHERE c.activo
            UNION ALL
            SELECT cl.id,cl.padre_id,cl.codigo,cl.nombre,a.ci_id,a.ruta||cl.id
            FROM cmdb_clasificaciones cl JOIN assignments a ON a.padre_id=cl.id WHERE NOT cl.id=ANY(a.ruta)
        ) SELECT id,codigo,nombre,count(DISTINCT ci_id) AS dispositivos_subarbol
          FROM assignments GROUP BY id,codigo,nombre ORDER BY codigo''').fetchall()
