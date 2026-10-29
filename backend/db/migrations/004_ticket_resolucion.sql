-- CHECK debe rechazar NULL de forma explícita, además de la validación del servicio.
ALTER TABLE sd_tickets ADD CONSTRAINT sd_ticket_resolucion_obligatoria CHECK
 (estado NOT IN ('resuelto','cerrado') OR
  (resolucion IS NOT NULL AND length(trim(resolucion))>0));
