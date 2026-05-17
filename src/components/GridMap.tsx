import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet';
import { MapPole, Severity } from '../types';

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#FBBF24',
  low: '#10B981',
};

interface GridMapProps {
  poles: MapPole[];
  totalPoleCount: number;
  selectedPoleId: string | null;
  onSelectPole: (poleId: string) => void;
}

function FlyToSelected({ poles, selectedPoleId }: { poles: MapPole[]; selectedPoleId: string | null }) {
  const map = useMap();
  useEffect(() => {
    const pole = poles.find((p) => p.id === selectedPoleId);
    if (pole) map.panTo([pole.lat, pole.lon], { animate: true, duration: 0.4 });
  }, [selectedPoleId, poles, map]);
  return null;
}

function FitToPoles({ poles, selectedPoleId }: { poles: MapPole[]; selectedPoleId: string | null }) {
  const map = useMap();
  useEffect(() => {
    if (selectedPoleId || poles.length === 0) return;
    const points = poles.map((pole) => [pole.lat, pole.lon] as [number, number]);
    if (points.length === 1) {
      map.setView(points[0], 16);
      return;
    }
    map.fitBounds(points, { padding: [28, 28], maxZoom: 16 });
  }, [selectedPoleId, poles, map]);
  return null;
}

export function GridMap({ poles, totalPoleCount, selectedPoleId, onSelectPole }: GridMapProps) {
  const center: [number, number] = poles.length
    ? [
        poles.reduce((sum, pole) => sum + pole.lat, 0) / poles.length,
        poles.reduce((sum, pole) => sum + pole.lon, 0) / poles.length,
      ]
    : [42.3314, -83.0458];

  return (
    <div className="card map-card">
      <div className="row map-head">
        <h4>Live map - DTE OSM pole inventory</h4>
        <div className="map-legend">
          {totalPoleCount > poles.length && (
            <span className="map-count">{poles.length.toLocaleString()} of {totalPoleCount.toLocaleString()} shown</span>
          )}
          {(['critical', 'high', 'medium', 'low'] as Severity[]).map((severity) => (
            <span key={severity} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className="dot" style={{ background: SEVERITY_COLOR[severity] }} />
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </span>
          ))}
        </div>
      </div>

      <MapContainer center={center} zoom={16} className="pole-map" scrollWheelZoom>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          maxZoom={19}
        />

        {poles.map((pole) => {
          const isSelected = pole.id === selectedPoleId;
          const color = SEVERITY_COLOR[pole.severity];
          return (
            <CircleMarker
              key={pole.id}
              center={[pole.lat, pole.lon]}
              radius={isSelected ? 9 : 6}
              pathOptions={{
                color: isSelected ? '#3B82F6' : '#0B1020',
                fillColor: color,
                fillOpacity: 1,
                weight: isSelected ? 2.5 : 1.5,
              }}
              eventHandlers={{ click: () => onSelectPole(pole.id) }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={1}>
                <strong>{pole.id}</strong>
                <br />
                {pole.severity.charAt(0).toUpperCase() + pole.severity.slice(1)}
                &nbsp;-&nbsp;
                {pole.lat.toFixed(5)} N,&nbsp;{Math.abs(pole.lon).toFixed(5)} W
              </Tooltip>
            </CircleMarker>
          );
        })}

        <FlyToSelected poles={poles} selectedPoleId={selectedPoleId} />
        <FitToPoles poles={poles} selectedPoleId={selectedPoleId} />
      </MapContainer>
    </div>
  );
}
