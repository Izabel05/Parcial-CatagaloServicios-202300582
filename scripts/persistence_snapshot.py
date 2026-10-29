"""Snapshot de tablas funcionales de la base exclusiva de aceptación, sin usuarios ni secretos."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from psycopg import sql
from backend.app.database.connection import get_connection

TABLES={
 'service_level_1':['code'],'services':['id'],'cmdb_ci':['id'],'cmdb_dispositivos':['ci_id'],
 'cmdb_clasificaciones':['id'],'cmdb_relaciones':['id'],'cmdb_ci_servicios':['ci_id','servicio_id'],
 'cmdb_ubicaciones':['id'],'cmdb_lotes_sinteticos':['id'],'cmdb_auditoria':['id'],
 'sd_colas':['id'],'sd_tickets':['id'],'sd_historial':['id'],'sd_aprobaciones':['id'],
 'sd_comentarios':['id'],'sd_adjuntos':['id'],'sd_ticket_ci':['ticket_id','ci_id'],'sd_ticket_vinculos':['id'],
 'sd_permisos_cola':['id'],'sd_cola_responsables':['cola_id','usuario_id'],'sd_roles_usuario':['usuario_id','rol'],
 'sd_ciclos_tiempo':['ticket_id','numero'],'sd_procesos_ticket':['ticket_id'],
 'sd_evento_incidente':['evento_id'],'sd_notificaciones':['id'],'sd_faq':['id'],
 'sd_demo_lotes':['id'],'sd_demo_tickets':['lote_id','proceso','indice'],
}


def snapshot():
    with get_connection() as connection:
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        name=connection.execute('SELECT current_database() nombre').fetchone()['nombre']
        if not name.endswith('_test'):raise ValueError('La persistencia de aceptación requiere base _test')
        result={}
        for table,keys in TABLES.items():
            query=sql.SQL("SELECT count(*) cantidad,md5(COALESCE(string_agg(row_to_json(t)::text,'|' ORDER BY {}),'')) huella FROM {} t").format(
                sql.SQL(',').join(map(sql.Identifier,keys)),sql.Identifier(table))
            result[table]=connection.execute(query).fetchone()
        return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    Path(args.output).write_text(json.dumps(snapshot(),indent=2),encoding='utf-8')
