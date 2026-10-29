"""Cálculos puros en minutos calendario; reloj inyectable para pruebas."""
from collections import Counter


def minutes(start, end):
    return max(0,(end-start).total_seconds()/60)


def objective(value, target, completed, applicable=True):
    if not applicable: return 'no_aplica'
    if target is None: return 'sin_objetivo'
    if completed: return 'cumplido' if value<=target else 'incumplido'
    return 'vencido' if value>target else 'pendiente'


def calculate(rows, now):
    current=[r for r in rows if r['actual']]
    details=[];first=[];resolved=[];attention=Counter();resolution=Counter()
    for row in rows:
        stop=row['resuelto_at'] or row['cerrado_at'] or now
        duration=minutes(row['inicio_at'],stop)
        response=minutes(row['inicio_at'],row['primera_atencion_at'] or stop)
        a=objective(response,row['objetivo_atencion_min'],row['primera_atencion_at'] is not None)
        r=objective(duration,row['objetivo_resolucion_min'],row['resuelto_at'] is not None,
                    not(row['cerrado_at'] and not row['resuelto_at']))
        attention[a]+=1;resolution[r]+=1
        if row['primera_atencion_at'] is not None: first.append(response)
        if row['resuelto_at'] is not None: resolved.append(duration)
        if row['actual']:
            details.append({'ticket_id':row['ticket_id'],'numero':row['ticket_numero'],'titulo':row['titulo'],
                'estado':row['estado'],'cola':row['cola_nombre'],'ciclo':row['numero'],'origen':row['origen'],
                'antiguedad_min':minutes(row['created_at'],now if row['estado'] not in ('resuelto','cerrado') else stop),
                'tiempo_ciclo_min':duration,'primera_atencion_min':response if row['primera_atencion_at'] else None,
                'resolucion_min':duration if row['resuelto_at'] else None,'objetivo_atencion_min':row['objetivo_atencion_min'],
                'objetivo_resolucion_min':row['objetivo_resolucion_min'],'estado_objetivo_atencion':a,'estado_objetivo_resolucion':r})
    counts=Counter(row['estado'] for row in current)
    return {'calculado_at':now,'unidad':'minutos calendario','pausas_descontadas_min':0,
        'cantidades':{s:counts[s] for s in ('abierto','en_atencion','resuelto','cerrado')},'total':len(current),
        'por_proceso':dict(Counter(r['proceso'] for r in current)),
        'por_prioridad':dict(Counter(r['prioridad'] for r in current)),
        'ciclos':len(rows),'reaperturas_registradas':sum(r['numero']>1 and r['origen']=='nativo' for r in rows),
        'ciclos_migrados':sum(r['origen']=='migracion' for r in rows),
        'promedio_primera_atencion_min':sum(first)/len(first) if first else None,
        'muestras_primera_atencion':len(first),'promedio_resolucion_min':sum(resolved)/len(resolved) if resolved else None,
        'muestras_resolucion':len(resolved),'objetivos_atencion':dict(attention),'objetivos_resolucion':dict(resolution),
        'por_cola':[{'cola_id':q,'cola':next(r['cola_nombre'] for r in current if r['cola_id']==q),
            'cantidad':sum(r['cola_id']==q for r in current)} for q in sorted({r['cola_id'] for r in current})],
        'tickets':sorted(details,key=lambda r:(-r['antiguedad_min'],r['ticket_id']))}
