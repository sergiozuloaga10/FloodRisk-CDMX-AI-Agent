import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
from datetime import datetime
from zoneinfo import ZoneInfo

TOMORROW_IO_API_KEY = "publicApikey shhhh"
DEEPSEEK_API_KEY = "mySecretKey shhhh"

print("Cargando datos...")

atlas_riesgo_inundaciones = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/atlas_de_riesgo_inundaciones/atlas_de_riesgo_inundaciones.shp")
atlas_relieve = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/relieve/formas-del-relieve/formas del relieve.shp")
atlas_rios = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/rios/rios_cdmx-2/rios_cdmx/Ríos de CDMX.shp")
atlas_riesgo_precipitaciones = pd.read_csv("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/DATOS LIMPIOS/datos_limpios_riesgo_precipitaciones.csv")
atlas_convergencia_riesgos_CDMX = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/convergencia_riegos_CDMX/sintesis_riesgos/sintesis_riesgos.shp")
atlas_encharcamientos = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/presencia_de_encharcamientos/presencia-de-encharcamientos-del-ano-2000-al-2017-en-la-ciudad-de-mexico/Presencia de encharcamientos del año 2000 al 2017 en la Ciudad de México/encharcamientos_2000_2017_e.shp")
atlas_inundacion_areas_verdes = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/niveles_inundación_cobertura_áreas_verdes/epma_1/epma_1.shp")
atlas_red_hidrografica = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/red_hidrográfica_superficial/red_hidrografica-2/red_hidrografica/Red hidrográfica superficial LIDAR.shp")

historico_reportes_agua = pd.read_csv("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/DATOS LIMPIOS/reportes_de_agua_filtrados.csv")
historico_llamadas_0311 = pd.read_csv("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/DATOS LIMPIOS/locatel_filtrado.csv")
historico_llamadas_911 = pd.read_csv("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/DATOS LIMPIOS/llamadas_filtradas.csv")
historico_encharcamientos_recurrentes = gpd.read_file("/home/sergio/Documentos/InteligenciaArtificial/Proyecto1/AgenteInundacionesAlpha/sitios_recurrentes_de_encharcamiento/sitios-recurrentes-de-encharcamiento-en-ciudad-de-mexico/Sitios recurrentes de encharcamiento en Ciudad de México/sitios_mayor_recurrencia_encharcamientos.shp")

print("Datos cargados correctamente")

# coordenadas = "19.495144, -99.119287"
# coordenadas = "19.483036, -99.135044"
#coordenadas = "19.494271, -99.119528"
# coordenadas = "19.442629, -99.113787"
coordenadas = "19.304311, -99.151831"

lat, lon = map(float, coordenadas.split(","))
punto = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")

radio_metros = 200

pd.set_option('display.max_rows', None) # Muestra todas las filas 
pd.set_option('display.max_columns', None) # Muestra todas las columnas 

def obtener_pronostico_tomorrow(lat, lon):
    url = "https://api.tomorrow.io/v4/weather/forecast"
    params = {
        "location": f"{lat},{lon}",
        "apikey": TOMORROW_IO_API_KEY,
        "units": "metric",
        "timesteps": "1h"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        pronostico = data.get("timelines", {}).get("hourly", [])
        return pronostico[:24]  # Solo las siguientes 24 horas
    except Exception as e:
        print(f"⚠️ Error al obtener pronóstico: {e}")
        return []


def filtrar_por_radio(gdf, radio=radio_metros):
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    buffer = punto.to_crs(epsg=3857).buffer(radio).to_crs("EPSG:4326")
    return gdf[gdf.intersects(buffer.iloc[0])]

resumen = {
    "latitud": lat,
    "longitud": lon
}

df_riesgo = filtrar_por_radio(atlas_riesgo_inundaciones)
for nivel in ["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"]:
    resumen[f"riesgo_inundacion_{nivel.replace(' ', '_').lower()}"] = (df_riesgo['intnsdd'] == nivel).sum()

df_relieve = filtrar_por_radio(atlas_relieve)
resumen["relieve_tipo"] = ", ".join(df_relieve["NOMBRE"].unique()) if not df_relieve.empty else "No encontrado"

df_rios = filtrar_por_radio(atlas_rios)
df_red_hidro = filtrar_por_radio(atlas_red_hidrografica)
resumen["cuerpos_agua_cercanos"] = len(df_rios) + len(df_red_hidro)

df_convergencia = filtrar_por_radio(atlas_convergencia_riesgos_CDMX)
resumen["convergencia_riesgos_sumatoria"] = df_convergencia["SUMATORIA"].sum()

df_encharcamientos = filtrar_por_radio(atlas_encharcamientos)
resumen["encharcamientos_prom_volumen"] = (
    df_encharcamientos["VOLUMEN"].sum() / len(df_encharcamientos)
    if len(df_encharcamientos) > 0 else 0
)

df_areas_verdes = filtrar_por_radio(atlas_inundacion_areas_verdes)
for nivel in ["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"]:
    resumen[f"inundacion_areas_verdes_{nivel.replace(' ', '_').lower()}"] = (df_areas_verdes['INUNDACION'] == nivel).sum()

df_encharc_recurrentes = filtrar_por_radio(historico_encharcamientos_recurrentes)
resumen["historico_encharcamientos_recurrentes"] = len(df_encharc_recurrentes)

gdf_reportes = gpd.GeoDataFrame(
    historico_reportes_agua, 
    geometry=gpd.points_from_xy(historico_reportes_agua["longitud"], historico_reportes_agua["latitud"]), 
    crs="EPSG:4326"
)
resumen["historico_reportes_agua"] = len(filtrar_por_radio(gdf_reportes))

gdf_0311 = gpd.GeoDataFrame(
    historico_llamadas_0311, 
    geometry=gpd.points_from_xy(historico_llamadas_0311["longitud"], historico_llamadas_0311["latitud"]), 
    crs="EPSG:4326"
)
resumen["historico_llamadas_0311"] = len(filtrar_por_radio(gdf_0311))

gdf_911 = gpd.GeoDataFrame(
    historico_llamadas_911, 
    geometry=gpd.points_from_xy(historico_llamadas_911["longitud"], historico_llamadas_911["latitud"]), 
    crs="EPSG:4326"
)
resumen["historico_llamadas_911"] = len(filtrar_por_radio(gdf_911))

pronostico = obtener_pronostico_tomorrow(lat, lon)
for i, hora in enumerate(pronostico):
    valores = hora.get("values", {})
    timestamp = hora.get("time")
    dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    dt_local = dt_utc.astimezone(ZoneInfo("America/Mexico_City"))
    hora_col = dt_local.strftime("%Hh")

    resumen[f"hora_{i+1}_{hora_col}_probabilidad"] = valores.get("precipitationProbability", 0) # %
    resumen[f"hora_{i+1}_{hora_col}_lluvia_mm_h"] = valores.get("rainIntensity", 0) # mm/h


df_resumen = pd.DataFrame([resumen])

output_file = "/home/sergio/Escritorio//Reportes/tabla_resumen_agente4.xlsx"
df_resumen.to_csv(output_file, index=False)
print(f"\nTABLA RESUMEN EXPORTADA A EXCEL: {output_file}")

print(df_resumen)



import os
from dotenv import load_dotenv
import requests

horas_pronostico = []

for i in range(1, 25):
    prob_col = [c for c in df_resumen.columns if c.startswith(f"hora_{i}_") and c.endswith("_probabilidad")]
    mm_col = [c for c in df_resumen.columns if c.startswith(f"hora_{i}_") and c.endswith("_lluvia_mm_h")]
    
    if prob_col and mm_col:
        prob = df_resumen[prob_col[0]][0]
        mm = df_resumen[mm_col[0]][0]
        # Extraemos la hora del nombre de columna (hora del día)
        hora_dia = prob_col[0].split("_")[2]  # ejemplo: '22h'
        horas_pronostico.append(f"{hora_dia} - Probabilidad {prob}%, Lluvia {mm} mm/h")
pronostico_texto = "\n".join(horas_pronostico)


load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class PronosticoLluviaAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def generar_informe(self, df):
        """Convierte el dataframe en texto y pide a la IA un análisis/pronóstico"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Convertimos el DataFrame en un texto compacto (puedes ajustar el formato si quieres)
        df_texto = df.to_markdown(index=False)

        '''
        prompt = f"""
        Estos son datos jerárquicos de riesgo de inundación y pronóstico horario de lluvia en la zona.
        Analiza la información y genera un breve informe de riesgo, indicando si es probable que llueva,
        la severidad esperada y si se recomienda alerta. 

        Datos:
        {df_texto}
        """
        '''

        prompt = f"""
        Analiza los siguientes datos de riesgo de inundación y pronóstico de lluvia para la zona especificada:

        - **Coordenadas:** Latitud {df['latitud'][0]}, Longitud {df['longitud'][0]}
        - **Descripción de la zona:** El tipo de relieve es {df['relieve_tipo'][0]}. 
        Existen {df['cuerpos_agua_cercanos'][0]} cuerpos de agua cercanos (rios y redes hidrograficas)
        y {df['convergencia_riesgos_sumatoria'][0]} zonas con riesgos de inundación según el atlas de riesgos gubernamental.

        - **Riesgos de inundación por categoría:**  
        Muy alto: {df['riesgo_inundacion_muy_alto'][0]} | 
        Alto: {df['riesgo_inundacion_alto'][0]} | 
        Medio: {df['riesgo_inundacion_medio'][0]} |
        Bajo: {df['riesgo_inundacion_bajo'][0]} | 
        Muy bajo: {df['riesgo_inundacion_muy_bajo'][0]}


        - **Riesgos de inundación de areas verdes en la zona:**  
        Muy alto: {df['inundacion_areas_verdes_muy_alto'][0]} | 
        Alto: {df['inundacion_areas_verdes_alto'][0]} | 
        Medio: {df['inundacion_areas_verdes_medio'][0]} |
        Bajo: {df['inundacion_areas_verdes_bajo'][0]} | 
        Muy bajo: {df['inundacion_areas_verdes_muy_bajo'][0]}

        - **Promedio de encharcamiento:** {df['encharcamientos_prom_volumen'][0]} litros por evento.

        - **Histórico de reportes:**  
        Encharcamientos recurrentes: {df['historico_encharcamientos_recurrentes'][0]}  
        Reportes de agua: {df['historico_reportes_agua'][0]}  
        Llamadas 0311: {df['historico_llamadas_0311'][0]}  
        Llamadas 911: {df['historico_llamadas_911'][0]}  

        - **Pronóstico horario de lluvia (probabilidad y mm/h):**
        Considera todas las horas disponibles y calcula si el acumulado de lluvia es significativo.
        Por ejemplo, si varias horas consecutivas tienen probabilidad mayor al 50% y un acumulado 
        mayor a 2 mm, puede representar riesgo elevado.
        Estos son lso datos que tiene la zona de pronostico de lluvia en las siguentes 24 horas:
        {pronostico_texto}


        **Tu tarea:**
        1. Resume en un párrafo breve la ubicación y características de la zona usando los datos de coordenadas y relieve.
        2. Evalúa el riesgo de inundación con base en el número de áreas de riesgo, encharcamientos promedio e historial de reportes.
        3. Interpreta el pronóstico de lluvia (probabilidades y mm/h) y determina si existe un riesgo relevante de inundación en las próximas horas.
        4. Clasifica el nivel de alerta en: **Bajo, Moderado, Alto o Crítico**.
        5. Explica brevemente por qué se asignó ese nivel de alerta.
        """


        data = {
            "model": "x-ai/grok-4-fast:free",
            "messages": [
                {"role": "system", "content": "Eres un experto en meteorología y gestión de riesgos de inundaciones."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"❌ Error al generar informe: {e}"


# --- NUEVO: función pública para reutilizar desde la API ---
def analizar_coordenadas(lat, lon, radio_metros=200):
    # Punto/buffer local (evita depender de 'punto' global)
    punto_local = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")

    def filtrar_por_radio_local(gdf, radio=radio_metros):
        if getattr(gdf, "crs", None) != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        buffer = punto_local.to_crs(epsg=3857).buffer(radio).to_crs("EPSG:4326")
        return gdf[gdf.intersects(buffer.iloc[0])]

    resumen = {
        "latitud": float(lat),
        "longitud": float(lon)
    }

    # === Copia tu lógica actual pero usando filtrar_por_radio_local ===
    df_riesgo = filtrar_por_radio_local(atlas_riesgo_inundaciones)
    for nivel in ["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"]:
        resumen[f"riesgo_inundacion_{nivel.replace(' ', '_').lower()}"] = int((df_riesgo['intnsdd'] == nivel).sum())

    df_relieve = filtrar_por_radio_local(atlas_relieve)
    resumen["relieve_tipo"] = ", ".join(df_relieve["NOMBRE"].unique()) if not df_relieve.empty else "No encontrado"

    df_rios = filtrar_por_radio_local(atlas_rios)
    df_red_hidro = filtrar_por_radio_local(atlas_red_hidrografica)
    resumen["cuerpos_agua_cercanos"] = int(len(df_rios) + len(df_red_hidro))

    df_convergencia = filtrar_por_radio_local(atlas_convergencia_riesgos_CDMX)
    resumen["convergencia_riesgos_sumatoria"] = float(df_convergencia["SUMATORIA"].sum()) if "SUMATORIA" in df_convergencia else 0.0

    df_encharcamientos = filtrar_por_radio_local(atlas_encharcamientos)
    resumen["encharcamientos_prom_volumen"] = (
        float(df_encharcamientos["VOLUMEN"].sum() / len(df_encharcamientos)) if len(df_encharcamientos) > 0 and "VOLUMEN" in df_encharcamientos else 0.0
    )

    df_areas_verdes = filtrar_por_radio_local(atlas_inundacion_areas_verdes)
    for nivel in ["Muy Alto", "Alto", "Medio", "Bajo", "Muy Bajo"]:
        resumen[f"inundacion_areas_verdes_{nivel.replace(' ', '_').lower()}"] = int((df_areas_verdes.get('INUNDACION') == nivel).sum()) if 'INUNDACION' in df_areas_verdes else 0

    df_encharc_recurrentes = filtrar_por_radio_local(historico_encharcamientos_recurrentes)
    resumen["historico_encharcamientos_recurrentes"] = int(len(df_encharc_recurrentes))

    # Tabulares → Geo con puntos (idéntico a tu código)
    gdf_reportes = gpd.GeoDataFrame(
        historico_reportes_agua, 
        geometry=gpd.points_from_xy(historico_reportes_agua["longitud"], historico_reportes_agua["latitud"]), 
        crs="EPSG:4326"
    )
    resumen["historico_reportes_agua"] = int(len(filtrar_por_radio_local(gdf_reportes)))

    gdf_0311 = gpd.GeoDataFrame(
        historico_llamadas_0311, 
        geometry=gpd.points_from_xy(historico_llamadas_0311["longitud"], historico_llamadas_0311["latitud"]), 
        crs="EPSG:4326"
    )
    resumen["historico_llamadas_0311"] = int(len(filtrar_por_radio_local(gdf_0311)))

    gdf_911 = gpd.GeoDataFrame(
        historico_llamadas_911, 
        geometry=gpd.points_from_xy(historico_llamadas_911["longitud"], historico_llamadas_911["latitud"]), 
        crs="EPSG:4326"
    )
    resumen["historico_llamadas_911"] = int(len(filtrar_por_radio_local(gdf_911)))

    # Pronóstico (usa tu obtener_pronostico_tomorrow)
    pronostico = obtener_pronostico_tomorrow(lat, lon)
    horas_pronostico = []
    for i, hora in enumerate(pronostico, start=1):
        valores = hora.get("values", {})
        timestamp = hora.get("time")
        if timestamp:
            dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(ZoneInfo("America/Mexico_City"))
            hora_col = dt_local.strftime("%Hh")
        else:
            hora_col = f"h{i}"

        p = float(valores.get("precipitationProbability", 0) or 0)
        mm = float(valores.get("rainIntensity", 0) or 0)
        resumen[f"hora_{i}_{hora_col}_probabilidad"] = p
        resumen[f"hora_{i}_{hora_col}_lluvia_mm_h"] = mm
        horas_pronostico.append(f"{hora_col} - Probabilidad {p}%, Lluvia {mm} mm/h")

    resumen["pronostico_texto"] = "\n".join(horas_pronostico)

    # Heurística simple para probability/nivel (idéntico a lo que te propuse)
    probs = [v for k, v in resumen.items() if k.endswith("_probabilidad")]
    mms   = [v for k, v in resumen.items() if k.endswith("_lluvia_mm_h")]
    pct_altas = (sum(1 for p in probs if p > 50) / max(1, len(probs)))
    lluvia_acum = sum(mms)
    prob = min(0.98, max(0.0, 0.2 + 0.5*pct_altas + 0.3*min(lluvia_acum/5.0, 1.0)))
    resumen["probability"] = float(prob)
    resumen["risk_level"] = ("Bajo" if prob < 0.33 else "Moderado" if prob < 0.66 else "Alto")

    return resumen


def main():
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY no encontrada. Configúrala en el .env o ponla en el código.")
        return

    agente = PronosticoLluviaAgent(OPENROUTER_API_KEY)
    print("🤖 Agente de pronóstico inicializado\n")

    print("🔎 Generando informe basado en los datos...")
    informe = agente.generar_informe(df_resumen)
    print("\n📄 INFORME GENERADO:\n")
    print(informe)
    print("\n✅ Análisis completado")

if __name__ == "__main__":
    main()

