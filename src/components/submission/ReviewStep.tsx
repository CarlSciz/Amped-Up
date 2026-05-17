import { useRef, useState } from 'react';
import { CapturedPhoto, GpsCoords, SubmitReportPayload } from '../../types/submission';

interface ReviewStepProps {
  poleId: string;
  photos: CapturedPhoto[];
  location: GpsCoords | null;
  description: string;
  onDescriptionChange: (v: string) => void;
  onPhotoReplace: (index: number, photo: CapturedPhoto) => void;
  onBack: () => void;
  onSubmit: (payload: SubmitReportPayload) => Promise<void>;
}

export function ReviewStep({
  poleId,
  photos,
  location,
  description,
  onDescriptionChange,
  onPhotoReplace,
  onBack,
  onSubmit,
}: ReviewStepProps) {
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const [replacingPhotoIndex, setReplacingPhotoIndex] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleReplaceUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || replacingPhotoIndex === null) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      onPhotoReplace(replacingPhotoIndex, {
        id: crypto.randomUUID(),
        dataUrl,
        label: photos[replacingPhotoIndex]?.label ?? '',
      });
    };
    reader.readAsDataURL(file);
    setReplacingPhotoIndex(null);
    e.target.value = '';
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        pole_id: poleId,
        location: location
          ? { lat: location.lat, lon: location.lon, accuracy: location.accuracy }
          : null,
        description,
        photo_count: photos.length,
        photos,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed. Check your connection and try again.');
      setSubmitting(false);
    }
  }

  return (
    <div className="sub-screen">
      {/* Header */}
      <div className="sub-hdr">
        <button className="sub-ico-btn" onClick={onBack} aria-label="Back">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
        </button>
        <div className="sub-hdr-title">
          <span>New report</span>
          <span className="sub-hdr-sub">Step 2 of 2 · Review</span>
        </div>
        <div style={{ width: 32 }} />
      </div>

      <div className="sub-review-body">
        {/* Photos */}
        <section className="sub-section">
          <h3 className="sub-section-label">Photos ({photos.length})</h3>
          <div className="sub-review-photos">
            {photos.map((p, i) => (
              <div key={p.id} className="sub-review-photo">
                <div className="sub-review-photo-img-wrap">
                  <img src={p.dataUrl} alt={p.label} />
                  <button
                    className="sub-review-photo-replace"
                    aria-label={`Replace ${p.label} photo`}
                    onClick={() => { setReplacingPhotoIndex(i); replaceInputRef.current?.click(); }}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                      <circle cx="12" cy="13" r="4" />
                    </svg>
                  </button>
                </div>
                <span className="sub-review-photo-lbl">{p.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Location */}
        <section className="sub-section">
          <h3 className="sub-section-label">Location</h3>
          <div className="sub-loc-card">
            {location ? (
              <>
                <div className="sub-loc-row">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#86EFAC" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                  <span>{location.lat.toFixed(5)}° N, {Math.abs(location.lon).toFixed(5)}° W</span>
                </div>
                <div className="sub-loc-row sub-loc-sub">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
                  </svg>
                  <span>±{location.accuracy.toFixed(1)} m accuracy</span>
                </div>
              </>
            ) : (
              <div className="sub-loc-row sub-loc-sub">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>GPS not available — location will not be attached</span>
              </div>
            )}
            <div className="sub-loc-row sub-loc-sub" style={{ marginTop: 6 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              <span>Pole {poleId}</span>
            </div>
          </div>
        </section>

        {/* Description */}
        <section className="sub-section">
          <h3 className="sub-section-label">Description <span className="sub-section-opt">(optional)</span></h3>
          <textarea
            className="sub-textarea"
            placeholder="Describe what you observed — damage type, extent, any safety hazard…"
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
            rows={4}
            maxLength={500}
          />
          <div className="sub-char-count">{description.length} / 500</div>
        </section>

        {error && <p className="sub-error">{error}</p>}

        {/* capture="environment" forces the camera on mobile — no gallery picker for guest users */}
        <input ref={replaceInputRef} type="file" accept="image/*" capture="environment" style={{ display: 'none' }} onChange={handleReplaceUpload} />

        <button
          className="sub-submit-btn"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="sub-spin">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Submitting…
            </>
          ) : (
            <>
              Submit report
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
