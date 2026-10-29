from collections import defaultdict, deque
from datetime import datetime, timezone

from backend.app.repositories.cmdb_repository import CmdbRepository


class CmdbError(ValueError):
    pass


class CmdbNotFound(CmdbError):
    pass


class CmdbService:
    def __init__(self, repository=None):
        self.repository = repository or CmdbRepository()

    @staticmethod
    def require(repo, entity, entity_id, active=False):
        row = repo.get(entity, entity_id)
        if not row:
            raise CmdbNotFound('Registro no encontrado')
        flag = 'is_active' if entity == 'users' else 'active' if entity == 'services' else 'activo'
        if active and row.get(flag) is not True:
            raise CmdbError('La referencia debe estar activa y validada')
        return row

    def catalogs(self, entity):
        with self.repository.transaction() as repo:
            return repo.catalogs(entity)

    def save_catalog(self, entity, values, actor, entity_id=None):
        with self.repository.transaction(write=True) as repo:
            before = self.require(repo, entity, entity_id) if entity_id else None
            if entity == 'ubicaciones':
                if values.get('padre_id') is not None:
                    raise CmdbError('Las ubicaciones no usan la jerarquía de clasificaciones')
                values = {k: v for k, v in values.items() if k != 'padre_id'}
            elif values.get('padre_id'):
                parent = values['padre_id']
                self.require(repo, entity, parent, True)
                ancestors = repo.ancestors(parent)
                if any(x['id'] == entity_id for x in ancestors):
                    raise CmdbError('La clasificación no puede formar ciclos')
                if not all(x['activo'] for x in ancestors):
                    raise CmdbError('La ruta de clasificación contiene padres inactivos')
            if before and not values['activo'] and repo.dependencies(entity, entity_id):
                raise CmdbError('Existen dependencias activas; resuélvalas antes de desactivar')
            result = repo.save(entity, values, entity_id)
            repo.audit(entity, result['id'], actor, 'editar' if before else 'crear', before, result)
            return result

    def deactivate(self, entity, entity_id, actor):
        with self.repository.transaction(write=True) as repo:
            before = self.require(repo, entity, entity_id)
            if entity != 'relaciones' and repo.dependencies(entity, entity_id):
                raise CmdbError('Existen dependencias activas; desvincúlelas antes de desactivar')
            result = repo.save(entity, {'activo': False}, entity_id)
            repo.audit(entity, entity_id, actor, 'desactivar', before, result)
            if entity == 'relaciones':
                for ci_id in (before['origen_ci_id'], before['destino_ci_id']):
                    repo.audit('ci', ci_id, actor, 'desactivar_relacion', before, result)
            return result

    def save_ci(self, values, actor, entity_id=None):
        values = dict(values)
        physical = values.pop('es_dispositivo')
        tag = values.pop('etiqueta')
        with self.repository.transaction(write=True) as repo:
            before = self.require(repo, 'ci', entity_id) if entity_id else None
            if before and before['codigo'].startswith('SYN-') and values['codigo'] != before['codigo']:
                raise CmdbError('El código del lote sintético es estable y no se puede renombrar')
            if not before and values['codigo'].startswith('SYN-'):
                raise CmdbError('El prefijo SYN- está reservado para el generador')
            old_device = repo.device(entity_id) if entity_id else None
            if old_device and not physical:
                raise CmdbError('No se permite convertir un dispositivo físico en software ni perder su lote')
            classification = self.require(repo, 'clasificaciones', values['clasificacion_id'], True)
            ancestors = repo.ancestors(classification['id'])
            if not all(c['activo'] for c in ancestors):
                raise CmdbError('Clasificación con ancestros inactivos')
            source_types = {c['nombre'].casefold() for c in ancestors}
            if physical and 'hardware' not in source_types:
                raise CmdbError('Un dispositivo debe pertenecer a Hardware o a una subclase documentada')
            if not physical and values['atributos_tecnicos']:
                raise CmdbError('Los atributos técnicos definidos son aplicables a dispositivos Hardware')
            if physical and (not tag or not values['ubicacion_id'] or not values['responsable_usuario_id']):
                raise CmdbError('Dispositivo requiere etiqueta, ubicación y responsable')
            for key, entity in [('ubicacion_id', 'ubicaciones'), ('responsable_usuario_id', 'users')]:
                if values[key]:
                    self.require(repo, entity, values[key], True)
            if before and not values['activo'] and repo.dependencies('ci', entity_id):
                raise CmdbError('El CI tiene relaciones o servicios activos')
            values['updated_at'] = datetime.now(timezone.utc)
            result = repo.save('ci', values, entity_id)
            device = repo.save_device(result['id'], tag) if physical else None
            repo.audit('ci', result['id'], actor, 'editar' if before else 'crear',
                       {**before, 'dispositivo': old_device} if before else None,
                       {**result, 'dispositivo': device})
            return result

    def list_ci(self, **filters):
        with self.repository.transaction() as repo:
            return repo.list_ci(**filters)

    def detail(self, ci_id):
        with self.repository.transaction() as repo:
            row = self.require(repo, 'ci', ci_id)
            return {**row, 'dispositivo': repo.device(ci_id),
                    'clasificacion_completa': repo.ancestors(row['clasificacion_id']),
                    'relaciones': repo.relations(ci_id), 'servicios': repo.linked_services(ci_id),
                    'historial': repo.history('ci', ci_id)}

    def types(self):
        with self.repository.transaction() as repo:
            return repo.relation_types()

    @staticmethod
    def reachable(edges, start, target):
        graph = defaultdict(list)
        for row in edges:
            graph[row['origen_ci_id']].append(row['destino_ci_id'])
        pending, visited = [start], set()
        while pending:
            node = pending.pop()
            if node == target:
                return True
            if node not in visited:
                visited.add(node)
                pending.extend(graph[node])
        return False

    def save_relation(self, values, actor, relation_id=None):
        values = dict(values)
        a, b, kind = values['origen_ci_id'], values['destino_ci_id'], values['tipo']
        if a == b:
            raise CmdbError('Un CI no puede relacionarse consigo mismo')
        with self.repository.transaction(write=True) as repo:
            before = self.require(repo, 'relaciones', relation_id) if relation_id else None
            self.require(repo, 'ci', a, True)
            self.require(repo, 'ci', b, True)
            if kind == 'conectado_a':
                values['origen_ci_id'], values['destino_ci_id'] = sorted((a, b))
            else:
                kinds = ['depende_de', 'alojado_en'] if kind in ('depende_de', 'alojado_en') else [kind]
                edges = repo.graph(kinds)
                # Excluir la arista que se reemplaza durante edición.
                if before:
                    edges = [e for e in edges if not (e['origen_ci_id'] == before['origen_ci_id']
                             and e['destino_ci_id'] == before['destino_ci_id'] and e['tipo'] == before['tipo'])]
                if self.reachable(edges, b, a):
                    raise CmdbError('La relación produciría un ciclo no permitido')
            values.update(activo=True, created_by=before['created_by'] if before else actor)
            result = repo.save('relaciones', values, relation_id)
            repo.audit('relaciones', result['id'], actor, 'editar' if before else 'crear', before, result)
            for ci_id in {a, b} | ({before['origen_ci_id'], before['destino_ci_id']} if before else set()):
                repo.audit('ci', ci_id, actor, 'relacion', before, result)
            return result

    def service_link(self, ci_id, service_id, actor, active=True):
        with self.repository.transaction(write=True) as repo:
            self.require(repo, 'ci', ci_id, active)
            self.require(repo, 'services', service_id, active)
            before = repo.linked_services(ci_id)
            result = repo.link_service(ci_id, service_id, active)
            repo.audit('ci', ci_id, actor, 'vincular_servicio' if active else 'desvincular_servicio', before, result)
            return result

    def impact(self, ci_id, limit=5000):
        with self.repository.transaction() as repo:
            self.require(repo, 'ci', ci_id)
            inverse = defaultdict(list)
            for edge in repo.graph(['depende_de', 'alojado_en']):
                inverse[edge['destino_ci_id']].append(edge['origen_ci_id'])
            parents = {ci_id: None}
            pending = deque([ci_id])
            truncated = False
            while pending:
                node = pending.popleft()
                for dependent in inverse[node]:
                    if dependent in parents:
                        continue
                    if len(parents) >= limit:
                        truncated = True
                        continue
                    parents[dependent] = node
                    pending.append(dependent)
            services = {}
            for service in repo.impact_services(list(parents)):
                if service['id'] in services:
                    continue
                path, current = [], service['ci_id']
                while current is not None:
                    path.append(current)
                    current = parents[current]
                services[service['id']] = {**service, 'ruta_ci': list(reversed(path))}
            return {'ci_id': ci_id, 'alcanzados': len(parents), 'truncado': truncated,
                    'servicios_potencialmente_afectados': list(services.values()),
                    'advertencia': 'Una dependencia no demuestra una interrupción efectiva.'}

    def report(self):
        with self.repository.transaction() as repo:
            counts = repo.report()
            for row in counts:
                row['nivel'] = len(repo.ancestors(row['id']))
            total = repo.list_ci('', None, None, True, True, 1, 1)['total']
            return {'dispositivos_activos': total, 'por_clasificacion': counts,
                    'jerarquia_docente_multinivel_verificada': False}
