import { useState } from "react";
import MapView from "./components/MapView";
import InfoPanel from "./components/InfoPanel";
import type { PredictCompactResponse } from "./lib/api";

type LatLon = { lat: number; lon: number };

export default function App() {
  const [selected, setSelected] = useState<LatLon | null>(null);
  const [data, setData] = useState<PredictCompactResponse | null>(null);
  const [report, setReport] = useState<string | null>(null);

  return (
    <div className="w-screen h-screen flex">
      <div className="flex-1 basis-2/3">
        <MapView
          marker={selected}
          onPick={(p) => {
            setSelected(p);
            setData(null);
            setReport(null);
          }}
        />
      </div>
      <div className="w-[420px] max-w-[40vw] border-l bg-gray-50">
        <InfoPanel
          selected={selected}
          data={data}
          setData={setData}
          report={report}
          setReport={setReport}
        />
      </div>
    </div>
  );
}
