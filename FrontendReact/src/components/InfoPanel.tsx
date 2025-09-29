import { useState } from "react";
import { fetchPredict, fetchExplain, type PredictCompactResponse } from "../lib/api";

type LatLon = { lat: number; lon: number };

export default function InfoPanel({
  selected,
  data,
  setData,
  report,
  setReport,
}: {
  selected: LatLon | null;
  data: PredictCompactResponse | null;
  setData: (d: PredictCompactResponse | null) => void;
  report: string | null;
  setReport: (r: string | null) => void;
}) {
  const [loading, setLoading] = useState<"idle" | "predict" | "explain">("idle");
  const [error, setError] = useState<string | null>(null);
  const coordText = selected ? `${selected.lat.toFixed(6)}, ${selected.lon.toFixed(6)}` : "N/D";
  const nivel = data?.risk_level ?? "N/D";
  const prob = data ? `${(data.probability * 100).toFixed(1)}%` : "N/D";

  async function handlePredict() {
    if (!selected) return;
    setError(null);
    setReport(null);
    setLoading("predict");
    try {
      const res = await fetchPredict({ lat: selected.lat, lon: selected.lon }, 12);
      setData(res);
      // intenta explain; si el backend no tiene key, no truenes la UI
      setLoading("explain");
      try {
        const ex = await fetchExplain({ lat: selected.lat, lon: selected.lon });
        setReport(ex.report);
      } catch {
        setReport(null);
      }
    } catch (e: any) {
      setError(e.message ?? "Error consultando la predicción.");
    } finally {
      setLoading("idle");
    }
  }

  return (
    <div className="h-screen w-full flex flex-col">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold">Riesgo de Inundaciones CDMX</h1>
        <p className="text-sm text-gray-600 mt-1">Haz click en cualquier lugar del mapa para consultar el riesgo de inundación.</p>
      </div>

      <div className="p-4">
        <div className="text-sm mb-2"><b>Coordenadas:</b> {coordText}</div>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          disabled={!selected || loading !== "idle"}
          onClick={handlePredict}
        >
          {loading === "predict" ? "Consultando..." : loading === "explain" ? "Obteniendo informe..." : "Consultar predicción"}
        </button>
      </div>

      <div className="px-4 pb-4 overflow-auto">
        <div className="rounded-xl border shadow-sm p-4 bg-white">
          <h2 className="font-semibold text-lg mb-2">Información de la ubicación</h2>

          <div className="text-sm space-y-1">
            <div><b>Nivel de riesgo:</b> {nivel} {data && <span>({prob})</span>}</div>
          </div>

          {error && <div className="text-red-600 text-sm mt-2">{error}</div>}

          {data && (
            <>
              <div className="mt-3">
                <h3 className="font-medium">Pronóstico (siguientes horas)</h3>
                <ul className="list-disc ml-5 text-sm">
                  {data.forecast_hours.slice(0, 6).map((h, i) => (
                    <li key={i}>{h.hour}: {h.probability_pct}% • {h.rain_mm_h} mm/h</li>
                  ))}
                </ul>
              </div>

              <div className="mt-3 text-sm">
                <b>Relieve:</b> {data.context.relief || "N/D"} • <b>Cuerpos de agua cercanos:</b> {data.context.nearby_water_bodies}
              </div>
            </>
          )}

          {report && (
            <div className="mt-3">
              <h3 className="font-medium">Interpretación</h3>
              <div className="text-sm whitespace-pre-wrap">{report}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
