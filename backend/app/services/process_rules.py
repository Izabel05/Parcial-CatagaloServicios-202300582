"""Estados y decisiones del proyecto; ninguna transición se decide en React."""
INITIAL={p:('registro' if p in ('incidentes','eventos','problemas') else 'solicitud') for p in
         ('nuevos_servicios','cambios','incidentes','eventos','problemas','accesos','servicios_tecnologia')}
PATHS={
 'nuevos_servicios':['solicitud','analisis','pendiente_aprobacion','aprobado','implementacion','validacion','resuelto','cerrado'],
 'cambios':['solicitud','evaluacion','pendiente_aprobacion','aprobado','planificacion','ejecucion','validacion','resuelto','cerrado'],
 'incidentes':['registro','clasificacion','diagnostico','atencion','recuperado','resuelto','cerrado'],
 'eventos':['registro','clasificacion','evaluacion','respondido','resuelto','cerrado'],
 'problemas':['registro','investigacion','error_conocido','solucion_definitiva','resuelto','cerrado'],
 'accesos':['solicitud','validacion','pendiente_aprobacion','aprobado','provision','verificacion','resuelto','cerrado'],
 'servicios_tecnologia':['solicitud','validacion','asignacion','cumplimiento','confirmacion','resuelto','cerrado'],
}
APPROVAL_PROCESSES={'nuevos_servicios','cambios','accesos'}


def successors(process,state):
    path=PATHS[process]
    if state=='pendiente_aprobacion': return ['aprobado','rechazado']
    if state=='rechazado': return ['cerrado']
    result=[path[path.index(state)+1]] if state in path and state!='cerrado' else []
    if process=='problemas' and state=='investigacion': result.append('solucion_definitiva')
    return result


def incident_suggestion(data):
    if data.get('seguridad'): return 'I6'
    if data.get('interrupcion') is False and not data.get('degradacion'): return 'I0'
    duration=data.get('duracion_estimada_horas')
    if duration is None: return None
    if duration<=3: return 'I1'
    if duration<=8: return 'I2'
    if duration<=48: return 'I3'
    if duration<=168: return 'I4'
    # Regla complementaria: todo valor >1 semana usa I5, incluido el hueco hasta un mes.
    return 'I5'


INCIDENT_PRIORITY={'I0':4,'I1':3,'I2':3,'I3':1,'I4':1,'I5':1,'I6':1}
OUTPUTS={'evidencia_implementacion','validacion','resultado_ejecucion','resultado_pruebas',
         'diagnostico','solucion','evidencia_recuperacion','evidencia_provision',
         'evidencia_cumplimiento','confirmacion'}
