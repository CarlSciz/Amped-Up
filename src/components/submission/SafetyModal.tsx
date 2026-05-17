interface SafetyModalProps {
  onAcknowledge: () => void;
}

export function SafetyModal({ onAcknowledge }: SafetyModalProps) {
  return (
    <div className="sfm-backdrop">
      <div className="sfm-card" role="alertdialog" aria-modal="true" aria-labelledby="sfm-title">

        {/* Warning icon */}
        <div className="sfm-icon-wrap">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>

        <div className="sfm-hazard-badge">⚡ LIVE ELECTRICAL HAZARD</div>

        <h2 className="sfm-title" id="sfm-title">Downed wires are life-threatening</h2>

        <p className="sfm-body">
          A downed power line can energize the ground around it. Never assume a wire is dead — even if it's not sparking.
        </p>

        {/* 25 ft distance callout */}
        <div className="sfm-distance">
          <div className="sfm-distance-num">25 ft</div>
          <div className="sfm-distance-label">minimum safe distance from any downed wire</div>
        </div>

        {/* Safety rules */}
        <ul className="sfm-rules">
          <li>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            Do not touch the wire or anything it contacts
          </li>
          <li>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            Do not drive over a downed wire
          </li>
          <li>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            Keep others away and warn bystanders
          </li>
        </ul>

        <div className="sfm-actions">
          <a href="tel:911" className="sfm-call-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.6a16 16 0 0 0 5.95 5.95l.91-.91a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
            Call 911
          </a>
          <button className="sfm-ack-btn" onClick={onAcknowledge}>
            I understand — I'm staying 25 ft back
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </button>
        </div>

        <p className="sfm-footer">
          If there is immediate danger, call 911 before submitting a report.
        </p>
      </div>
    </div>
  );
}
