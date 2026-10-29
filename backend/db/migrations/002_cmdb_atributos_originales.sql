-- Referencias literales del Excel, separadas de vínculos técnicos y tickets reales.
ALTER TABLE cmdb_ci ADD COLUMN IF NOT EXISTS relaciones_originales TEXT;
ALTER TABLE cmdb_ci ADD COLUMN IF NOT EXISTS padres_hijos_originales TEXT;
ALTER TABLE cmdb_ci ADD COLUMN IF NOT EXISTS fecha_cambio_original DATE;
ALTER TABLE cmdb_ci ADD COLUMN IF NOT EXISTS descripcion_cambio_original TEXT;
ALTER TABLE cmdb_ci ADD COLUMN IF NOT EXISTS documentacion_relacionada TEXT;
ALTER TABLE cmdb_ci ADD COLUMN IF NOT EXISTS enlaces_incidentes_problemas TEXT;
