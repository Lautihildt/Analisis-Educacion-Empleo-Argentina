#%% Importación de librerías y configuración inicial
import pandas as pd     
import duckdb as db
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter # Importamos esta herramienta específica
import seaborn as sns
import geopandas as gpd
import textwrap
import os

# Configuración de estilo para los gráficos
plt.style.use('default')

#%% Carga de datasets originales
# Se asume que los archivos se encuentran en el directorio de trabajo
educacion_original = pd.read_excel('2022_padron_oficial_establecimientos_educativos.xlsx', skiprows=6)
produccion_original = pd.read_csv('Datos_por_departamento_actividad_y_sexo.csv')
actividades_economicas = pd.read_csv('actividades_establecimientos.csv')
padron_original = pd.read_excel('padron_poblacion.xlsx', skiprows=12)

#%% Procesamiento y Normalización: Tabla de Población (Departamentos)
# Selección de columnas relevantes del padrón
padron_original = padron_original.iloc[:, 1:5]
padron_original.dropna(axis=0, how="all", inplace=True)

departamentos_info = pd.DataFrame(columns=[
    "Departamento_Id", "Departamento_Nombre", "Provincia_Nombre", 
    "Poblacion_Jardin", "Poblacion_Primario", "Poblacion_Secundario", "Poblacion_Total"
])

# Iteración sobre el padrón para estructurar la información por departamento y rangos etarios

i = 0
while i < len(padron_original):
    valor_columna1 = str(padron_original.iloc[i, 0]).strip()
    valor_columna2 = str(padron_original.iloc[i, 1]).strip()
    
    if valor_columna1.startswith("AREA"):
        Departamento_Id = valor_columna1[-5:]
        Departamento_Nombre = valor_columna2
        Poblacion_Jardin = 0
        Poblacion_Primario = 0
        Poblacion_Secundario = 0
        Poblacion_Total = 0
        
        i += 2 # Saltar fila de encabezados internos
        
        # Sumatoria de población por rangos de edad
        while not str(padron_original.iloc[i, 0]).strip().startswith("Total"):
            edad = int(padron_original.iloc[i, 0])
            cant_habitantes = int(padron_original.iloc[i, 1])
            
            if 3 <= edad <= 5:
                Poblacion_Jardin += cant_habitantes
            elif 6 <= edad <= 12:
                Poblacion_Primario += cant_habitantes
            elif 13 <= edad <= 17:
                Poblacion_Secundario += cant_habitantes
            i += 1
            
        Poblacion_Total = int(padron_original.iloc[i, 1])
        departamentos_info.loc[len(departamentos_info)] = [
            Departamento_Id, Departamento_Nombre, None, 
            Poblacion_Jardin, Poblacion_Primario, Poblacion_Secundario, Poblacion_Total
        ]
        i += 1
    else:
        i += 1

# Corrección manual de códigos de departamento inconsistentes
departamentos_info["Departamento_Id"] = departamentos_info["Departamento_Id"].replace({"94015": "94014", "94008": "94007"})

#%% Normalización y Limpieza: Asignación de Provincias
#Creamos una tabla auxiliar para vincular provincias mediante códigos de departamento
produccion_provisoria = produccion_original.copy()

# Normalización de IDs a 5 dígitos
produccion_provisoria["in_departamentos"] = produccion_provisoria["in_departamentos"].astype(str).str.zfill(5)
produccion_provisoria = produccion_provisoria.drop_duplicates(subset="in_departamentos", keep="first")
produccion_provisoria["in_departamentos"] = produccion_provisoria["in_departamentos"].replace("06217", "06218")
produccion_provisoria = produccion_provisoria.set_index("in_departamentos")

# Asignación del nombre de provincia a la tabla principal
for i in range(len(departamentos_info)):
    id_departamento = departamentos_info.loc[i, "Departamento_Id"]
    if id_departamento in produccion_provisoria.index:
        provincia = produccion_provisoria.loc[id_departamento, "provincia"]
        if provincia == "CABA":
            provincia = "Buenos Aires"
        departamentos_info.loc[i, "Provincia_Nombre"] = provincia

# Exportación de tabla normalizada
departamentos_info.to_excel('departamentos_info.xlsx', index=False)

#%% Normalización y Limpieza: Establecimientos Productivos
establecimientos_productivos = produccion_original.iloc[:, [0, 5, 1, 8, 9, 10, 11]].copy()

# Filtrado por año 2022 y selección de columnas
establecimientos_productivos = establecimientos_productivos[establecimientos_productivos["anio"] == 2022]
establecimientos_productivos = establecimientos_productivos.iloc[:, [1, 2, 3, 4, 5, 6]]

# Renombrado y ajuste de tipos de datos
establecimientos_productivos.columns = ["Clae6", "Departamento_Id", "Genero", "Cant_Empleados", "Cant_Establecimientos", "Cant_Empresas_Exportadoras"]
establecimientos_productivos["Departamento_Id"] = establecimientos_productivos["Departamento_Id"].astype(str).str.zfill(5)
establecimientos_productivos["Departamento_Id"] = establecimientos_productivos["Departamento_Id"].replace("06217", "06218")

# Exportación de tabla normalizada
establecimientos_productivos.to_excel('establecimientos_productivos.xlsx', index=False)

#%% Normalización y Limpieza: Establecimientos Educativos
establecimientos_educativos = educacion_original.iloc[:, [1, 9, 2, 3]].copy()
establecimientos_educativos.columns = ["Cueanexo", "Departamento_Id", "Establecimiento_Nombre", "Sector"]

# Normalización de IDs de departamento (extracción de los primeros 5 dígitos del código de localidad)
establecimientos_educativos["Departamento_Id"] = establecimientos_educativos["Departamento_Id"].astype(str).str.zfill(8)
establecimientos_educativos["Departamento_Id"] = establecimientos_educativos["Departamento_Id"].str[:5]

# Corrección de códigos de departamento erróneos
datos_a_cambiar = {
    "02101": "02007", "02102": "02014", "02103": "02021", "02104": "02028",
    "02105": "02035", "02106": "02042", "02107": "02049", "02108": "02056",
    "02109": "02063", "02110": "02070", "02111": "02077", "02112": "02084",
    "02113": "02091", "02114": "02098", "02115": "02105"
}
establecimientos_educativos["Departamento_Id"] = establecimientos_educativos["Departamento_Id"].replace(datos_a_cambiar)

# Exportación de tabla normalizada
establecimientos_educativos.to_excel('establecimientos_educativos.xlsx', index=False)

#%% Normalización y Limpieza: Niveles Educativos
educacion_provisoria = educacion_original.copy()

# Limpieza de espacios en columnas clave
cols_interes = ["Común", "Nivel inicial - Jardín de infantes", "Primario", "Secundario"]
educacion_provisoria[cols_interes] = educacion_provisoria[cols_interes].astype(str).apply(lambda fila: fila.str.strip())

# Filtrado solo educación común
educacion_provisoria = educacion_provisoria[educacion_provisoria["Común"] == "1"]

niveles_educativos = pd.DataFrame(columns=["Cueanexo", "Nivel"])

# Transformación de datos 
i = 0
while i < len(educacion_provisoria):
    Cueanexo = educacion_provisoria.iloc[i, 1]  
    nivel_jardin = educacion_provisoria.iloc[i, 21]
    nivel_primaria = educacion_provisoria.iloc[i, 22]
    nivel_secundaria = educacion_provisoria.iloc[i, 23]
    
    if nivel_jardin == "1":
        niveles_educativos.loc[len(niveles_educativos)] = [Cueanexo, "Jardin"]
    if nivel_primaria == "1":
        niveles_educativos.loc[len(niveles_educativos)] = [Cueanexo, "Primaria"]
    if nivel_secundaria == "1":
        niveles_educativos.loc[len(niveles_educativos)] = [Cueanexo, "Secundaria"]
    i += 1
    
# Exportación de tabla normalizada
niveles_educativos.to_excel('niveles_educativos.xlsx', index=False)

# Exportación de actividades económicas (sin modificaciones)
actividades_economicas.to_excel('actividades_economicas.xlsx', index=False)

#%% Análisis SQL: Generación de Reportes
# Reporte 1: Infraestructura educativa y población por nivel
consulta_ee = """
SELECT d.Provincia_Nombre AS Provincia,
       d.Departamento_Nombre AS Departamento,
       SUM(CASE WHEN n.Nivel = 'Jardin' THEN 1 ELSE 0 END) AS Jardines,
       d.Poblacion_Jardin AS "Población Jardin",
       SUM(CASE WHEN n.Nivel = 'Primaria' THEN 1 ELSE 0 END) AS Primarias,
       d.Poblacion_Primario AS "Población Primaria",
       SUM(CASE WHEN n.Nivel = 'Secundaria' THEN 1 ELSE 0 END) AS Secundarias,
       d.Poblacion_Secundario AS "Población Secundaria"
FROM departamentos_info d
LEFT JOIN establecimientos_educativos e ON d.Departamento_Id = e.Departamento_Id
LEFT JOIN niveles_educativos n ON e.Cueanexo = n.Cueanexo
GROUP BY d.Provincia_Nombre, d.Departamento_Nombre, d.Poblacion_Jardin, 
         d.Poblacion_Primario, d.Poblacion_Secundario
ORDER BY Provincia ASC, Primarias DESC
"""
reporte_i = db.query(consulta_ee).to_df()
reporte_i.to_excel("reporte_infraestructura_educativa.xlsx", index=False)

# Reporte 2: Total de empleados por departamento
consulta_empleados = """
SELECT d.Provincia_Nombre AS Provincia, d.Departamento_Nombre AS Departamento,
       SUM(p.Cant_Empleados) AS "Cantidad total de empleados en 2022"
FROM departamentos_info d
LEFT JOIN establecimientos_productivos p ON d.Departamento_Id = p.Departamento_Id
GROUP BY d.Provincia_Nombre, d.Departamento_Nombre
ORDER BY Provincia ASC, "Cantidad total de empleados en 2022" DESC
"""
reporte_ii = db.query(consulta_empleados).to_df()
reporte_ii.to_excel("reporte_empleo_total.xlsx", index=False)

# Reporte 3: Empresas exportadoras y género
consulta_exportadoras = """
SELECT e.Departamento_Id,
       d.Provincia_Nombre AS Provincia,
       d.Departamento_Nombre AS Departamento,
       p."Cantidad de empresas exportadoras con mujeres",
       COUNT(e.Cueanexo) AS "Cantidad de EE",
       d.Poblacion_Total AS "Población Total"
FROM establecimientos_educativos e
LEFT JOIN departamentos_info d ON e.Departamento_Id = d.Departamento_Id
LEFT JOIN (SELECT p.Departamento_Id,
                  SUM(p.Cant_Empresas_Exportadoras) AS "Cantidad de empresas exportadoras con mujeres"
           FROM establecimientos_productivos p
           WHERE p.Genero = 'Mujeres'
           GROUP BY p.Departamento_Id) p
ON e.Departamento_Id = p.Departamento_Id
GROUP BY e.Departamento_Id, d.Provincia_Nombre, d.Departamento_Nombre, 
         d.Poblacion_Total, p."Cantidad de empresas exportadoras con mujeres"
ORDER BY "Cantidad de EE" DESC, "Cantidad de empresas exportadoras con mujeres" DESC,
         Provincia ASC, Departamento ASC
"""
reporte_iii = db.query(consulta_exportadoras).to_df()
reporte_iii.to_excel("reporte_exportadoras_genero.xlsx", index=False)

# Reporte 4: Análisis avanzado de CLAE y empleo relativo
empleos_departamento_query = """
SELECT a.Departamento_Id, SUM(a.Cant_Empleados) AS Total_Empleados, b.Provincia_Nombre
FROM establecimientos_productivos AS a
JOIN departamentos_info AS b ON a.Departamento_Id = b.Departamento_Id
GROUP BY a.Departamento_Id, b.Provincia_Nombre
ORDER BY b.Provincia_Nombre
"""
empleos_departamento = db.query(empleos_departamento_query).to_df()

departamentos_por_provincia_query = """
SELECT Provincia_Nombre, COUNT(DISTINCT Departamento_Id) AS Cantidad_Departamentos
FROM departamentos_info
GROUP BY Provincia_Nombre
"""
departamentos_por_provincia = db.query(departamentos_por_provincia_query).to_df()

empleados_por_provincia_query = """
SELECT Provincia_Nombre, SUM(Total_Empleados) AS Empleados_Provincia
FROM empleos_departamento
GROUP BY Provincia_Nombre
"""
empleados_por_provincia = db.query(empleados_por_provincia_query).to_df()

promedio_empleados_query = """
SELECT p.Provincia_Nombre, p.Empleados_Provincia, d.Cantidad_Departamentos,
       p.Empleados_Provincia * 1.0 / d.Cantidad_Departamentos AS Promedio_Provincial
FROM empleados_por_provincia p
JOIN departamentos_por_provincia d ON p.Provincia_Nombre = d.Provincia_Nombre
"""
promedio_empleados = db.query(promedio_empleados_query).to_df()

clae6_departamento_query = """ 
SELECT b.Provincia_Nombre, b.Departamento_Nombre, b.Departamento_Id, a.CLAE6, SUM(a.Cant_Empleados) AS Empleados_Rubro 
FROM establecimientos_productivos AS a 
JOIN departamentos_info AS b ON a.Departamento_Id = b.Departamento_Id 
GROUP BY b.Provincia_Nombre, b.Departamento_Nombre, a.CLAE6, b.Departamento_Id 
ORDER BY b.Provincia_Nombre, b.Departamento_Nombre, Empleados_Rubro DESC 
""" 
clae6_departamento = db.query(clae6_departamento_query).to_df()

departamentos_arriba_promedio_query = """
SELECT a.Departamento_Id, a.Total_Empleados, a.Provincia_Nombre
FROM empleos_departamento AS a
JOIN promedio_empleados AS b ON a.Provincia_Nombre = b.Provincia_Nombre
WHERE a.Total_Empleados > b.Promedio_Provincial
"""
departamentos_arriba_promedio = db.query(departamentos_arriba_promedio_query).to_df()

clae6_filtrado_query = """
SELECT a.*
FROM clae6_departamento AS a
INNER JOIN departamentos_arriba_promedio AS b ON a.Departamento_Id = b.Departamento_Id
"""
clae6_filtrado = db.query(clae6_filtrado_query).to_df()

max_por_departamento_query = """
SELECT Departamento_Id, MAX(Empleados_Rubro) AS Max_Empleados_Rubro
FROM clae6_filtrado
GROUP BY Departamento_Id
"""
max_por_departamento = db.query(max_por_departamento_query).to_df()

clae6_final_query = """
SELECT a.Provincia_Nombre, a.Departamento_Nombre, a.Departamento_Id, a.CLAE6, a.Empleados_Rubro
FROM clae6_filtrado AS a
INNER JOIN max_por_departamento AS b
ON a.Departamento_Id = b.Departamento_Id AND a.Empleados_Rubro = b.Max_Empleados_Rubro
"""
clae6_final = db.query(clae6_final_query).to_df()
clae6_final["Clae6"] = clae6_final["Clae6"].astype(str)
clae6_final["Clae3"] = clae6_final["Clae6"].str.zfill(6).str[:3]

resultado_final_query = """
SELECT Provincia_Nombre AS Nombre,
       Departamento_Nombre AS Departamento,
       Clae3 AS CLAE3,
       Empleados_Rubro AS Cant_Empleados
FROM clae6_final
"""
reporte_iv = db.query(resultado_final_query).to_df()
reporte_iv.to_excel('reporte_clae_destacado.xlsx', index=False)


# Consulta v: Ranking de eficiencia productiva por provincia
# Muestra qué departamentos tienen más empresas exportadoras dentro de cada provincia
consulta_ranking = """
SELECT 
    d.Provincia_Nombre,
    d.Departamento_Nombre,
    p.Cant_Empresas_Exportadoras,
    RANK() OVER (PARTITION BY d.Provincia_Nombre ORDER BY p.Cant_Empresas_Exportadoras DESC) as Ranking_Provincial
FROM departamentos_info d
JOIN establecimientos_productivos p ON d.Departamento_Id = p.Departamento_Id
WHERE p.Cant_Empresas_Exportadoras > 0
ORDER BY d.Provincia_Nombre, Ranking_Provincial ASC
"""

df_ranking = db.query(consulta_ranking).to_df()

# Guardamos este reporte "bonus"
df_ranking.to_excel("reporte_ranking_exportadoras.xlsx", index=False)

#%% Visualización: Análisis Gráfico


# Gráfico 1: Empleados por Provincia
empleados_x_provincia = db.query("""
SELECT d.provincia_nombre AS Provincia, 
       SUM(p.cant_empleados) AS "Cantidad de Empleados"
FROM establecimientos_productivos p 
LEFT JOIN departamentos_info d ON p.Departamento_Id = d.Departamento_Id 
GROUP BY d.provincia_nombre
ORDER BY "Cantidad de Empleados" DESC
""").to_df()

# Función para formatear: convierte 3,000,000 en "3 M"
def millones(x, pos):
    return f'{x*1e-6:.1f} M' # Divide por 1 millón y pone un decimal

# Graficamos
ax = empleados_x_provincia.plot(
    kind="barh", 
    x="Provincia",
    y="Cantidad de Empleados",
    title="Empleados por Provincia",
    legend=False,
    width=0.8,
    color="dodgerblue",
    edgecolor="black")

ax.xaxis.set_major_formatter(FuncFormatter(millones))

plt.title("Empleados por Provincia", weight="bold")
plt.xlabel("Cantidad de Empleados (en Millones)") # Aclaramos en la etiqueta
plt.ylabel("Provincia")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("grafico_empleados_provincia.png", dpi=300, bbox_inches="tight")
plt.show()

# Gráfico 2: Relación Población vs Infraestructura Educativa
plt.figure(figsize=(9, 6)) 
plt.scatter(
    reporte_i["Población Jardin"], reporte_i["Jardines"],
    color="orange", label="Nivel Inicial", alpha=0.7, edgecolors="Black", s=70
)
plt.scatter(
    reporte_i["Población Primaria"], reporte_i["Primarias"],
    color="dodgerblue", label="Nivel Primario", alpha=0.7, edgecolors="Black", s=70
)
plt.scatter(
    reporte_i["Población Secundaria"], reporte_i["Secundarias"],
    color="green", label="Nivel Secundario", alpha=0.7, edgecolors="Black", s=70
)
plt.title("Relación entre Población y Cantidad de Escuelas por Nivel Educativo", fontsize=13, weight="bold")
plt.xlabel("Población del grupo etario")
plt.ylabel("Cantidad de establecimientos educativos (EE)")
plt.legend(fontsize=12)
plt.grid(visible=True, alpha=0.5)
plt.tight_layout()
plt.savefig("grafico_poblacion_vs_educacion.png", dpi=300, bbox_inches="tight")

# Gráfico 3: Distribución de Establecimientos por Departamento (Boxplot)
ee_por_departamento = db.query("""
SELECT r.Provincia, r.Departamento, (r.Jardines + r.Primarias + r.Secundarias) AS cant_ee 
FROM reporte_i r
""").to_df()

mediana_por_provincia = db.query("""
SELECT Provincia, MEDIAN(e.cant_ee) AS mediana
FROM ee_por_departamento e
GROUP BY Provincia ORDER BY mediana ASC
""").to_df()

provincias_ordenadas = mediana_por_provincia["Provincia"].tolist()

plt.figure(figsize=(14, 6))
sns.boxplot(
    data=ee_por_departamento,
    x="Provincia",
    y="cant_ee",
    order=provincias_ordenadas,
    palette="tab20",
    flierprops=dict(markerfacecolor='red')
)
plt.xticks(rotation=45, ha="right")
plt.xlabel("Provincia")
plt.ylabel("Cantidad de Establecimientos Educativos por Departamento")
plt.title("Distribución de Establecimientos Educativos por Departamento", weight="bold")
plt.grid(True, axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("grafico_distribucion_ee.png", dpi=300, bbox_inches="tight")

# Gráfico 4: Relación Empleados y Educación cada Mil habitantes
relacion_empleados_ee = db.query("""
SELECT 
    d.Departamento_Id, d.Poblacion_Total,
    p.total_empleados,
    e.total_ee,
    (p.total_empleados / d.Poblacion_Total) * 1000 AS empleados_cada_mil,
    (e.total_ee / d.Poblacion_Total) * 1000 AS ee_cada_mil
FROM departamentos_info d
LEFT JOIN (SELECT Departamento_Id, SUM(Cant_Empleados) AS total_empleados
           FROM establecimientos_productivos GROUP BY Departamento_Id) p
    ON d.Departamento_Id = p.Departamento_Id
LEFT JOIN (SELECT Departamento_Id, COUNT(Cueanexo) AS total_ee
           FROM establecimientos_educativos GROUP BY Departamento_Id) e
    ON d.Departamento_Id = e.Departamento_Id
""").to_df()

plt.figure(figsize=(10, 6))
plt.scatter(
    relacion_empleados_ee["ee_cada_mil"], 
    relacion_empleados_ee["empleados_cada_mil"],
    color="dodgerblue",
    edgecolor="black",
    s=70,
    alpha=0.7
)
plt.xlabel("Cantidad de EE por 1000 habitantes")
plt.ylabel("Cantidad de empleados por 1000 habitantes")
plt.title("Relación entre empleados y EE cada mil habitantes", weight="bold")
plt.grid(True, alpha=0.4)
plt.tight_layout()
plt.savefig("grafico_empleados_vs_educacion_mil_hab.png", dpi=300, bbox_inches="tight")

# Gráfico 5: Participación Femenina por Sector 

consulta_letras = """
SELECT 
    t2.Letra_Desc AS Actividad,
    CAST(SUM(CASE WHEN t1.Genero = 'Mujeres' THEN t1.Cant_Empleados ELSE 0 END) AS FLOAT) / SUM(t1.Cant_Empleados) AS prop_mujeres
FROM establecimientos_productivos AS t1
INNER JOIN actividades_economicas AS t2 
    ON t1.Clae6 = t2.Clae6
GROUP BY t2.Letra_Desc
ORDER BY prop_mujeres DESC
"""
df_letras = db.query(consulta_letras).to_df()

# Formateo de texto para etiquetas
df_letras["Actividad"] = df_letras["Actividad"].str.title()

def cortar_texto(texto):
    return textwrap.fill(str(texto), width=40)

df_letras["Actividad"] = df_letras["Actividad"].apply(cortar_texto)

# Selección de extremos (Top 5 y Bottom 5)
top5 = df_letras.head(5)
bottom5 = df_letras.tail(5)
df_final = pd.concat([top5, bottom5])
df_final = df_final.iloc[::-1]

promedio_global = db.query("""
    SELECT CAST(SUM(CASE WHEN Genero = 'Mujeres' THEN Cant_Empleados ELSE 0 END) AS FLOAT) / SUM(Cant_Empleados) 
    FROM establecimientos_productivos
""").fetchone()[0]

plt.figure(figsize=(12, 9))
plt.barh(
    df_final["Actividad"],
    df_final["prop_mujeres"], 
    color="dodgerblue", 
    edgecolor="black",
    height=0.7
)
plt.axvline(promedio_global, color="red", linestyle="--", label=f"Promedio País: {promedio_global:.2%}")
plt.xlabel("Proporción de mujeres (0.0 a 1.0)")
plt.title("Participación femenina por Sector (Top 5 y Bottom 5)", weight="bold", fontsize=14)
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig("grafico_participacion_femenina.png", dpi=300, bbox_inches="tight")

#%% Visualización: Mapas Geoespaciales
# Carga del shapefile de departamentos
gdf_mapa = gpd.read_file("departamentoPolygon.shp")
gdf_mapa['in1'] = gdf_mapa['in1'].astype(str)
relacion_empleados_ee['Departamento_Id'] = relacion_empleados_ee['Departamento_Id'].astype(str)

# Fusión de datos espaciales y estadísticos
gdf_final = gdf_mapa.merge(relacion_empleados_ee, 
                           left_on='in1', 
                           right_on='Departamento_Id', 
                           how='left')

# Filtrado geográfico (exclusión de Antártida e islas del Atlántico Sur) y reproyección
gdf_continental = gdf_final[gdf_final.geometry.centroid.y > -60].copy()
gdf_continental = gdf_continental.to_crs(epsg=5346)

# Creación de capa de provincias (disolución de límites departamentales)
gdf_continental['provincia_id'] = gdf_continental['in1'].str.slice(0, 2)
gdf_temp = gdf_continental.copy()
gdf_temp['geometry'] = gdf_temp.geometry.buffer(200) # Buffer para corregir topología
gdf_provincias = gdf_temp.dissolve(by='provincia_id')

# Mapa 1: Distribución Total de Empleados
fig, ax = plt.subplots(1, 1, figsize=(10, 9.5)) 
cax = fig.add_axes([0.30, 0.12, 0.40, 0.02]) 

gdf_continental.plot(column='total_empleados',  
                     cmap='YlOrRd',
                     linewidth=0.1,       
                     edgecolor='0.5',
                     vmax=40000,    
                     legend=True,
                     cax=cax,
                     legend_kwds={'label': "Total de Empleados Registrados", 'orientation': "horizontal"},
                     missing_kwds={'color': 'lightgrey', 'label': 'Sin datos'}, 
                     ax=ax)

gdf_provincias.plot(ax=ax, 
                    facecolor='none',  
                    edgecolor='black', 
                    linewidth=1.2)

ax.set_xlim(2.5e6, 6.0e6) 
ax.set_ylim(3.6e6, 7.6e6) 
ax.set_axis_off()
ax.set_title("Cantidad Total de Empleados por Departamento\n(Argentina Continental)", fontsize=18)

plt.savefig("mapa_geo_empleados.png", dpi=300, bbox_inches='tight')

# Mapa 2: Distribución de Establecimientos Educativos
# Nota: Se reutilizan los dataframes geoespaciales ya procesados
fig, ax = plt.subplots(1, 1, figsize=(10, 9.5)) 
cax = fig.add_axes([0.30, 0.12, 0.40, 0.02]) 

gdf_continental.plot(column='total_ee',         
                     cmap='YlOrRd',
                     linewidth=0.1,       
                     edgecolor='0.5',
                     vmax=400,    
                     legend=True,
                     cax=cax,
                     legend_kwds={'label': "Total de Establecimientos Educativos", 'orientation': "horizontal"},
                     missing_kwds={'color': 'lightgrey', 'label': 'Sin datos'}, 
                     ax=ax)

gdf_provincias.plot(ax=ax, 
                    facecolor='none',  
                    edgecolor='black', 
                    linewidth=1.2)

ax.set_xlim(2.5e6, 6.0e6) 
ax.set_ylim(3.6e6, 7.6e6) 
ax.set_axis_off()
ax.set_title("Cantidad Total de Establecimientos Educativos\n(Argentina Continental)", fontsize=18)

plt.savefig("mapa_geo_educacion.png", dpi=300, bbox_inches='tight')
