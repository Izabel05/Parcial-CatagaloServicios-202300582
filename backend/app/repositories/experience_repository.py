from backend.app.repositories.desk_repository import DeskRepository


class ExperienceRepository(DeskRepository):
    """SQL de ciclos, autoservicio y lecturas del tablero."""
    def begin_cycle(self, ticket, number=1):
        return self.connection.execute('''INSERT INTO sd_ciclos_tiempo
            (ticket_id,numero,inicio_at,cola_objetivo_id,objetivo_atencion_min,objetivo_resolucion_min,origen)
            SELECT %s,%s,CURRENT_TIMESTAMP,id,objetivo_primera_atencion_min,objetivo_resolucion_min,'nativo'
            FROM sd_colas WHERE id=%s RETURNING *''',(ticket['id'],number,ticket['cola_id'])).fetchone()

    def attend(self, ticket_id):
        self.connection.execute('''UPDATE sd_ciclos_tiempo SET primera_atencion_at=COALESCE(primera_atencion_at,CURRENT_TIMESTAMP)
            WHERE ticket_id=%s AND numero=(SELECT max(numero) FROM sd_ciclos_tiempo WHERE ticket_id=%s)''',(ticket_id,ticket_id))

    def finish_cycle(self, ticket_id, state):
        column={'resuelto':'resuelto_at','cerrado':'cerrado_at'}[state]
        self.connection.execute(f'''UPDATE sd_ciclos_tiempo SET {column}=CURRENT_TIMESTAMP
            WHERE ticket_id=%s AND numero=(SELECT max(numero) FROM sd_ciclos_tiempo WHERE ticket_id=%s)''',(ticket_id,ticket_id))

    def metrics_rows(self, actor, queues, scope, queue_id=None, process=None):
        conditions=['t.solicitante_id=%s' if scope=='propios' else 't.cola_id=ANY(%s)']
        params=[actor if scope=='propios' else queues]
        if queue_id is not None: conditions.append('t.cola_id=%s');params.append(queue_id)
        if process is not None: conditions.append('q.proceso=%s');params.append(process)
        return self.connection.execute('''SELECT c.*,t.numero ticket_numero,t.titulo,t.estado,t.prioridad,t.cola_id,q.nombre cola_nombre,q.proceso,
            t.created_at,t.solicitante_id,c.numero=(SELECT max(numero) FROM sd_ciclos_tiempo WHERE ticket_id=t.id) actual
            FROM sd_ciclos_tiempo c JOIN sd_tickets t ON t.id=c.ticket_id JOIN sd_colas q ON q.id=t.cola_id
            WHERE '''+' AND '.join(conditions)+' ORDER BY t.id,c.numero',params).fetchall()

    def faqs(self, search, admin):
        return self.connection.execute('''SELECT f.*,s.code servicio_codigo FROM sd_faq f
            LEFT JOIN services s ON s.id=f.servicio_id WHERE (%s OR publicado)
            AND (%s='' OR titulo ILIKE %s OR pregunta ILIKE %s OR respuesta ILIKE %s) ORDER BY titulo,id''',
            (admin,search,*(['%'+search+'%']*3))).fetchall()

    def faq(self, faq_id):
        return self.connection.execute('SELECT * FROM sd_faq WHERE id=%s FOR UPDATE',(faq_id,)).fetchone()

    def save_faq(self, values, faq_id=None):
        if faq_id is None:
            return self.connection.execute('''INSERT INTO sd_faq(titulo,pregunta,respuesta,servicio_id,publicado)
                VALUES (%s,%s,%s,%s,%s) RETURNING *''',tuple(values[k] for k in ('titulo','pregunta','respuesta','servicio_id','publicado'))).fetchone()
        return self.connection.execute('''UPDATE sd_faq SET titulo=%s,pregunta=%s,respuesta=%s,servicio_id=%s,
            publicado=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s RETURNING *''',
            (*[values[k] for k in ('titulo','pregunta','respuesta','servicio_id','publicado')],faq_id)).fetchone()
