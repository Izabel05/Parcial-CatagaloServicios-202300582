-- Consulta de tickets por CI sin recorrer todas las asociaciones.
CREATE INDEX sd_ticket_ci_por_ci ON sd_ticket_ci(ci_id,ticket_id);
