from unittest.mock import patch
from tests.integration import test_scenarios as base


class DemoIntegrationTest(base.ScenarioIntegrationTest):
    @classmethod
    def setUpClass(cls):
        from urllib.parse import urlparse
        if not urlparse(base.TEST_DATABASE_URL).path.endswith('_test'):
            raise RuntimeError('La demostración de pruebas requiere una base exclusiva _test')
        super().setUpClass()

    def test_demo_01_37_tickets_roles_categorias_y_repeticion(self):
        from backend.app.services.demo_service import prepare_demo
        from backend.app.services.desk_service import DeskService
        from backend.app.services.process_service import ProcessService
        from backend.app.database.connection import get_connection
        first,credentials=prepare_demo(9001)
        self.assertEqual(first['tickets_creados'],37)
        self.assertEqual(len(first['colas']),7)
        self.assertTrue(all(count>=5 for count in first['por_proceso'].values()))
        self.assertEqual({r['datos']['categoria'] for r in first['tickets'] if r['proceso']=='incidentes'},set('I'+str(i) for i in range(7)))
        self.assertEqual({r['datos']['categoria'] for r in first['tickets'] if r['proceso']=='eventos'},{'E0','E1','E2','E3'})
        self.assertEqual(first['dispositivos'],{'cantidad':5000,'unicos':5000})
        self.assertEqual(len(first['notificaciones_eventos']),2)
        self.assertEqual({u['rol'] for u in first['usuarios']},{'administrador','consulta','agente','solicitante','aprobador'})
        self.assertEqual(len(credentials),6)
        ids={u['usuario']:u['id'] for u in first['usuarios']}
        ticket=next(r['id'] for r in first['tickets'] if r['proceso']=='nuevos_servicios' and r['indice']==1)
        DeskService().assign(ids['demo-agente1'],ticket)
        ProcessService().transition(ids['demo-agente1'],ticket,'analisis','Avance del evaluador que debe conservarse')
        second,credentials=prepare_demo(9001)
        self.assertEqual(len(credentials),0);self.assertEqual(second['tickets_creados'],0)
        self.assertEqual(len(second['tickets']),37);self.assertEqual(second['dispositivos'],first['dispositivos'])
        self.assertEqual([t['id'] for t in second['tickets']],[t['id'] for t in first['tickets']])
        self.assertEqual(next(r['etapa'] for r in second['tickets'] if r['id']==ticket),'analisis')
        self.assertEqual(len(second['notificaciones_eventos']),2)
        with get_connection(base.TEST_DATABASE_URL) as connection:
            self.assertEqual(connection.execute('SELECT count(*) cantidad FROM sd_demo_tickets').fetchone()['cantidad'],37)

    def test_demo_02_fallo_deliberado_revierte_tickets_y_lote(self):
        from backend.app.services.demo_service import prepare_demo
        from backend.app.database.connection import get_connection
        def fail(generator):
            generator.ticket('cambios',1,{},'solicitud')
            raise RuntimeError('Fallo deliberado de prueba; no forma parte de la aplicación')
        with get_connection(base.TEST_DATABASE_URL) as connection:
            before=connection.execute('SELECT count(*) cantidad FROM sd_tickets').fetchone()['cantidad']
        with patch('backend.app.services.demo_service.VERSION','prueba-fallo'),patch('backend.app.services.demo_service.DemoGenerator.run',fail):
            with self.assertRaisesRegex(RuntimeError,'Fallo deliberado'):prepare_demo(9001)
        with get_connection(base.TEST_DATABASE_URL) as connection:
            self.assertEqual(connection.execute('SELECT count(*) cantidad FROM sd_tickets').fetchone()['cantidad'],before)
            self.assertEqual(connection.execute("SELECT count(*) cantidad FROM sd_demo_lotes WHERE version='prueba-fallo'").fetchone()['cantidad'],0)
