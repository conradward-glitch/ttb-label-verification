import React, { ChangeEvent, FormEvent, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { verifyLabel } from './services/api';
import type { ApplicationData, FieldResult, Status, VerificationResult } from './types';
import './styles.css';

const defaultApplication: ApplicationData = {
  brand_name: 'OLD TOM DISTILLERY',
  class_type: 'Kentucky Straight Bourbon Whiskey',
  alcohol_content: '45% Alc./Vol. (90 Proof)',
  net_contents: '750 mL'
};

function statusClass(status: Status): string {
  return `status status-${status.toLowerCase()}`;
}

function statusLabel(status: Status): string {
  if (status === 'PASS') return 'Pass';
  if (status === 'FAIL') return 'Fail';
  return 'Review';
}

function FieldCard({ field }: { field: FieldResult }) {
  return (
    <article className="field-card">
      <div className="field-card-header">
        <h3>{field.field}</h3>
        <span className={statusClass(field.status)}>{statusLabel(field.status)}</span>
      </div>
      <p>{field.message}</p>
      <dl>
        {field.expected && <><dt>Expected</dt><dd>{field.expected}</dd></>}
        {field.found && <><dt>Found</dt><dd>{field.found}</dd></>}
        {field.evidence && <><dt>Evidence</dt><dd>{field.evidence}</dd></>}
      </dl>
    </article>
  );
}

function App() {
  const [applicationData, setApplicationData] = useState<ApplicationData>(defaultApplication);
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const canSubmit = useMemo(() => Boolean(image && applicationData.brand_name && applicationData.class_type && applicationData.alcohol_content && applicationData.net_contents), [image, applicationData]);

  function updateField(field: keyof ApplicationData, value: string) {
    setApplicationData((current) => ({ ...current, [field]: value }));
  }

  function onImageChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setImage(selected);
    setResult(null);
    setError('');
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : '');
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!image) {
      setError('Upload a PNG or JPG label image first.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const verification = await verifyLabel(image, applicationData);
      setResult(verification);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed.');
    } finally {
      setLoading(false);
    }
  }

  function loadSampleData() {
    setApplicationData(defaultApplication);
    setResult(null);
    setError('Sample application data loaded. Upload samples/labels/passing-bourbon-label.png to run the full demo.');
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Treasury / TTB Take-Home Prototype</p>
          <h1>AI-Powered Alcohol Label Verification</h1>
          <p className="hero-copy">Upload a label, enter application data, and receive explainable PASS / FAIL / REVIEW results for the core single-label workflow.</p>
        </div>
        <div className="guardrails">
          <span>No COLA integration</span>
          <span>No database</span>
          <span>Local OCR</span>
          <span>Human review ready</span>
        </div>
      </section>

      <form className="workspace" onSubmit={onSubmit}>
        <section className="panel upload-panel">
          <div className="panel-heading">
            <h2>1. Upload Label</h2>
            <p>PNG or JPG. Clear, front-facing artwork works best.</p>
          </div>
          <label className="dropzone">
            <input type="file" accept="image/png,image/jpeg" onChange={onImageChange} />
            {previewUrl ? <img src={previewUrl} alt="Label preview" /> : <span>Choose label image</span>}
          </label>
          {image && <p className="file-name">Selected: {image.name}</p>}
        </section>

        <section className="panel form-panel">
          <div className="panel-heading row-heading">
            <div>
              <h2>2. Submitted Application Data</h2>
              <p>Simulated COLA/application record values submitted for comparison against the uploaded label.</p>
            </div>
            <button type="button" className="secondary-button" onClick={loadSampleData}>Load sample data</button>
          </div>
          <div className="form-grid">
            <label>Brand Name<input value={applicationData.brand_name} onChange={(e) => updateField('brand_name', e.target.value)} /></label>
            <label>Class/Type<input value={applicationData.class_type} onChange={(e) => updateField('class_type', e.target.value)} /></label>
            <label>Alcohol Content<input value={applicationData.alcohol_content} onChange={(e) => updateField('alcohol_content', e.target.value)} /></label>
            <label>Net Contents<input value={applicationData.net_contents} onChange={(e) => updateField('net_contents', e.target.value)} /></label>
          </div>
          <button className="primary-button" disabled={!canSubmit || loading}>{loading ? 'Verifying…' : 'Verify Label'}</button>
          {error && <div className="error-box">{error}</div>}
        </section>
      </form>

      {result && (
        <section className="results">
          <div className="overall-card">
            <div>
              <p className="eyebrow">Overall Result</p>
              <h2>{statusLabel(result.overall_status)}</h2>
              <p>{result.summary}</p>
              {result.ocr_message && <p className="ocr-note">OCR: {result.ocr_message}</p>}
            </div>
            <span className={statusClass(result.overall_status)}>{result.overall_status}</span>
          </div>

          <div className="result-grid">
            <section className="panel">
              <h2>Field-Level Verification</h2>
              <div className="field-list">
                {result.fields.map((field) => <FieldCard key={field.field} field={field} />)}
              </div>
            </section>
            <section className="panel">
              <h2>Extracted OCR Text</h2>
              <pre className="ocr-text">{result.ocr_text || 'No OCR text extracted.'}</pre>
            </section>
          </div>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
