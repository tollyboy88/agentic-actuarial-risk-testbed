'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, CheckCircle2, Database, FlaskConical, GitBranch,
  Play, RefreshCw, Search, ShieldCheck, Waypoints,
} from 'lucide-react';
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

type Row = Record<string, string | number | boolean | null>;
type Payload = {
  meta: Record<string, string | number>;
  topologies: Row[]; faults: Row[]; detection_heatmap: Row[]; propagation: Row[];
  capital: Row[]; systemic: Row[]; optimisation: Row[]; recent_runs: Row[];
};

const API = 'http://127.0.0.1:8765';
const labels: Record<string, string> = {
  T1_LINEAR: 'Linear', T2_VALIDATOR: 'Validator', T3_SUPERVISOR: 'Supervisor',
  T4_CRITIC: 'Critic', T5_HUMAN_K0: 'Human K0', T5_HUMAN_K1: 'Human K1',
  T5_HUMAN_K2: 'Human K2', T5_HUMAN_K3: 'Human K3',
};
const faultLabels: Record<string, string> = {
  F1_DATA: 'Data / units', F2_SEMANTIC: 'Semantic', F3_TOOL: 'Tool use',
  F4_REASONING: 'Reasoning', F5_HANDOFF: 'Hand-off', F6_CONTEXT: 'Context',
  F7_ADVERSARIAL: 'Adversarial',
};
const stages = ['S1_INGEST', 'S2_RECONCILE', 'S3_SEGMENT', 'S4_MODEL', 'S5_SELECT', 'S6_NARRATE'];
const palette = ['#0b8f68', '#3b82a0', '#7c6ee6', '#cf7a36', '#c44e68', '#6d8b4a', '#9467bd', '#65717a'];

const pct = (value: unknown) => `${(Number(value) * 100).toFixed(1)}%`;
const money = (value: unknown, compact = true) => new Intl.NumberFormat('en-GB', {
  style: 'currency', currency: 'GBP', notation: compact ? 'compact' : 'standard', maximumFractionDigits: compact ? 1 : 0,
}).format(Number(value));
const short = (value: string | number | boolean | null | undefined) => String(value ?? '').replace(/^F\d_/, '').replace(/^S\d_/, '').replaceAll('_', ' ');

export function AatDashboard() {
  const [profile, setProfile] = useState('scaled');
  const [data, setData] = useState<Payload | null>(null);
  const [online, setOnline] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('Loading verified results…');
  const [trajectoryRows, setTrajectoryRows] = useState<Row[]>([]);
  const [traceTopology, setTraceTopology] = useState('');
  const [traceFault, setTraceFault] = useState('');
  const [view, setView] = useState('overview');

  const load = useCallback(async (selected: string) => {
    setNotice('Loading results…');
    try {
      const response = await fetch(`${API}/api/results?profile=${selected}`);
      if (!response.ok) throw new Error('API unavailable');
      setData(await response.json()); setOnline(true); setNotice('Live local API connected');
    } catch {
      const response = await fetch(`/data/${selected}.json`);
      if (!response.ok) throw new Error('No generated result set found');
      setData(await response.json()); setOnline(false); setNotice('Read-only snapshot · start the API to run tests');
    }
  }, []);

  useEffect(() => {
    queueMicrotask(() => load(profile).catch((error) => setNotice(String(error))));
  }, [load, profile]);

  const launch = async () => {
    if (!online) { setNotice('Start the Python API before launching a test.'); return; }
    setBusy(true); setNotice(`Running ${profile} experiment…`);
    const response = await fetch(`${API}/api/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ profile }) });
    if (!response.ok) { setBusy(false); setNotice(await response.text()); return; }
    const poll = window.setInterval(async () => {
      const status = await fetch(`${API}/api/health`).then((item) => item.json()) as { state: string; message: string };
      setNotice(status.message);
      if (status.state === 'complete' || status.state === 'failed') {
        window.clearInterval(poll); setBusy(false); if (status.state === 'complete') await load(profile);
      }
    }, 1500);
  };

  const loadTrajectories = async () => {
    if (!online) { setTrajectoryRows(data?.recent_runs ?? []); setNotice('Showing run summaries from the snapshot'); return; }
    const params = new URLSearchParams({ profile, limit: '120' });
    if (traceTopology) params.set('topology', traceTopology);
    if (traceFault) params.set('fault_type', traceFault);
    const result = await fetch(`${API}/api/trajectories?${params}`).then((item) => item.json()) as { rows: Row[]; count: number };
    setTrajectoryRows(result.rows ?? []); setNotice(`Loaded ${result.count ?? 0} trajectory events`);
  };

  const topologyChart = useMemo(() => (data?.topologies ?? []).map((row) => ({
    ...row, label: labels[String(row.topology)] ?? row.topology,
    detection: Number(row.detection_rate) * 100, silent: Number(row.silent_failure_rate) * 100,
  })), [data]);
  const capitalChart = useMemo<Array<Row & { label: string }>>(() => (data?.capital ?? []).map((row) => ({ ...row, label: labels[String(row.topology)] ?? String(row.topology) })), [data]);
  const selected = data?.optimisation.find((row) => row.selected);

  if (!data) return <main className="grid min-h-screen place-items-center bg-background"><div className="text-center"><RefreshCw className="mx-auto mb-3 animate-spin text-emerald-700" /><p>{notice}</p></div></main>;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-white/8 bg-[#071711]/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-5 py-3 lg:px-8">
          <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-emerald-400 text-[#062018]"><Activity /></span><div><p className="font-semibold tracking-tight text-white">AAT Control Room</p><p className="text-xs text-emerald-100/55">Agentic actuarial risk laboratory</p></div></div>
          <div className="flex flex-wrap items-center gap-2"><Badge className={online ? 'bg-emerald-400/15 text-emerald-300' : 'bg-amber-300/15 text-amber-200'}>{online ? 'Live API' : 'Snapshot mode'}</Badge><NativeSelect value={profile} onChange={(event) => setProfile(event.target.value)} className="text-white [&_select]:border-white/15 [&_select]:bg-white/5"><NativeSelectOption value="scaled">Scaled screening</NativeSelectOption><NativeSelectOption value="smoke">Smoke test</NativeSelectOption></NativeSelect><Button onClick={launch} disabled={busy} className="bg-emerald-400 text-[#062018] hover:bg-emerald-300">{busy ? <RefreshCw className="animate-spin" /> : <Play />} {busy ? 'Running' : `Run ${profile}`}</Button></div>
        </div>
      </header>

      <div className="mx-auto max-w-[1600px] px-5 py-6 lg:px-8">
        <section className="mb-5 flex flex-col justify-between gap-3 md:flex-row md:items-end"><div><p className="mb-1 text-xs font-semibold uppercase tracking-[.18em] text-emerald-700">Verified experiment workspace</p><h1 className="text-3xl font-semibold tracking-[-.035em] md:text-4xl">Where agent errors become capital risk.</h1><p className="mt-2 max-w-3xl text-muted-foreground">Test controls, trace faults through six actuarial stages, and examine scenario-conditioned tail consequences.</p></div><div className="rounded-lg border bg-white/60 px-3 py-2 text-xs text-muted-foreground"><span className="mr-2 inline-block size-2 rounded-full bg-emerald-500" />{notice}</div></section>

        <div>
          <nav className="mb-5 flex w-fit flex-wrap gap-1 rounded-xl bg-emerald-950/5 p-1" aria-label="Dashboard views">{[
            ['overview', 'Overview'], ['capital', 'Capital & dependence'],
            ['trajectories', 'Trajectory explorer'], ['methods', 'Evidence boundary'],
          ].map(([key, label]) => <button key={key} onClick={() => setView(key)} className={`rounded-lg px-3 py-2 text-sm font-medium transition ${view === key ? 'bg-white text-emerald-900 shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>{label}</button>)}</nav>

          {view === 'overview' && <div className="space-y-5">
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <Metric value={Number(data.meta.runs).toLocaleString()} label="Completed runs" icon={FlaskConical} />
              <Metric value={Number(data.meta.snapshots).toLocaleString()} label="Stage snapshots" icon={Waypoints} />
              <Metric value={String(data.meta.worlds)} label="Synthetic worlds" icon={Database} />
              <Metric value={String(data.meta.hard_failures)} label="Hard failures" icon={CheckCircle2} />
              <Metric value={labels[String(data.meta.selected_topology)] ?? String(data.meta.selected_topology)} label="Selected control" icon={ShieldCheck} />
            </section>
            <section className="grid gap-5 xl:grid-cols-[1.5fr_.75fr]">
              <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Control effectiveness</CardTitle><CardDescription>Detection and silent-failure shares among injected-fault runs.</CardDescription></CardHeader><CardContent><ResponsiveContainer width="100%" height={340}><BarChart data={topologyChart} margin={{ left: 0, right: 12 }}><CartesianGrid vertical={false} stroke="#dbe5df" /><XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={62} /><YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} /><Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} /><Legend /><Bar dataKey="detection" name="Detected" fill="#0b8f68" radius={[5, 5, 0, 0]} /><Bar dataKey="silent" name="Silent failure" fill="#ce6b52" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></CardContent></Card>
              <Card className="border-0 bg-[#0a2a20] text-white shadow-sm"><CardHeader><CardTitle className="text-white">Control decision</CardTitle><CardDescription className="text-emerald-50/60">Minimum capital-plus-control objective</CardDescription></CardHeader><CardContent><div className="rounded-xl border border-emerald-300/15 bg-white/5 p-5"><p className="text-xs uppercase tracking-[.15em] text-emerald-300">{labels[String(selected?.topology)]}</p><p className="mt-3 text-4xl font-semibold">{money(selected?.var_995)}</p><p className="mt-1 text-sm text-emerald-50/60">VaR 99.5%</p></div><div className="mt-4 grid grid-cols-2 gap-3"><DarkMetric label="ES 99.5%" value={money(selected?.es_995)} /><DarkMetric label="Annual control" value={money(selected?.annual_control_cost, false)} /></div><p className="mt-5 text-xs leading-relaxed text-emerald-50/45">Selected under the current scenario assumptions and 75% residual-risk cap. This is not regulatory capital advice.</p></CardContent></Card>
            </section>
            <section className="grid gap-5 xl:grid-cols-[.85fr_1.15fr]">
              <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Fault severity</CardTitle><CardDescription>95th percentile absolute paired reserve movement.</CardDescription></CardHeader><CardContent><div className="space-y-4">{[...data.faults].sort((a, b) => Number(b.p95_abs_delta) - Number(a.p95_abs_delta)).map((row) => { const max = Math.max(...data.faults.map((item) => Number(item.p95_abs_delta))); const width = max ? Number(row.p95_abs_delta) / max * 100 : 0; return <div key={String(row.fault_type)}><div className="mb-1 flex justify-between gap-3 text-sm"><span>{faultLabels[String(row.fault_type)]}</span><span className="font-mono text-xs">{money(row.p95_abs_delta)}</span></div><div className="h-1 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-emerald-700" style={{ width: `${width}%` }} /></div></div>; })}</div></CardContent></Card>
              <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Detection map</CardTitle><CardDescription>Observed detection share by fault and injection stage.</CardDescription></CardHeader><CardContent><DetectionHeatmap rows={data.detection_heatmap} /></CardContent></Card>
            </section>
          </div>}

          {view === 'capital' && <div className="space-y-5">
            <section className="grid gap-5 xl:grid-cols-2">
              <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Operational risk capital</CardTitle><CardDescription>VaR 99.5% by architecture; logarithmic axis exposes both controlled and stress tails.</CardDescription></CardHeader><CardContent><ResponsiveContainer width="100%" height={360}><BarChart data={capitalChart}><CartesianGrid vertical={false} /><XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={62} /><YAxis scale="log" domain={['auto', 'auto']} tickFormatter={(v) => money(v)} width={82} /><Tooltip formatter={(value) => money(value, false)} /><Bar dataKey="var_995" name="VaR 99.5%" fill="#147d64" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></CardContent></Card>
              <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Common-model dependence stress</CardTitle><CardDescription>Sector VaR 99.5% under prescribed Gaussian-copula correlation.</CardDescription></CardHeader><CardContent><ResponsiveContainer width="100%" height={360}><LineChart data={systemicWide(data.systemic)}><CartesianGrid vertical={false} /><XAxis dataKey="rho" tickFormatter={(v) => `ρ ${v}`} /><YAxis scale="log" domain={['auto', 'auto']} tickFormatter={(v) => money(v)} width={82} /><Tooltip formatter={(value) => money(value, false)} />{capitalChart.map((row, index) => <Line key={String(row.topology)} type="monotone" dataKey={String(row.topology)} name={String(row.label)} stroke={palette[index % palette.length]} strokeWidth={2} dot={false} />)}</LineChart></ResponsiveContainer></CardContent></Card>
            </section>
            <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Control package comparison</CardTitle><CardDescription>Scenario tail, expected shortfall, annual control cost and selection status.</CardDescription></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>Architecture</TableHead><TableHead>VaR 99.5%</TableHead><TableHead>ES 99.5%</TableHead><TableHead>Annual control</TableHead><TableHead>Feasible</TableHead><TableHead>Decision</TableHead></TableRow></TableHeader><TableBody>{data.optimisation.map((row) => <TableRow key={String(row.topology)}><TableCell className="font-medium">{labels[String(row.topology)]}</TableCell><TableCell>{money(row.var_995, false)}</TableCell><TableCell>{money(row.es_995, false)}</TableCell><TableCell>{money(row.annual_control_cost, false)}</TableCell><TableCell>{row.feasible ? <Badge className="bg-emerald-100 text-emerald-800">Within cap</Badge> : <Badge variant="destructive">Over cap</Badge>}</TableCell><TableCell>{row.selected ? <Badge>Selected</Badge> : '—'}</TableCell></TableRow>)}</TableBody></Table></CardContent></Card>
          </div>}

          {view === 'trajectories' && <div className="space-y-5">
            <Card className="border-0 shadow-sm"><CardHeader><CardTitle>Trajectory evidence explorer</CardTitle><CardDescription>Filter the SQLite audit trail and inspect injection, inspection, repair and stage events.</CardDescription></CardHeader><CardContent><div className="mb-5 flex flex-wrap gap-2"><NativeSelect value={traceTopology} onChange={(e) => setTraceTopology(e.target.value)}><NativeSelectOption value="">All architectures</NativeSelectOption>{data.topologies.map((row) => <NativeSelectOption key={String(row.topology)} value={String(row.topology)}>{labels[String(row.topology)]}</NativeSelectOption>)}</NativeSelect><NativeSelect value={traceFault} onChange={(e) => setTraceFault(e.target.value)}><NativeSelectOption value="">All fault types</NativeSelectOption>{data.faults.map((row) => <NativeSelectOption key={String(row.fault_type)} value={String(row.fault_type)}>{faultLabels[String(row.fault_type)]}</NativeSelectOption>)}</NativeSelect><Button onClick={loadTrajectories} variant="outline"><Search />Load evidence</Button></div>{trajectoryRows.length ? <Table><TableHeader><TableRow><TableHead>Run / world</TableHead><TableHead>Architecture</TableHead><TableHead>Fault</TableHead><TableHead>Stage</TableHead><TableHead>Event</TableHead><TableHead>Detected</TableHead></TableRow></TableHeader><TableBody>{trajectoryRows.map((row, index) => <TableRow key={`${row.run_id}-${row.sequence ?? index}`}><TableCell><span className="font-mono text-xs">{String(row.run_id).slice(0, 8)}</span> · {row.world_id}</TableCell><TableCell>{labels[String(row.topology)]}</TableCell><TableCell>{faultLabels[String(row.fault_type)] ?? row.fault_type}</TableCell><TableCell>{short(row.stage ?? row.injection_stage)}</TableCell><TableCell><Badge variant="outline">{short(row.event_type ?? (row.silent_failure ? 'silent failure' : 'run summary'))}</Badge></TableCell><TableCell>{row.detected ? 'Yes' : 'No'}</TableCell></TableRow>)}</TableBody></Table> : <div className="grid min-h-56 place-items-center rounded-xl border border-dashed bg-muted/25 text-center"><div><GitBranch className="mx-auto mb-2 text-muted-foreground" /><p className="font-medium">Choose filters and load evidence</p><p className="mt-1 text-sm text-muted-foreground">The live API reads the full trajectory database.</p></div></div>}</CardContent></Card>
          </div>}

          {view === 'methods' && <div className="space-y-5">
            <section className="grid gap-5 lg:grid-cols-3"><Boundary icon={Database} title="Known-truth worlds">Synthetic policies, claims, payments and ultimate losses allow direct error measurement without restricted insurer data.</Boundary><Boundary icon={GitBranch} title="Paired causal design">Every injected run is compared with the same world and architecture without the injected fault.</Boundary><Boundary icon={ShieldCheck} title="Replayable controls">A downstream detection restores the clean state and deterministically replays affected stages.</Boundary></section>
            <Card className="border-0 shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="text-amber-600" />Evidential boundary</CardTitle></CardHeader><CardContent className="grid gap-6 leading-relaxed text-muted-foreground lg:grid-cols-2"><div><p className="font-medium text-foreground">What this prototype establishes</p><ul className="mt-2 list-disc space-y-2 pl-5"><li>A reproducible method for measuring propagation and control response.</li><li>A scenario-conditioned bridge from paired error to aggregate tail loss.</li><li>An auditable basis for ORSA scenarios and control-placement discussion.</li></ul></div><div><p className="font-medium text-foreground">What still needs firm evidence</p><ul className="mt-2 list-disc space-y-2 pl-5"><li>Production fault frequencies and human-review effectiveness.</li><li>Economic conversion from reserve movement to realized operational loss.</li><li>Actual control placement and cross-firm dependence.</li></ul></div></CardContent></Card>
          </div>}
        </div>
      </div>
    </main>
  );
}

function Metric({ value, label, icon: Icon }: { value: string; label: string; icon: typeof Activity }) {
  return <Card className="border-0 shadow-sm"><CardContent className="flex items-center justify-between py-1"><div><p className="text-2xl font-semibold tracking-tight">{value}</p><p className="mt-1 text-[11px] uppercase tracking-wider text-muted-foreground">{label}</p></div><Icon className="size-5 text-emerald-700" /></CardContent></Card>;
}
function DarkMetric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-white/5 p-3"><p className="text-xs text-emerald-50/50">{label}</p><p className="mt-1 text-lg font-medium">{value}</p></div>; }
function Boundary({ icon: Icon, title, children }: { icon: typeof Activity; title: string; children: React.ReactNode }) { return <Card className="border-0 shadow-sm"><CardHeader><Icon className="mb-2 text-emerald-700" /><CardTitle>{title}</CardTitle></CardHeader><CardContent className="leading-relaxed text-muted-foreground">{children}</CardContent></Card>; }

function DetectionHeatmap({ rows }: { rows: Row[] }) {
  return <div className="overflow-x-auto"><div className="grid min-w-[650px] grid-cols-[130px_repeat(6,1fr)] gap-1 text-xs"><span />{stages.map((stage) => <span key={stage} className="px-1 py-2 text-center font-medium text-muted-foreground">{short(stage)}</span>)}{Object.keys(faultLabels).map((fault) => <div key={fault} className="contents"><span className="flex items-center font-medium">{faultLabels[fault]}</span>{stages.map((stage) => { const row = rows.find((item) => item.fault_type === fault && item.injection_stage === stage); const rate = Number(row?.detection_rate ?? 0); return <div key={stage} className="rounded-md px-2 py-3 text-center font-mono" style={{ background: `color-mix(in oklab, #0b8f68 ${Math.round(rate * 82 + 8)}%, white)`, color: rate > .55 ? 'white' : '#183a31' }}>{row ? pct(rate) : '—'}</div>; })}</div>)}</div></div>;
}

function systemicWide(rows: Row[]) {
  const values = new Map<number, Record<string, number>>();
  rows.forEach((row) => { const rho = Number(row.rho); const current = values.get(rho) ?? { rho }; current[String(row.topology)] = Number(row.var_995_sector); values.set(rho, current); });
  return [...values.values()].sort((a, b) => a.rho - b.rho);
}
