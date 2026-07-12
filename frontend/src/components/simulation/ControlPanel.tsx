import { useEffect, useRef, useState } from 'react';
import { fetchConfigSchema, fetchTopologies } from '../../api/client';
import { useSimulation } from '../../contexts/SimulationContext';
import type { ConfigSchema, SimConfig, TopologyInfo } from '../../types/models';

import { PRESETS } from '../../constants/presets';

const fallback: ConfigSchema = {
  version: 0,
  defaults: { topology: 'watts_strogatz', N: 200, T: 10000, gamma: 1, theta: 0.3, sigma: 0.01, seed: 42, p_er: 0.05, k_ws: 6, p_rewire: 0.1, m_ba: 3, n_communities: 2, p_in: 0.15, p_out: 0.02 },
  fields: {},
};

function RangeField({
  field,
  config,
  schema,
  onChange,
  disabled,
}: {
  field: keyof SimConfig;
  config: SimConfig;
  schema: ConfigSchema;
  onChange: (key: keyof SimConfig, value: number) => void;
  disabled: boolean;
}) {
  const meta = schema.fields[String(field)] ?? { label: String(field), help: '', min: 0, max: 1, step: 0.1 };
  const value = config[field] as number;
  return (
    <div className="field">
      <label htmlFor={String(field)}>
        {meta.label}
        <span className="value">{value}</span>
      </label>
      <input
        id={String(field)}
        type="range"
        min={meta.min}
        max={meta.max}
        step={meta.step}
        value={value}
        disabled={disabled}
        onChange={e => onChange(field, Number(e.target.value))}
        aria-label={meta.label}
      />
      <small>{meta.help}</small>
    </div>
  );
}

function ConfigForm({
  config,
  setConfig,
  isRunning,
  run,
  topologies,
  schema,
  onClose,
}: {
  config: SimConfig;
  setConfig: (c: SimConfig) => void;
  isRunning: boolean;
  run: () => void;
  topologies: Record<string, TopologyInfo>;
  schema: ConfigSchema;
  onClose?: () => void;
}) {
  const [activePreset, setActivePreset] = useState('');
  const change = (key: keyof SimConfig, value: number | string) =>
    setConfig({ ...config, [key]: value } as SimConfig);

  const params =
    topologies[config.topology]?.params ??
    (config.topology === 'er' ? ['p_er'] :
     config.topology === 'ba' ? ['m_ba'] :
     config.topology === 'sbm' ? ['p_in', 'p_out'] :
     ['k_ws', 'p_rewire']);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, margin: 0 }}>Simulation setup</h2>
        {onClose && (
          <button
            onClick={onClose}
            aria-label="Close configuration"
            style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--color-graphite)', lineHeight: 1 }}
          >
            ✕
          </button>
        )}
      </div>

      <div className="control-group">
      <p className="control-group-label">Question</p>
      <fieldset className="preset-options"><legend>Start from a preset</legend>{Object.values(PRESETS).map(preset => {
        const id = `preset-${preset.name.replace(/\s+/g, '-').toLowerCase()}`;
        return <div key={preset.name} className={activePreset === preset.name ? 'is-selected' : ''}><input type="radio" id={id} name="preset" value={preset.name} checked={activePreset === preset.name} onChange={() => { setActivePreset(preset.name); setConfig({ ...config, ...preset.config } as SimConfig); setTimeout(() => run(), 50); }} /><label htmlFor={id}><span><strong>{preset.name}</strong><small>{preset.desc}</small></span></label></div>
      })}</fieldset>

      <div className="field">
        <label htmlFor="topology">Network topology</label>
        <select
          id="topology"
          value={config.topology}
          disabled={isRunning}
          onChange={e => change('topology', e.target.value)}
        >
          {(['er', 'watts_strogatz', 'ba', 'sbm'] as const).map(key => (
            <option key={key} value={key}>
              {topologies[key]?.label ?? key.replace('_', ' ')}
            </option>
          ))}
        </select>
        <small>{topologies[config.topology]?.desc}</small>
      </div>
      </div>

      <div className="control-group">
      <p className="control-group-label">Population and dynamics</p>
      {(['N', 'T', 'gamma', 'theta', 'sigma'] as const).map(key => <RangeField key={key} field={key} config={config} schema={schema} onChange={change} disabled={isRunning} />)}
      </div>

      <div className="control-group">
      <p className="control-group-label">Network details</p>
      {params.map(key => (
        <RangeField key={key} field={key as keyof SimConfig} config={config} schema={schema} onChange={change} disabled={isRunning} />
      ))}
      </div>

      <div className="control-group">
      <p className="control-group-label">Reproducibility</p>
      <div className="field">
        <label htmlFor="seed">Random seed</label>
        <input
          id="seed"
          type="number"
          min="0"
          value={config.seed}
          disabled={isRunning}
          onChange={e => change('seed', Number(e.target.value))}
        />
        <small>{schema.fields.seed?.help ?? 'Reuse to reproduce a configuration.'}</small>
      </div>
      </div>

      <button
        className="btn btn-primary"
        style={{ width: '100%', marginTop: 24 }}
        disabled={isRunning}
        onClick={() => { run(); onClose?.(); }}
      >
        {isRunning ? 'Running simulation…' : 'Run simulation →'}
      </button>
    </>
  );
}

export function ControlPanel() {
  const { config, setConfig, isRunning, run } = useSimulation();
  const [topologies, setTopologies] = useState<Record<string, TopologyInfo>>({});
  const [schema, setSchema] = useState<ConfigSchema>(fallback);
  const [modalOpen, setModalOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    void fetchTopologies().then(setTopologies);
    void fetchConfigSchema().then(setSchema).catch(() => setSchema(fallback));
  }, []);

  // Open/close native dialog for mobile
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (modalOpen) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  }, [modalOpen]);

  return (
    <>
      {/* ── Mobile trigger — only visible below 800px ─────────────── */}
      <button
        className="btn btn-secondary"
        id="configure-run-trigger"
        style={{ display: 'none' }}
        aria-haspopup="dialog"
        aria-controls="config-modal"
        onClick={() => setModalOpen(true)}
      >
        ⚙ Configure run
      </button>

      {/* ── Desktop: sticky sidebar panel ─────────────────────────── */}
      <aside className="panel controls" id="config-sidebar" aria-label="Simulation configuration">
        <ConfigForm
          config={config}
          setConfig={setConfig}
          isRunning={isRunning}
          run={run}
          topologies={topologies}
          schema={schema}
        />
      </aside>

      {/* ── Mobile modal/sheet ────────────────────────────────────── */}
      <dialog
        ref={dialogRef}
        id="config-modal"
        aria-label="Simulation configuration"
        aria-modal="true"
        style={{
          border: '1px solid var(--color-hairline)',
          borderRadius: 16,
          padding: 24,
          width: 'min(92vw, 480px)',
          maxHeight: '90dvh',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-xl)',
        }}
        onClick={e => { if (e.target === dialogRef.current) setModalOpen(false); }}
        onCancel={() => setModalOpen(false)}
      >
        <ConfigForm
          config={config}
          setConfig={setConfig}
          isRunning={isRunning}
          run={run}
          topologies={topologies}
          schema={schema}
          onClose={() => setModalOpen(false)}
        />
      </dialog>
    </>
  );
}
