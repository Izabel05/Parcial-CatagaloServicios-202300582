from psycopg.types.json import Jsonb


class ProcessRepository:
    """Persistencia del flujo; comparte la transacción y bloqueo del ticket."""
    def __init__(self, connection):
        self.connection = connection

    def get(self, ticket_id, initial):
        self.connection.execute('INSERT INTO sd_procesos_ticket(ticket_id,estado) VALUES (%s,%s) ON CONFLICT DO NOTHING', (ticket_id, initial))
        return self.connection.execute('SELECT * FROM sd_procesos_ticket WHERE ticket_id=%s FOR UPDATE', (ticket_id,)).fetchone()

    def update(self, ticket_id, state, data, version, service_id=None):
        self.connection.execute('UPDATE sd_tickets SET updated_at=CURRENT_TIMESTAMP WHERE id=%s', (ticket_id,))
        return self.connection.execute('''UPDATE sd_procesos_ticket SET estado=%s,datos=%s,version=%s,
            servicio_resultado_id=%s,updated_at=CURRENT_TIMESTAMP WHERE ticket_id=%s RETURNING *''',
            (state,Jsonb(data),version,service_id,ticket_id)).fetchone()

    def approval(self, ticket_id, version):
        return self.connection.execute('SELECT * FROM sd_aprobaciones WHERE ticket_id=%s AND version_proceso=%s', (ticket_id,version)).fetchone()

    def link(self, source, target, kind):
        self.connection.execute('INSERT INTO sd_ticket_vinculos(origen_id,destino_id,tipo) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING', (source,target,kind))

    def event_incident(self, ticket_id):
        return self.connection.execute('SELECT * FROM sd_evento_incidente WHERE evento_id=%s', (ticket_id,)).fetchone()

    def register_event(self, event_id, incident_id, actor):
        self.connection.execute('INSERT INTO sd_evento_incidente(evento_id,incidente_id,actor_id) VALUES (%s,%s,%s)', (event_id,incident_id,actor))
        self.link(event_id,incident_id,'evento_incidente')
        self.connection.execute('INSERT INTO sd_notificaciones(evento_id,incidente_id,mensaje) VALUES (%s,%s,%s)', (event_id,incident_id,'Evento asociado a incidente; revisar impacto en el servicio'))

    def service_by_code(self, code):
        return self.connection.execute('SELECT * FROM services WHERE code=%s', (code,)).fetchone()
