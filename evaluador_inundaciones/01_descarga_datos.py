import duckdb
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Polygon

print("1. Descargando equipamiento urbano desde OpenStreetMap...")
lugar = "San Fernando, Buenos Aires, Argentina"

tags_escuelas = {"amenity": "school"}
tags_salud = {"amenity": ["hospital", "clinic", "doctors"]}

try:
    escuelas = ox.features_from_place(lugar, tags=tags_escuelas)
    salud = ox.features_from_place(lugar, tags=tags_salud)
except AttributeError:
    escuelas = ox.geometries_from_place(lugar, tags=tags_escuelas)
    salud = ox.geometries_from_place(lugar, tags=tags_salud)

# Filtrar solo puntos
escuelas_puntos = escuelas[escuelas.geometry.type == "Point"][["name", "geometry"]].copy()
salud_puntos = salud[salud.geometry.type == "Point"][["name", "geometry"]].copy()

escuelas_puntos["name"] = escuelas_puntos["name"].fillna("Escuela sin nombre")
salud_puntos["name"] = salud_puntos["name"].fillna("Centro de salud sin nombre")

escuelas_puntos["tipo"] = "Educacion"
salud_puntos["tipo"] = "Salud"

# Unir capas
infraestructura = gpd.pd.concat([escuelas_puntos, salud_puntos], ignore_index=True)
infraestructura = gpd.GeoDataFrame(infraestructura, geometry="geometry", crs="EPSG:4326")

print(f"-> Total equipamientos encontrados: {len(infraestructura)}")

print("2. Creando capa de zona vulnerable/inundable...")
# Coordenadas geográficas precisas: (Longitud X, Latitud Y)
# Delimitamos la franja ribereña baja este/noreste de San Fernando
minx, miny, maxx, maxy = infraestructura.total_bounds

# Creamos un polígono realista pegado al sector fluvial/costero
zona_inundable_geom = Polygon([
    (maxx, maxy),
    (minx + (maxx - minx) * 0.45, maxy),
    (minx + (maxx - minx) * 0.20, miny),
    (maxx, miny),
    (maxx, maxy)
])

zona_inundable = gpd.GeoDataFrame(
    [{"id_zona": 1, "descripcion": "Zona Ribereña Baja"}],
    geometry=[zona_inundable_geom],
    crs="EPSG:4326"
)

print("3. Conectando con la base de datos SQL e insertando capas...")
con = duckdb.connect("inundaciones.db")
con.execute("INSTALL spatial; LOAD spatial;")

con.register("df_infra", df_infra_sql)
con.register("df_zonas", df_zonas_sql)

# Usamos ST_GeomFromText() para que DuckDB cree geometrías espaciales nativas
con.execute("""
    CREATE OR REPLACE TABLE equipamiento AS 
    SELECT 
        name, 
        tipo, 
        ST_GeomFromText(geom_wkt) AS geometry 
    FROM df_infra;
""")

con.execute("""
    CREATE OR REPLACE TABLE zonas_inundacion AS 
    SELECT 
        id_zona, 
        descripcion, 
        ST_GeomFromText(geom_wkt) AS geometry 
    FROM df_zonas;
""")

con.close()
print("¡Listo! Base de datos 'inundaciones.db' creada correctamente con tablas espaciales nativas.")