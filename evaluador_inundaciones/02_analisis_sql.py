import duckdb

# 1. Conexión y carga del módulo espacial
con = duckdb.connect("inundaciones.db")
con.execute("LOAD spatial;")

print("=" * 60)
print("CONSULTA 1: Equipamientos dentro de la zona de inundación")
print("=" * 60)

# ST_Intersects devuelve TRUE cuando el punto toca o queda dentro del polígono
query_afectados = """
SELECT 
    e.tipo,
    e.name AS nombre,
    z.descripcion AS zona_afectada
FROM equipamiento e
JOIN zonas_inundacion z
  ON ST_Intersects(e.geometry, z.geometry)
ORDER BY e.tipo, e.name;
"""

df_afectados = con.execute(query_afectados).df()
print(df_afectados.to_string(index=False))
print(f"\nTotal infraestructura afectada: {len(df_afectados)}")

print("\n" + "=" * 60)
print("CONSULTA 2: Conteo agregado por Tipo (Educación vs Salud)")
print("=" * 60)

# GROUP BY para generar métricas sintéticas
query_resumen = """
SELECT 
    e.tipo,
    COUNT(*) AS cantidad_afectada
FROM equipamiento e
JOIN zonas_inundacion z
  ON ST_Intersects(e.geometry, z.geometry)
GROUP BY e.tipo;
"""

df_resumen = con.execute(query_resumen).df()
print(df_resumen.to_string(index=False))

print("\n" + "=" * 60)
print("CONSULTA 3: Clasificación y creación de la tabla final")
print("=" * 60)

# LEFT JOIN y CASE WHEN para etiquetar cada punto según su riesgo
query_crear_tabla = """
CREATE OR REPLACE TABLE evaluacion_riesgo AS
SELECT 
    e.name AS nombre,
    e.tipo,
    CASE 
        WHEN z.id_zona IS NOT NULL THEN 'Riesgo Alto (Inundable)'
        ELSE 'Riesgo Bajo (Zona Segura)'
    END AS nivel_riesgo,
    ST_AsText(e.geometry) AS geom_wkt
FROM equipamiento e
LEFT JOIN zonas_inundacion z
  ON ST_Intersects(e.geometry, z.geometry);
"""

con.execute(query_crear_tabla)

# Mostramos el balance general de riesgo
df_conteo_riesgo = con.execute("""
    SELECT 
        nivel_riesgo, 
        COUNT(*) AS total 
    FROM evaluacion_riesgo 
    GROUP BY nivel_riesgo;
""").df()

print(df_conteo_riesgo.to_string(index=False))

con.close()
print("\n¡Análisis completado! La tabla 'evaluacion_riesgo' quedó guardada.")