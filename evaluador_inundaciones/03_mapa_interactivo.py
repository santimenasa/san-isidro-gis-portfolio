import duckdb
import geopandas as gpd
import folium
from shapely import wkt

# 1. Extraer los datos ya evaluados desde DuckDB
con = duckdb.connect("inundaciones.db")
con.execute("LOAD spatial;")
df_riesgo = con.execute("SELECT nombre, tipo, nivel_riesgo, geom_wkt FROM evaluacion_riesgo;").df()
con.close()

# 2. Reconstruir geometrías en GeoPandas
df_riesgo["geometry"] = df_riesgo["geom_wkt"].apply(wkt.loads)
gdf_riesgo = gpd.GeoDataFrame(df_riesgo, geometry="geometry", crs="EPSG:4326")

# 3. Delimitar la mancha calculando la envolvente de los puntos en riesgo real
gdf_rojos = gdf_riesgo[gdf_riesgo["nivel_riesgo"].str.contains("Alto")].copy()
gdf_rojos_utm = gdf_rojos.to_crs(epsg=5347)
mancha_utm = gdf_rojos_utm.unary_union.convex_hull.buffer(350)

gdf_mancha = gpd.GeoDataFrame(
    [{"zona": "Área de Afectación"}],
    geometry=[mancha_utm],
    crs="EPSG:5347"
).to_crs(epsg=4326)

# 4. Configurar el mapa con Esri Canvas (sin API key, sin 403, sin marcas de agua)
centro_lat = gdf_riesgo.geometry.y.mean()
centro_lon = gdf_riesgo.geometry.x.mean()

m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13, tiles=None)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
    name="Esri Base Gris"
).add_to(m)

# 5. Dibujar el polígono de inundación
folium.GeoJson(
    gdf_mancha,
    name="Zona de Afectación",
    style_function=lambda x: {
        "fillColor": "#3182bd",
        "color": "#08519c",
        "weight": 2,
        "fillOpacity": 0.35
    }
).add_to(m)

# 6. Dibujar los marcadores clasificados
for _, fila in gdf_riesgo.iterrows():
    es_alto = "Alto" in fila["nivel_riesgo"]
    color = "red" if es_alto else "green"
    icono = "warning" if es_alto else "ok"
    
    html = f"""
    <b>{fila['nombre']}</b><br>
    Tipo: {fila['tipo']}<br>
    Estado: <b style='color:{color};'>{fila['nivel_riesgo']}</b>
    """
    
    folium.Marker(
        location=[fila.geometry.y, fila.geometry.x],
        popup=folium.Popup(html, max_width=240),
        tooltip=fila['nombre'],
        icon=folium.Icon(color=color, icon=icono)
    ).add_to(m)

folium.LayerControl().add_to(m)
m.save("mapa_riesgo_inundacion.html")
print("Listo: 'mapa_riesgo_inundacion.html' generado correctamente.")