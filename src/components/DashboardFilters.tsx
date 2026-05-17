import { useEffect, useRef, useState } from 'react';
import { DashboardFilterOptions, DashboardFilterState, FilterOption } from '../types';

type FilterKey = keyof DashboardFilterState;

interface DashboardFiltersProps {
  options: DashboardFilterOptions;
  value: DashboardFilterState;
  onChange: (next: DashboardFilterState) => void;
}

const EMPTY_FILTERS: DashboardFilterState = {
  severities: [],
  classifications: [],
  circuits: [],
  owners: [],
  violationFamilies: [],
  violationTypeIds: [],
};

function activeCount(value: DashboardFilterState): number {
  return Object.values(value).reduce((sum, values) => sum + values.length, 0);
}

function toggle(values: string[], option: string): string[] {
  return values.includes(option) ? values.filter((value) => value !== option) : [...values, option];
}

function FilterGroup({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: FilterOption[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  if (options.length === 0) return null;

  return (
    <div className="filter-group">
      <div className="filter-label">{label}</div>
      <div className="filter-options">
        {options.map((option) => {
          const isActive = selected.includes(option.value);
          return (
            <button
              key={option.value}
              type="button"
              className={`filter-chip${isActive ? ' active' : ''}`}
              aria-pressed={isActive}
              onClick={() => onToggle(option.value)}
            >
              <span>{option.label}</span>
              <span className="filter-count">{option.count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function DashboardFilters({ options, value, onChange }: DashboardFiltersProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node | null;
      if (target && rootRef.current?.contains(target)) return;
      setOpen(false);
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  function update(key: FilterKey, option: string) {
    onChange({
      ...value,
      [key]: toggle(value[key] as string[], option),
    });
  }

  const count = activeCount(value);

  return (
    <div className="filter-bar" ref={rootRef}>
      <button
        className={`btn filter-trigger${open ? ' active' : ''}`}
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((next) => !next)}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
        </svg>
        Filters
        {count > 0 && <span className="filter-badge">{count}</span>}
      </button>

      {count > 0 && (
        <button className="btn" type="button" onClick={() => onChange(EMPTY_FILTERS)}>
          Clear
        </button>
      )}

      {open && (
        <div className="card filter-menu">
          <div className="filter-menu-head">
            <div>
              <h4>Filter map</h4>
              <div className="muted">Narrow poles and open reports.</div>
            </div>
          </div>

          <div className="filter-grid">
            <FilterGroup
              label="Severity"
              options={options.severities}
              selected={value.severities}
              onToggle={(option) => update('severities', option)}
            />
            <FilterGroup
              label="Violation"
              options={options.violationFamilies}
              selected={value.violationFamilies}
              onToggle={(option) => update('violationFamilies', option)}
            />
            <FilterGroup
              label="Pole type"
              options={options.classifications}
              selected={value.classifications}
              onToggle={(option) => update('classifications', option)}
            />
            <FilterGroup
              label="Circuit"
              options={options.circuits}
              selected={value.circuits}
              onToggle={(option) => update('circuits', option)}
            />
            <FilterGroup
              label="Owner"
              options={options.owners}
              selected={value.owners}
              onToggle={(option) => update('owners', option)}
            />
            <FilterGroup
              label="NESC type"
              options={options.violationTypes}
              selected={value.violationTypeIds}
              onToggle={(option) => update('violationTypeIds', option)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
