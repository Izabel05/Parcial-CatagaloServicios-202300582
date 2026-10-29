# Pantallas, autoservicio y tiempos

## Navegación

El acceso a **Service Desk** contiene tres espacios independientes. Al cambiar
de espacio se reinician la búsqueda y la ficha para no mezclar sus ámbitos.

- **Portal del solicitante:** lista y ficha exclusivamente de los tickets cuyo
  solicitante es el usuario activo. Crear requiere rol solicitante o administrador.
  Permite comentarios públicos, adjuntos y confirmar sus solicitudes de tecnología.
  Un agente también puede consultar su portal; para crear necesita además el rol
  solicitante. No muestra operaciones de atención aunque el usuario tenga ese rol.
- **Consola del agente:** muestra tickets de colas con permiso consultar; permite
  tomar, asignar, atender y transferir según los permisos efectivos. Aprobadores
  disponen de sus decisiones y consulta conserva solo lectura. La pertenencia a
  una cola no otorga automáticamente todos sus permisos.
- **Administración:** colas, responsables, permisos, roles adicionales y objetivos.
  Solo aparece para administrador o un usuario con permiso administrar en alguna
  cola; este último solo gestiona esas colas. Cuentas de usuario y edición de FAQ
  siguen reservadas al administrador principal. Consulta nunca obtiene este espacio.

**CMDB** conserva su pestaña: dispositivos paginados, ubicaciones, clasificaciones,
relaciones técnicas, servicios vinculados y navegación de dependencias.

**FAQ** presenta solo artículos publicados, con búsqueda por título, pregunta o
respuesta. Los artículos pueden vincular un servicio. Administración permite crear
borradores, editarlos, publicarlos y retirarlos mediante el indicador publicado.
El contenido se muestra como texto; no se interpreta HTML. Las FAQ iniciales son
orientación funcional del proyecto, no procedimientos técnicos extraídos del Excel.

**Tablero** contiene cantidades por estado, proceso, prioridad y cola actual, antigüedad por ticket,
primera atención y resolución promedio, sus tamaños de muestra, objetivos por
ciclo y detalle paginado. Permite filtrar por proceso, cola y ámbito. Los tickets
se ordenan por mayor antigüedad. Actualizar obtiene otro corte; no hay refresco
automático oculto.

## Autorización del ámbito

El backend vuelve a validar la sesión en cada ruta. `/tickets?ambito=propios`
filtra por solicitante incluso para administradores; `ambito=colas` exige permiso
consultar en la cola. Las fichas con esos ámbitos aplican el mismo control y
omiten vínculos a tickets fuera de su ámbito. Las rutas existentes sin ámbito
conservan la regla original: propio o cola autorizada.

El tablero aplica el ámbito **antes** de calcular cantidades y promedios; no
calcula totales globales para después esconder filas. Un filtro de cola no
amplía los permisos. FAQ requiere sesión; leer borradores o escribir artículos
requiere administrador, independientemente de la visibilidad de los botones.

## Reloj y fórmulas

Todos los cálculos usan marcas PostgreSQL `TIMESTAMPTZ` y un instante de corte
UTC del servidor. La interfaz presenta las fechas en la zona local del navegador.
La unidad es **minutos calendario, 24 horas al día, siete días a la semana**.
Se incluyen noches, fines de semana, feriados y esperas por aprobación o por el
usuario. No se usa calendario laboral ni zona horaria para descontar intervalos.
Los valores se calculan sin redondear; la pantalla muestra hasta un decimal.

Cada ticket tiene uno o varios ciclos en `sd_ciclos_tiempo`. Para un ciclo:

| Dato | Definición |
|---|---|
| Inicio | Creación del ticket, o instante de su reapertura. |
| Primera atención | Primera operación válida de tomar/asignar agente dentro del ciclo. Un comentario, crear o aprobar no establece esta marca. Reasignar no la sustituye. |
| Resolución | Instante de la transición autorizada a resuelto. |
| Cierre | Instante de la transición a cerrado; no sustituye la resolución. |
| Fin usado para tiempo transcurrido | Resolución si existe; en su defecto cierre si existe; de lo contrario instante de corte. |
| Tiempo de primera atención | `(primera_atencion_at - inicio_at) / 60 segundos`, cuando existe la atención. |
| Tiempo de resolución | `(resuelto_at - inicio_at) / 60 segundos`, solo para ciclos resueltos. |
| Tiempo transcurrido del ciclo | `(fin - inicio_at) / 60 segundos`. |
| Antigüedad del ticket | Desde su creación original hasta el corte mientras está activo; para un ticket terminado se congela en la resolución o, si no la hubo, en el cierre. Incluye los intervalos entre ciclos; no es el tiempo del ciclo actual. |

Los promedios se calculan con **todos los ciclos autorizados que tienen esa
marca**, incluidos los ciclos anteriores de tickets reabiertos. Se informa la
cantidad de muestras. Una primera atención o resolución pendiente es `null`,
no cero. Cero es válido cuando las marcas coinciden. Los cálculos defensivamente
limitan diferencias negativas a cero; las marcas normales proceden del servidor.

Las cantidades por estado cuentan cada ticket una vez y representan su estado
actual, no la cantidad de transiciones. El total de ciclos y las reaperturas se
muestran aparte. Los objetivos agregados cuentan ciclos, por lo que su denominador
puede superar la cantidad de tickets.

## Objetivos y transferencias

Al crear o reabrir un ticket se copian los dos objetivos de su cola al ciclo:
primera atención y resolución, en minutos calendario. `null` significa que no hay
objetivo configurado. Se conserva la cola de origen de esos objetivos.

Editar la configuración de una cola afecta solo a ciclos nuevos. Una transferencia
o escalamiento conserva el inicio, primera atención y objetivos del ciclo; no
reinicia el reloj ni borra un incumplimiento. Los conteos y permisos se evalúan
según la **cola actual** del ticket, aunque sus objetivos provengan de otra cola.

| Estado de objetivo | Cálculo |
|---|---|
| sin_objetivo | El ciclo no tiene ese objetivo configurado/conocido. |
| pendiente | No se completó la marca y el tiempo transcurrido es menor o igual al objetivo. |
| vencido | No se completó la marca y el tiempo transcurrido supera el objetivo. |
| cumplido | La duración completada es menor o igual al objetivo. |
| incumplido | La duración completada supera el objetivo. |
| no_aplica | Para resolución, el ciclo se cerró sin pasar por resuelto, por ejemplo una solicitud rechazada. No se registra como una solución. |

Ejemplo: objetivo 60 minutos. Atender a los 60 cumple; atender a los 60.1 incumple.
Un ticket todavía sin atender a los 60 está pendiente y a los 60.1 está vencido.
La primera atención pendiente se compara con el transcurrido hasta el fin del
ciclo si este ya terminó; el reloj de ciclos terminados no sigue creciendo.

## Pausas y reaperturas

**No se descuentan pausas en esta versión**: `pausas_descontadas_min = 0`.
Las etapas pendiente de aprobación, validación y confirmación no detienen el reloj.
No existe un botón que suspenda el objetivo ni se infiere una pausa por inactividad.
Esta decisión evita presentar tiempo calendario como si fuera un SLA de horario laboral.

Reabrir un ticket resuelto/cerrado crea otro ciclo numerado, sin eliminar los
tiempos del anterior. El ciclo nuevo inicia con primera atención y resolución
vacías y objetivos copiados de la cola actual. Tomarlo de nuevo registra la
primera atención de ese ciclo, aunque el campo común del ticket conserve la
primera atención histórica para compatibilidad. El tablero usa la tabla de ciclos.
Los resultados y aprobaciones siguen las reglas de [PROCESOS.md](PROCESOS.md).

Ejemplo: primer ciclo atendido en 5 minutos y resuelto en 20. Se reabre a los dos
días y aún no se atiende: sigue siendo un ticket, con dos ciclos. El promedio de
resolución sigue en 20, con una muestra; el ciclo actual no muestra una resolución
de cero ni reutiliza la primera atención del ciclo anterior.

## Datos anteriores y limitaciones

La migración 006 preserva los tickets y materializa únicamente su ciclo vigente.
Busca en la bitácora el inicio de la última reapertura; si no existe usa creación.
Una primera atención histórica anterior al inicio de ese ciclo se deja desconocida.
**No se reconstruyen ciclos anteriores ni objetivos históricos**. Los ciclos
migrados se identifican en el tablero y no tienen objetivos, aunque hoy la cola
sí los tenga. No se inventan incumplimientos retroactivos.

Desde esta migración se conservan todos los ciclos nuevos, también los incidentes
creados automáticamente desde eventos. La tabla mantiene los objetivos adoptados
por ciclo, no un historial completo de configuraciones SLA. La bitácora de colas
sí registra quién cambió su configuración. Este tablero es operativo, sin periodos
de reporte ni exclusiones laborales configurables.

## Implementación y comprobación

- SQL y persistencia: `experience_repository.py`, migración `006_pantallas_metricas.sql`.
- Reglas, autorización y cálculos: `experience_service.py` y `desk_metrics.py`.
- Pantallas: `DeskWorkspace.jsx`, `DeskDashboard.jsx`, `FaqPanel.jsx`, y componentes
  de tickets/colas existentes separados por modo.
- Pruebas: métricas con reloj fijo y límites exactos; ámbitos portal/cola y tablero;
  publicación de FAQ; objetivos congelados; reapertura y atención por ciclo;
  migración que no inventa objetivos históricos; recorridos de navegador.

Se ejecutan con la suite predeterminada de `compose.test.yaml`. Resultados reales:
[58 métodos backend, 15 E2E y persistencia](evidencias/PANTALLAS-2026-10-28.md).
