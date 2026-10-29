# Glosario del proyecto

| Término | Significado en esta solución |
|---|---|
| Servicio | Elemento del catálogo con código único; los controles de la fuente son 12 niveles 1 y 46 servicios nivel 2. |
| CI | Elemento de configuración; la CMDB implementa dispositivos y sus atributos. |
| Clasificación | Árbol CMDB independiente de la organización; padre existente, sin ciclos. |
| Organización | Empresa → área → departamento → sección → puesto → usuario. |
| Relación técnica | Arista entre CI; su tipo determina si admite ciclos. |
| Impacto potencial | Servicio alcanzable mediante dependencias; no equivale a caída demostrada. |
| Cola | Conjunto de tickets de un proceso con permisos y objetivos configurables. |
| Solicitante | Persona para quien se crea la solicitud; ve sus tickets en el portal. |
| Agente | Usuario autorizado para atender y tomar tickets de una cola. |
| Aprobador | Actor independiente con permiso de decidir en la cola y ciclo actuales. |
| Consulta | Rol de lectura; las concesiones adicionales no habilitan escritura. |
| Ciclo | Atención inicial o posterior a reapertura, con marcas y objetivos propios. |
| Objetivo calendario | Tiempo 24×7; no descuenta noches, fines de semana ni espera de aprobación. |
| Primera atención | Primera toma/asignación del ciclo; no es solo consultar una ficha. |
| E0–E3 / I0–I6 | Categorías de eventos/incidentes del material, con reglas complementarias explícitas. |
| Idempotencia | Repetir una carga con la misma identidad no duplica el conjunto. |
| Harness | Scripts, fixtures, comprobaciones y reportes automatizados; Docker es su entorno de ejecución. |
| Árbol modificado | Archivos que difieren del commit base; sus hashes identifican lo ejecutado. |
