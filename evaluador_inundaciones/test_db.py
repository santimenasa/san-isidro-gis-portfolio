import duckdb

con = duckdb.connect("inundaciones.db")

print("--- 1. TABLAS EXISTENTES EN LA BASE DE DATOS ---")
print(con.execute("SHOW TABLES;").df())

print("\n--- 2. CONTEO DE FILAS POR TABLA ---")
total_equip = con.execute("SELECT COUNT(*) FROM equipamiento;").fetchone()[0]
total_zonas = con.execute("SELECT COUNT(*) FROM zonas_inundacion;").fetchone()[0]

print(f"Puntos de equipamiento cargados: {total_equip}")
print(f"Polígonos de zonas de inundación cargados: {total_zonas}")

print("\n--- 3. MUESTRA DE DATOS (TABLA EQUIPAMIENTO) ---")
print(con.execute("SELECT name, tipo FROM equipamiento LIMIT 5;").df())

con.close()