import { MapContainer, TileLayer, useMapEvents, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { patchLeafletIcons } from "../leafletIcons";

type LatLon = { lat: number; lon: number };

export default function MapView({
  onPick,
  marker,
}: {
  onPick: (p: LatLon) => void;
  marker: LatLon | null;
}) {
  useEffect(() => patchLeafletIcons(), []);

  function ClickHandler() {
    useMapEvents({
      click: (e) => onPick({ lat: e.latlng.lat, lon: e.latlng.lng }),
    });
    return null;
  }

  return (
    <MapContainer center={[19.4326, -99.1332]} zoom={11} style={{ height: "100vh", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler />
      {marker && (
        <Marker position={[marker.lat, marker.lon]}>
          <Popup>
            <div className="text-sm">
              <b>Lat:</b> {marker.lat.toFixed(6)} <b>Lon:</b> {marker.lon.toFixed(6)}
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
