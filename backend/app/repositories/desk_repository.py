from contextlib import contextmanager
import json

from psycopg import sql
from psycopg.types.json import Jsonb
from backend.app.database.connection import get_connection

TABLES = {'cola': 'sd_colas', 'ticket': 'sd_tickets', 'comentario': 'sd_comentarios',
          'vinculo': 'sd_ticket_vinculos', 'aprobacion': 'sd_aprobaciones'}


class DeskRepository:
    def __init__(self, connection=None, database_url=None):
        self.connection, self.database_url = connection, database_url

    @contextmanager
    def transaction(self, write=False):
        if self.connection is not None:
            with self.connection.transaction():
                if write: self.connection.execute('SELECT pg_advisory_xact_lock(7200584)')
                yield DeskRepository(self.connection,self.database_url)
            return
        with get_connection(self.database_url) as connection:
            if write:
                connection.execute('SELECT pg_advisory_xact_lock(7200584)')
            yield DeskRepository(connection, self.database_url)

    def user(self, user_id):
        row = self.connection.execute('SELECT id,username,role,is_active FROM users WHERE id=%s FOR SHARE', (user_id,)).fetchone()
        if row:
            row['roles'] = list({row['role']} | {r['rol'] for r in self.connection.execute(
                'SELECT rol FROM sd_roles_usuario WHERE usuario_id=%s', (user_id,)).fetchall()})
        return row

    def roles(self, user_id, roles):
        self.connection.execute('DELETE FROM sd_roles_usuario WHERE usuario_id=%s', (user_id,))
        for role in sorted(set(roles)):
            self.connection.execute('INSERT INTO sd_roles_usuario VALUES (%s,%s)', (user_id, role))

    def user_by_username(self, username):
        return self.connection.execute('SELECT id FROM users WHERE username_normalized=%s', (username.casefold(),)).fetchone()

    def queue_history(self, queue_id):
        return self.connection.execute('SELECT * FROM sd_historial WHERE cola_id=%s ORDER BY id', (queue_id,)).fetchall()

    def get(self, entity, entity_id, lock=False):
        return self.connection.execute(sql.SQL('SELECT * FROM {} WHERE id=%s' + (' FOR UPDATE' if lock else '')).format(
            sql.Identifier(TABLES[entity])), (entity_id,)).fetchone()

    def save(self, entity, values, entity_id=None):
        if entity_id is None:
            query = sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING *').format(sql.Identifier(TABLES[entity]),
                sql.SQL(',').join(map(sql.Identifier, values)), sql.SQL(',').join(sql.Placeholder() for _ in values))
            params = tuple(values.values())
        else:
            query = sql.SQL('UPDATE {} SET {} WHERE id=%s RETURNING *').format(sql.Identifier(TABLES[entity]),
                sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in values))
            params = (*values.values(), entity_id)
        return self.connection.execute(query, params).fetchone()

    def audit(self, actor, action, before, after, ticket_id=None, queue_id=None, internal=False):
        encode = lambda v: Jsonb(json.loads(json.dumps(v, default=str))) if v is not None else None
        self.connection.execute('''INSERT INTO sd_historial(ticket_id,cola_id,actor_id,accion,antes,despues,interno)
            VALUES (%s,%s,%s,%s,%s,%s,%s)''', (ticket_id, queue_id, actor, action, encode(before), encode(after), internal))

    def queues(self):
        return self.connection.execute('SELECT * FROM sd_colas ORDER BY proceso,codigo').fetchall()

    def grants(self, queue_id):
        return self.connection.execute('SELECT rol,usuario_id,permiso FROM sd_permisos_cola WHERE cola_id=%s ORDER BY id', (queue_id,)).fetchall()

    def save_grants(self, queue_id, grants):
        self.connection.execute('DELETE FROM sd_permisos_cola WHERE cola_id=%s', (queue_id,))
        for grant in grants:
            self.connection.execute('''INSERT INTO sd_permisos_cola(cola_id,rol,usuario_id,permiso)
                VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING''', (queue_id, grant['rol'], grant['usuario_id'], grant['permiso']))

    def managers(self, queue_id, ids=None):
        if ids is not None:
            self.connection.execute('DELETE FROM sd_cola_responsables WHERE cola_id=%s', (queue_id,))
            for user_id in set(ids):
                self.connection.execute('INSERT INTO sd_cola_responsables VALUES (%s,%s)', (queue_id, user_id))
        return [r['usuario_id'] for r in self.connection.execute('SELECT usuario_id FROM sd_cola_responsables WHERE cola_id=%s', (queue_id,)).fetchall()]

    def assigned(self, user_id=None, queue_id=None):
        return self.connection.execute('''SELECT id,cola_id,responsable_id FROM sd_tickets
            WHERE estado<>'cerrado' AND (%s::bigint IS NULL OR responsable_id=%s)
            AND (%s::bigint IS NULL OR cola_id=%s)''', (user_id, user_id, queue_id, queue_id)).fetchall()

    def queue_has_open(self, queue_id):
        return self.connection.execute("SELECT EXISTS(SELECT 1 FROM sd_tickets WHERE cola_id=%s AND estado<>'cerrado') AS yes", (queue_id,)).fetchone()['yes']

    def queue_has_tickets(self, queue_id):
        return self.connection.execute('SELECT EXISTS(SELECT 1 FROM sd_tickets WHERE cola_id=%s) AS yes', (queue_id,)).fetchone()['yes']

    def reference(self, entity, entity_id):
        if entity=='servicio':
            return self.connection.execute('''SELECT s.*,l.active AS nivel1_activo FROM services s
                JOIN service_level_1 l ON l.code=s.level_1_code WHERE s.id=%s FOR SHARE''', (entity_id,)).fetchone()
        table = {'servicio': 'services', 'ci': 'cmdb_ci'}[entity]
        return self.connection.execute(sql.SQL('SELECT * FROM {} WHERE id=%s FOR SHARE').format(sql.Identifier(table)), (entity_id,)).fetchone()

    def replace_ci(self, ticket_id, ci_ids):
        self.connection.execute('DELETE FROM sd_ticket_ci WHERE ticket_id=%s', (ticket_id,))
        for ci_id in sorted(set(ci_ids)):
            self.connection.execute('INSERT INTO sd_ticket_ci VALUES (%s,%s)', (ticket_id, ci_id))

    def cis(self, ticket_id):
        return self.connection.execute('''SELECT c.id,c.codigo,c.nombre FROM cmdb_ci c
            JOIN sd_ticket_ci l ON l.ci_id=c.id WHERE l.ticket_id=%s ORDER BY c.codigo''', (ticket_id,)).fetchall()

    def claim(self, ticket_id, user_id):
        # La condición se evalúa bajo el bloqueo de la fila: solo un UPDATE puede ganar.
        return self.connection.execute('''UPDATE sd_tickets SET responsable_id=%s,estado='en_atencion',
            primera_atencion_at=COALESCE(primera_atencion_at,CURRENT_TIMESTAMP),updated_at=CURRENT_TIMESTAMP
            WHERE id=%s AND responsable_id IS NULL AND estado='abierto' RETURNING *''', (user_id, ticket_id)).fetchone()

    def list_tickets(self, actor_id, queue_ids, admin, filters, page, size):
        scope=filters.get('ambito','visibles')
        if scope=='propios': conditions,params=['t.solicitante_id=%s'],[actor_id]
        elif scope=='colas': conditions,params=['t.cola_id=ANY(%s)'],[queue_ids]
        else:
            conditions=['(%s OR t.solicitante_id=%s OR t.cola_id=ANY(%s))']
            params=[admin,actor_id,queue_ids]
        mapping = {'cola_id':'t.cola_id','servicio_id':'t.servicio_id','estado':'t.estado',
                   'prioridad':'t.prioridad','responsable_id':'t.responsable_id','proceso':'q.proceso'}
        for name, column in mapping.items():
            if filters.get(name) is not None:
                conditions.append(column+'=%s'); params.append(filters[name])
        if filters.get('ci_id') is not None:
            conditions.append('EXISTS(SELECT 1 FROM sd_ticket_ci tc WHERE tc.ticket_id=t.id AND tc.ci_id=%s)')
            params.append(filters['ci_id'])
        if filters.get('search'):
            conditions.append('(t.numero ILIKE %s OR t.titulo ILIKE %s)')
            params.extend(['%'+filters['search']+'%'] * 2)
        for name, op in [('desde','>='),('hasta','<=')]:
            if filters.get(name):
                conditions.append('t.created_at'+op+'%s'); params.append(filters[name])
        base = ' FROM sd_tickets t JOIN sd_colas q ON q.id=t.cola_id WHERE ' + ' AND '.join(conditions)
        total = self.connection.execute('SELECT count(*) AS total'+base, params).fetchone()['total']
        order = 't.created_at DESC,t.id DESC' if filters.get('recientes') else 't.prioridad,t.created_at,t.id'
        rows = self.connection.execute('''SELECT t.*,q.nombre AS cola_nombre,q.proceso,
            s.code AS servicio_codigo,s.level_1_code,
            CASE q.proceso WHEN 'accesos' THEN 'solicitud_acceso' WHEN 'eventos' THEN 'evento'
            WHEN 'incidentes' THEN 'incidente' WHEN 'cambios' THEN 'solicitud_cambio'
            WHEN 'problemas' THEN 'problema' ELSE 'requisicion_servicio' END AS tipo
            ''' + base.replace(' WHERE ', ' JOIN services s ON s.id=t.servicio_id WHERE ', 1) +
            ' ORDER BY '+order+' LIMIT %s OFFSET %s', (*params, size, (page-1)*size)).fetchall()
        return {'items':rows,'total':total,'page':page,'page_size':size}

    def details(self, ticket_id, internal):
        comments = self.connection.execute('''SELECT c.*,u.username AS actor FROM sd_comentarios c JOIN users u ON u.id=c.actor_id
            WHERE ticket_id=%s AND (%s OR NOT interno) ORDER BY c.id''', (ticket_id, internal)).fetchall()
        history = self.connection.execute('''SELECT h.*,u.username AS actor FROM sd_historial h JOIN users u ON u.id=h.actor_id
            WHERE ticket_id=%s AND (%s OR NOT interno) ORDER BY h.id''', (ticket_id, internal)).fetchall()
        attachments = self.connection.execute('''SELECT id,nombre,mime,sha256,interno,fecha,octet_length(contenido) AS bytes
            FROM sd_adjuntos WHERE ticket_id=%s AND (%s OR NOT interno) ORDER BY id''', (ticket_id, internal)).fetchall()
        approvals = self.connection.execute('SELECT * FROM sd_aprobaciones WHERE ticket_id=%s ORDER BY id', (ticket_id,)).fetchall()
        notifications = self.connection.execute('SELECT * FROM sd_notificaciones WHERE evento_id=%s ORDER BY id', (ticket_id,)).fetchall()
        return {'comentarios':comments,'historial':history,'adjuntos':attachments,'aprobaciones':approvals,'notificaciones':notifications}

    def links(self, ticket_id):
        return self.connection.execute('SELECT * FROM sd_ticket_vinculos WHERE origen_id=%s OR destino_id=%s ORDER BY id', (ticket_id,ticket_id)).fetchall()

    def add_attachment(self, ticket_id, actor, name, mime, data, digest, internal):
        return self.connection.execute('''INSERT INTO sd_adjuntos(ticket_id,actor_id,nombre,mime,contenido,sha256,interno)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id,nombre,mime,sha256,interno,fecha''',
            (ticket_id,actor,name,mime,data,digest,internal)).fetchone()

    def attachment(self, attachment_id, content=False):
        columns = '*' if content else 'id,ticket_id,nombre,mime,interno'
        return self.connection.execute('SELECT '+columns+' FROM sd_adjuntos WHERE id=%s', (attachment_id,)).fetchone()
