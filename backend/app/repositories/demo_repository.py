class DemoRepository:
    def __init__(self, connection): self.connection=connection

    def lot(self, seed, version):
        return self.connection.execute('''INSERT INTO sd_demo_lotes(semilla,version) VALUES (%s,%s)
            ON CONFLICT(semilla,version) DO UPDATE SET version=EXCLUDED.version RETURNING id''',(seed,version)).fetchone()['id']

    def mapped(self, lot):
        return {(r['proceso'],r['indice']):r['ticket_id'] for r in self.connection.execute(
            'SELECT * FROM sd_demo_tickets WHERE lote_id=%s',(lot,)).fetchall()}

    def register(self, lot, process, index, ticket_id):
        self.connection.execute('INSERT INTO sd_demo_tickets(lote_id,proceso,indice,ticket_id) VALUES (%s,%s,%s,%s)',(lot,process,index,ticket_id))

    def context(self, seed):
        return self.connection.execute('''SELECT c.id ci_id,s.id servicio_id FROM cmdb_dispositivos d
            JOIN cmdb_lotes_sinteticos l ON l.id=d.lote_id JOIN cmdb_ci c ON c.id=d.ci_id
            JOIN cmdb_ci_servicios x ON x.ci_id=c.id JOIN services s ON s.id=x.servicio_id
            JOIN service_level_1 n ON n.code=s.level_1_code
            WHERE l.semilla=%s AND l.version='hardware-v1' AND c.activo AND s.active AND n.active AND x.activo
            ORDER BY d.indice_sintetico,s.id LIMIT 1''',(seed,)).fetchone()

    def graph_devices(self, seed):
        return [r['ci_id'] for r in self.connection.execute('''SELECT d.ci_id FROM cmdb_dispositivos d
            JOIN cmdb_lotes_sinteticos l ON l.id=d.lote_id WHERE l.semilla=%s AND l.version='hardware-v1'
            ORDER BY d.indice_sintetico LIMIT 3''',(seed,)).fetchall()]

    def relation_exists(self, a, b):
        return self.connection.execute("SELECT id FROM cmdb_relaciones WHERE origen_ci_id=%s AND destino_ci_id=%s AND tipo='depende_de'",(a,b)).fetchone()

    def report(self, lot):
        rows=self.connection.execute('''SELECT m.proceso,m.indice,t.id,t.numero,t.estado,p.estado etapa,p.datos,
            t.servicio_id,t.cola_id,t.solicitante_id,t.responsable_id
            FROM sd_demo_tickets m JOIN sd_tickets t ON t.id=m.ticket_id
            JOIN sd_procesos_ticket p ON p.ticket_id=t.id WHERE m.lote_id=%s ORDER BY m.proceso,m.indice''',(lot,)).fetchall()
        devices=self.connection.execute('SELECT count(*) cantidad,count(DISTINCT etiqueta) unicos FROM cmdb_dispositivos').fetchone()
        distribution=self.connection.execute('''WITH RECURSIVE arbol AS (
            SELECT id,nombre,origen,0 nivel FROM cmdb_clasificaciones WHERE padre_id IS NULL
            UNION ALL SELECT c.id,c.nombre,c.origen,a.nivel+1 FROM cmdb_clasificaciones c JOIN arbol a ON c.padre_id=a.id
        ) SELECT a.nombre,a.origen,a.nivel,count(d.ci_id) cantidad FROM arbol a
            LEFT JOIN cmdb_ci ci ON ci.clasificacion_id=a.id LEFT JOIN cmdb_dispositivos d ON d.ci_id=ci.id
            GROUP BY a.nombre,a.origen,a.nivel ORDER BY a.nivel,a.nombre''').fetchall()
        notifications=self.connection.execute('''SELECT n.* FROM sd_notificaciones n JOIN sd_demo_tickets m
            ON m.ticket_id=n.evento_id WHERE m.lote_id=%s ORDER BY n.id''',(lot,)).fetchall()
        return {'tickets':rows,'dispositivos':devices,'distribucion_dispositivos':distribution,'notificaciones_eventos':notifications}
