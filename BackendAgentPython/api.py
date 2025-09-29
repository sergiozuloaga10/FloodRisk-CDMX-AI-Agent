# api.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os, re


import dataObserver  # tu módulo original

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Flood Model API (CDMX)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Modelos ----------
class PredictIn(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

def in_cdmx(lat: float, lon: float) -> bool:
    return 19.0 <= lat <= 19.7 and -99.36 <= lon <= -98.94

# ---------- Helper: compactar payload ----------
_hour_re = re.compile(r"^hora_(\d+)_(\d{2}h)_(probabilidad|lluvia_mm_h)$")

def build_compact_payload(resumen: Dict[str, Any], hours: Optional[int] = None) -> Dict[str, Any]:
    buckets: Dict[int, Dict[str, Any]] = {}
    for k, v in resumen.items():
        m = _hour_re.match(k)
        if not m:
            continue
        idx = int(m.group(1)); hh = m.group(2); kind = m.group(3)
        if idx not in buckets:
            buckets[idx] = {"hour": hh, "probability_pct": 0.0, "rain_mm_h": 0.0}
        if kind == "probabilidad":
            buckets[idx]["probability_pct"] = float(v)
        else:
            buckets[idx]["rain_mm_h"] = float(v)

    hours_list = [buckets[i] for i in sorted(buckets.keys())]
    if hours:
        hours_list = hours_list[:hours]

    probs = [h["probability_pct"] for h in hours_list]
    rains = [h["rain_mm_h"] for h in hours_list]
    pct_high = (sum(p > 50 for p in probs) / len(probs)) if probs else 0.0
    rain_sum = sum(rains)
    probability = max(0.0, min(0.98, 0.2 + 0.5*pct_high + 0.3*min(rain_sum/5.0, 1.0)))
    risk_level = "Bajo" if probability < 0.33 else "Moderado" if probability < 0.66 else "Alto"

    compact = {
        "location": {"lat": float(resumen.get("latitud")), "lon": float(resumen.get("longitud"))},
        "context": {
            "relief": resumen.get("relieve_tipo"),
            "nearby_water_bodies": int(resumen.get("cuerpos_agua_cercanos", 0)),
            "risk_convergence_sum": float(resumen.get("convergencia_riesgos_sumatoria", 0.0)),
            "avg_ponding_volume_l": float(resumen.get("encharcamientos_prom_volumen", 0.0)),
            "history": {
                "recurrent_ponding_sites": int(resumen.get("historico_encharcamientos_recurrentes", 0)),
                "water_reports": int(resumen.get("historico_reportes_agua", 0)),
                "calls_0311": int(resumen.get("historico_llamadas_0311", 0)),
                "calls_911": int(resumen.get("historico_llamadas_911", 0)),
            }
        },
        "atlas_risk_counts": {
            "muy_alto": int(resumen.get("riesgo_inundacion_muy_alto", 0)),
            "alto": int(resumen.get("riesgo_inundacion_alto", 0)),
            "medio": int(resumen.get("riesgo_inundacion_medio", 0)),
            "bajo": int(resumen.get("riesgo_inundacion_bajo", 0)),
            "muy_bajo": int(resumen.get("riesgo_inundacion_muy_bajo", 0)),
        },
        "green_area_risk_counts": {
            "muy_alto": int(resumen.get("inundacion_areas_verdes_muy_alto", 0)),
            "alto": int(resumen.get("inundacion_areas_verdes_alto", 0)),
            "medio": int(resumen.get("inundacion_areas_verdes_medio", 0)),
            "bajo": int(resumen.get("inundacion_areas_verdes_bajo", 0)),
            "muy_bajo": int(resumen.get("inundacion_areas_verdes_muy_bajo", 0)),
        },
        "forecast_hours": hours_list,
        "probability": round(probability, 3),
        "risk_level": risk_level,
    }
    return compact

def sanitize(obj: Dict[str, Any]) -> Dict[str, Any]:
    clean = {}
    for k, v in obj.items():
        if hasattr(v, "item"):
            v = v.item()
        clean[k] = float(v) if isinstance(v, float) else int(v) if isinstance(v, int) else v
    return clean

# ---------- Endpoints ----------
@app.post("/predict")
def predict(
    inp: PredictIn,
    compact: int = Query(1, description="1 = compacto, 0 = crudo"),
    hours: Optional[int] = Query(None, ge=1, le=24, description="limita horas de pronóstico (1–24)")
):
    if not in_cdmx(inp.lat, inp.lon):
        raise HTTPException(status_code=400, detail="Punto fuera de CDMX.")
    try:
        resumen = dataObserver.analizar_coordenadas(inp.lat, inp.lon)
        if compact == 1:
            return build_compact_payload(resumen, hours)
        return sanitize(resumen)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/explain")
def predict_explain(inp: PredictIn):
    """
    Devuelve el informe del agente LLM exactamente como el que ves en consola.
    Requiere OPENROUTER_API_KEY en el entorno.
    """
    if not in_cdmx(inp.lat, inp.lon):
        raise HTTPException(status_code=400, detail="Punto fuera de CDMX.")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY no configurada")

    try:
        # 1) Construye resumen (incluye pronostico_texto)
        resumen = dataObserver.analizar_coordenadas(inp.lat, inp.lon)

        # 2) Prepara DataFrame como espera tu agente
        df = dataObserver.pd.DataFrame([resumen])

        # 3) Inyecta pronostico_texto en el módulo (tu agente lo lee como global)
        dataObserver.pronostico_texto = resumen.get("pronostico_texto", "")

        # 4) Crea agente con tu clase original y genera informe
        agente = dataObserver.PronosticoLluviaAgent(OPENROUTER_API_KEY)
        texto = agente.generar_informe(df)  # ← mismo estilo que en consola

        # 5) También devolvemos prob/risk compactos por conveniencia
        compact = build_compact_payload(resumen, None)
        return {
            "report": texto,
            "probability": compact["probability"],
            "risk_level": compact["risk_level"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
