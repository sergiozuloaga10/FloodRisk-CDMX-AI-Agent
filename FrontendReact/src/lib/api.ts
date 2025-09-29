export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";

export type PredictRequest = { lat: number; lon: number };

export type ForecastHour = { hour: string; probability_pct: number; rain_mm_h: number };

export type PredictCompactResponse = {
  location: { lat: number; lon: number; alcaldia?: string; estado?: string; area_km2?: number };
  context: {
    relief: string;
    nearby_water_bodies: number;
    risk_convergence_sum: number;
    avg_ponding_volume_l: number;
    history: {
      recurrent_ponding_sites: number;
      water_reports: number;
      calls_0311: number;
      calls_911: number;
    };
  };
  atlas_risk_counts: Record<"muy_alto"|"alto"|"medio"|"bajo"|"muy_bajo", number>;
  green_area_risk_counts: Record<"muy_alto"|"alto"|"medio"|"bajo"|"muy_bajo", number>;
  forecast_hours: ForecastHour[];
  probability: number;    // 0..1
  risk_level: "Bajo" | "Moderado" | "Alto";
  report?: string;        // si decides devolver texto corto aquí
};

export type ExplainResponse = {
  report: string;
  probability: number;
  risk_level: "Bajo" | "Moderado" | "Alto";
};

export async function fetchPredict(body: PredictRequest, hours = 12): Promise<PredictCompactResponse> {
  const res = await fetch(`${API_BASE}/predict?compact=1&hours=${hours}`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Predict error ${res.status}`);
  return res.json();
}

export async function fetchExplain(body: PredictRequest): Promise<ExplainResponse> {
  const res = await fetch(`${API_BASE}/predict/explain`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Explain error ${res.status}`);
  return res.json();
}
