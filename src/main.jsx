import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AlertTriangle, Filter, Layers, MapPin, RefreshCw, Search, SlidersHorizontal, Zap } from 'lucide-react';
import './styles.css';

const API = 'http://127.0.0.1:8000/api';
const bands = ['All', 'Critical', 'High', 'Moderate', 'Low'];
const drivers = ['All', 'weather', 'vegetation', 'soil', 'imagery', 'asset'];

function bandClass(band) {
  return band.toLowerCase();
}

function riskColor(score) {
  if (score >= 80) return '#d63d2e';
  if (score >= 62) return '#d9822b';
  if (score >= 38) return '#d0a72c';
  return '#338b5f';
}

function useRiskData(filters) {
  const [data, setData] = useState({ summary: null, poles: [], segments: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.circuit !== 'All') params.set('circuit', filters.circuit);
    if (filters.band !== 'All') params.set('band', filters.band);
    if (filters.driver !== 'All') params.set('driver', filters.driver);
    params.set('min_score', filters.minScore);
    const segmentParams = new URLSearchParams(params);
    segmentParams.delete('driver');

    setLoading(true);
    Promise.all([
      fetch(`${API}/summary`).then((r) => r.json()),
      fetch(`${API}/poles?${params}`).then((r) => r.json()),
      fetch(`${API}/circuits?${segmentParams}`).then((r) => r.json()),
    ])
      .then(([summary, poles, segments]) => {
        setData({ summary, poles, segments });
        setError('');
      })
      .catch(() => setError('Backend API is not reachable. Start FastAPI on port 8000.'))
      .finally(() => setLoading(false));
  }, [filters]);

  return { ...data, loading, error };
}

function Stat({ label, value, detail }) {
  return (
    <section className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </section>
  );
}

function Filters({ filters, setFilters, circuits }) {
  return (
    <aside className="filters">
      <div className="panel-title">
        <Filter size={18} />
        <h2>Filters</h2>
      </div>
      <label>
        Circuit
        <select value={filters.circuit} onChange={(e) => setFilters({ ...filters, circuit: e.target.value })}>
          {['All', ...circuits].map((circuit) => <option key={circuit}>{circuit}</option>)}
        </select>
      </label>
      <label>
        Risk band
        <select value={filters.band} onChange={(e) => setFilters({ ...filters, band: e.target.value })}>
          {bands.map((band) => <option key={band}>{band}</option>)}
        </select>
      </label>
      <label>
        Primary driver
        <select value={filters.driver} onChange={(e) => setFilters({ ...filters, driver: e.target.value })}>
          {drivers.map((driver) => <option key={driver}>{driver}</option>)}
        </select>
      </label>
      <label>
        Minimum score
        <input
          type="range"
          min="0"
          max="95"
          value={filters.minScore}
          onChange={(e) => setFilters({ ...filters, minScore: e.target.value })}
        />
        <output>{filters.minScore}</output>
      </label>
    </aside>
  );
}

function RiskMap({ poles, segments, selectedPole, setSelectedPole }) {
  const bounds = useMemo(() => {
    const lats = poles.map((p) => p.location.lat);
    const lons = poles.map((p) => p.location.lon);
    return {
      minLat: Math.min(...lats),
      maxLat: Math.max(...lats),
      minLon: Math.min(...lons),
      maxLon: Math.max(...lons),
    };
  }, [poles]);

  const project = (point) => {
    const x = ((point.lon - bounds.minLon) / Math.max(0.0001, bounds.maxLon - bounds.minLon)) * 86 + 7;
    const y = (1 - (point.lat - bounds.minLat) / Math.max(0.0001, bounds.maxLat - bounds.minLat)) * 78 + 11;
    return { x, y };
  };

  if (!poles.length) {
    return <section className="map empty">No assets match the current filters.</section>;
  }

  return (
    <section className="map">
      <div className="map-grid" />
      <svg viewBox="0 0 100 100" aria-label="Risk map">
        {segments.map((segment) => {
          const segmentPoles = segment.pole_ids.map((id) => poles.find((p) => p.id === id)).filter(Boolean);
          const points = segmentPoles.map((pole) => {
            const p = project(pole.location);
            return `${p.x},${p.y}`;
          }).join(' ');
          return (
            <polyline
              key={segment.id}
              points={points}
              fill="none"
              stroke={riskColor(segment.risk_score)}
              strokeWidth="0.8"
              strokeOpacity="0.45"
            />
          );
        })}
        {poles.map((pole) => {
          const p = project(pole.location);
          const selected = selectedPole?.id === pole.id;
          return (
            <button
              key={pole.id}
              className="map-hit"
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
              onClick={() => setSelectedPole(pole)}
              aria-label={`${pole.id} ${pole.risk_band}`}
            >
              <span
                className={selected ? 'pin selected' : 'pin'}
                style={{ background: riskColor(pole.risk_score) }}
              />
            </button>
          );
        })}
      </svg>
      <div className="legend">
        <span><i className="low-dot" /> Low</span>
        <span><i className="moderate-dot" /> Moderate</span>
        <span><i className="high-dot" /> High</span>
        <span><i className="critical-dot" /> Critical</span>
      </div>
    </section>
  );
}

function PoleDetail({ pole }) {
  if (!pole) {
    return (
      <aside className="detail muted">
        <MapPin />
        Select a pole on the map or prioritization table.
      </aside>
    );
  }

  return (
    <aside className="detail">
      <div className="detail-head">
        <div>
          <span className={`badge ${bandClass(pole.risk_band)}`}>{pole.risk_band}</span>
          <h2>{pole.id}</h2>
          <p>{pole.circuit_id} / {pole.segment_id}</p>
        </div>
        <strong>{pole.risk_score}</strong>
      </div>
      <p className="action">{pole.recommended_action}</p>
      <div className="meta">
        <span>Confidence {(pole.confidence * 100).toFixed(0)}%</span>
        <span>Data quality {(pole.data_quality * 100).toFixed(0)}%</span>
        <span>{pole.material}, {pole.age_years} yrs</span>
      </div>
      <h3>Explainability</h3>
      {pole.factors.map((factor) => (
        <div className="factor" key={factor.name}>
          <div>
            <b>{factor.name}</b>
            {factor.proxy && <span>proxy</span>}
          </div>
          <meter min="0" max="100" value={factor.score} />
          <small>{factor.evidence}</small>
        </div>
      ))}
    </aside>
  );
}

function PriorityTable({ poles, setSelectedPole }) {
  return (
    <section className="table-wrap">
      <div className="panel-title">
        <SlidersHorizontal size={18} />
        <h2>Prioritized Poles</h2>
      </div>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Pole</th>
            <th>Risk</th>
            <th>Drivers</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {poles.slice(0, 14).map((pole) => (
            <tr key={pole.id} onClick={() => setSelectedPole(pole)}>
              <td>#{pole.priority_rank}</td>
              <td>{pole.id}</td>
              <td><span className={`badge ${bandClass(pole.risk_band)}`}>{pole.risk_score}</span></td>
              <td>{pole.top_drivers.join(', ')}</td>
              <td>{(pole.confidence * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function SegmentList({ segments }) {
  return (
    <section className="segments">
      <div className="panel-title">
        <Layers size={18} />
        <h2>Circuit Segments</h2>
      </div>
      {segments.slice(0, 6).map((segment) => (
        <article key={segment.id}>
          <div>
            <b>{segment.name}</b>
            <span>{segment.pole_count} poles / {segment.critical_poles} critical</span>
          </div>
          <strong style={{ color: riskColor(segment.risk_score) }}>{segment.risk_score}</strong>
        </article>
      ))}
    </section>
  );
}

function App() {
  const [filters, setFilters] = useState({ circuit: 'All', band: 'All', driver: 'All', minScore: '0' });
  const [selectedPole, setSelectedPole] = useState(null);
  const { summary, poles, segments, loading, error } = useRiskData(filters);
  const circuits = useMemo(() => ['CIR-1', 'CIR-2', 'CIR-3'], []);

  useEffect(() => {
    if (poles.length && !poles.some((pole) => pole.id === selectedPole?.id)) {
      setSelectedPole(poles[0]);
    }
  }, [poles, selectedPole]);

  return (
    <main>
      <header>
        <div>
          <h1>Utility Pole Risk Profiler</h1>
          <p>Weather, vegetation, soil, imagery, and asset context rolled into explainable pole and circuit risk.</p>
        </div>
        <button onClick={() => setFilters({ circuit: 'All', band: 'All', driver: 'All', minScore: '0' })}>
          <RefreshCw size={18} />
          Reset
        </button>
      </header>

      {error && <div className="error"><AlertTriangle size={18} />{error}</div>}
      {loading && <div className="loading"><Search size={18} />Loading risk profiles...</div>}

      {summary && (
        <div className="stats">
          <Stat label="Poles" value={summary.pole_count} detail={`${summary.segment_count} circuit segments`} />
          <Stat label="Average Risk" value={summary.average_risk} detail={`${summary.high_or_above_poles} high or above`} />
          <Stat label="Critical Poles" value={summary.critical_poles} detail="field attention queue" />
          <Stat label="Proxy Rate" value={`${(summary.data_proxy_rate * 100).toFixed(0)}%`} detail={`${(summary.average_confidence * 100).toFixed(0)}% avg confidence`} />
        </div>
      )}

      <div className="dashboard">
        <Filters filters={filters} setFilters={setFilters} circuits={circuits} />
        <RiskMap poles={poles} segments={segments} selectedPole={selectedPole} setSelectedPole={setSelectedPole} />
        <PoleDetail pole={selectedPole} />
      </div>

      <div className="lower">
        <PriorityTable poles={poles} setSelectedPole={setSelectedPole} />
        <SegmentList segments={segments} />
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
