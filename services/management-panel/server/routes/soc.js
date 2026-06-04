const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const DB_FILE = path.join(DATA_DIR, 'soc.json');

function loadDb() {
  try {
    if (fs.existsSync(DB_FILE)) {
      return JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    }
  } catch (e) { /* ignore */ }
  return { soar: { playbooks: [], cases: [], connectors: [] }, ti: { iocs: [], feeds: [], actors: [] }, sase: { policies: [], branches: [], ztna: [] }, siem: { sources: [], alerts: [], rules: [] }, vuln: { findings: [], scans: [], patches: [] }, endpoint: { devices: [], policies: [], alerts: [] }, cloud: { cspm: [], workloads: [], iam: [] }, iam: { users: [], roles: [], reviews: [], audit: [] }, compliance: { frameworks: [], controls: [], audits: [], remediations: [] }, analytics: { dashboards: [], reports: [], anomalies: [], metrics: [] } };
}

function saveDb(db) {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

function generateId() { return Math.random().toString(36).substr(2, 9); }

// ========== SOAR Routes ==========
router.get('/soar/playbooks', (req, res) => { const db = loadDb(); res.json(db.soar.playbooks); });
router.post('/soar/playbooks', (req, res) => { const db = loadDb(); const p = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.soar.playbooks.push(p); saveDb(db); res.status(201).json(p); });
router.get('/soar/playbooks/:id', (req, res) => { const db = loadDb(); const p = db.soar.playbooks.find(x => x.id === req.params.id); p ? res.json(p) : res.status(404).json({ error: 'Not found' }); });
router.put('/soar/playbooks/:id', (req, res) => { const db = loadDb(); const idx = db.soar.playbooks.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.soar.playbooks[idx] = { ...db.soar.playbooks[idx], ...req.body }; saveDb(db); res.json(db.soar.playbooks[idx]); });
router.delete('/soar/playbooks/:id', (req, res) => { const db = loadDb(); db.soar.playbooks = db.soar.playbooks.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.post('/soar/playbooks/:id/execute', (req, res) => { res.json({ id: req.params.id, status: 'executing', started: new Date().toISOString() }); });
router.get('/soar/cases', (req, res) => { const db = loadDb(); res.json(db.soar.cases); });
router.get('/soar/connectors', (req, res) => { const db = loadDb(); res.json(db.soar.connectors); });

// ========== Threat Intelligence Routes ==========
router.get('/ti/iocs', (req, res) => { const db = loadDb(); res.json(db.ti.iocs); });
router.post('/ti/iocs', (req, res) => { const db = loadDb(); const ioc = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.ti.iocs.push(ioc); saveDb(db); res.status(201).json(ioc); });
router.get('/ti/iocs/:id', (req, res) => { const db = loadDb(); const ioc = db.ti.iocs.find(x => x.id === req.params.id); ioc ? res.json(ioc) : res.status(404).json({ error: 'Not found' }); });
router.delete('/ti/iocs/:id', (req, res) => { const db = loadDb(); db.ti.iocs = db.ti.iocs.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.get('/ti/feeds', (req, res) => { const db = loadDb(); res.json(db.ti.feeds); });
router.post('/ti/feeds', (req, res) => { const db = loadDb(); const f = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.ti.feeds.push(f); saveDb(db); res.status(201).json(f); });
router.post('/ti/enrich', (req, res) => { res.json({ value: req.body.value, enriched: true, sources: ['virustotal', 'abuseipdb'], score: 78 }); });
router.get('/ti/actors', (req, res) => { const db = loadDb(); res.json(db.ti.actors); });

// ========== SASE Routes ==========
router.get('/sase/policies', (req, res) => { const db = loadDb(); res.json(db.sase.policies); });
router.post('/sase/policies', (req, res) => { const db = loadDb(); const p = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.sase.policies.push(p); saveDb(db); res.status(201).json(p); });
router.put('/sase/policies/:id', (req, res) => { const db = loadDb(); const idx = db.sase.policies.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.sase.policies[idx] = { ...db.sase.policies[idx], ...req.body }; saveDb(db); res.json(db.sase.policies[idx]); });
router.delete('/sase/policies/:id', (req, res) => { const db = loadDb(); db.sase.policies = db.sase.policies.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.get('/sase/branches', (req, res) => { const db = loadDb(); res.json(db.sase.branches); });
router.get('/sase/ztna/apps', (req, res) => { const db = loadDb(); res.json(db.sase.ztna); });

// ========== SIEM Routes ==========
router.get('/siem/sources', (req, res) => { const db = loadDb(); res.json(db.siem.sources); });
router.get('/siem/alerts', (req, res) => { const db = loadDb(); res.json(db.siem.alerts); });
router.get('/siem/alerts/:id', (req, res) => { const db = loadDb(); const a = db.siem.alerts.find(x => x.id === req.params.id); a ? res.json(a) : res.status(404).json({ error: 'Not found' }); });
router.post('/siem/rules', (req, res) => { const db = loadDb(); const r = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.siem.rules.push(r); saveDb(db); res.status(201).json(r); });
router.put('/siem/rules/:id', (req, res) => { const db = loadDb(); const idx = db.siem.rules.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.siem.rules[idx] = { ...db.siem.rules[idx], ...req.body }; saveDb(db); res.json(db.siem.rules[idx]); });
router.delete('/siem/rules/:id', (req, res) => { const db = loadDb(); db.siem.rules = db.siem.rules.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.post('/siem/search', (req, res) => { res.json({ query: req.body.query, results: [], took_ms: 2400, total: 0 }); });

// ========== Vulnerability Routes ==========
router.get('/vuln/findings', (req, res) => { const db = loadDb(); res.json(db.vuln.findings); });
router.get('/vuln/findings/:id', (req, res) => { const db = loadDb(); const f = db.vuln.findings.find(x => x.id === req.params.id); f ? res.json(f) : res.status(404).json({ error: 'Not found' }); });
router.put('/vuln/findings/:id', (req, res) => { const db = loadDb(); const idx = db.vuln.findings.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.vuln.findings[idx] = { ...db.vuln.findings[idx], ...req.body }; saveDb(db); res.json(db.vuln.findings[idx]); });
router.get('/vuln/scans', (req, res) => { const db = loadDb(); res.json(db.vuln.scans); });
router.post('/vuln/scans', (req, res) => { const db = loadDb(); const s = { id: generateId(), ...req.body, status: 'pending', created: new Date().toISOString() }; db.vuln.scans.push(s); saveDb(db); res.status(201).json(s); });
router.post('/vuln/scans/:id/run', (req, res) => { res.json({ id: req.params.id, status: 'running' }); });
router.delete('/vuln/scans/:id', (req, res) => { const db = loadDb(); db.vuln.scans = db.vuln.scans.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.get('/vuln/patches', (req, res) => { const db = loadDb(); res.json(db.vuln.patches); });

// ========== Endpoint Routes ==========
router.get('/endpoint/devices', (req, res) => { const db = loadDb(); res.json(db.endpoint.devices); });
router.get('/endpoint/devices/:id', (req, res) => { const db = loadDb(); const d = db.endpoint.devices.find(x => x.id === req.params.id); d ? res.json(d) : res.status(404).json({ error: 'Not found' }); });
router.post('/endpoint/devices/:id/scan', (req, res) => { res.json({ device_id: req.params.id, scan: 'started', type: 'quick' }); });
router.get('/endpoint/policies', (req, res) => { const db = loadDb(); res.json(db.endpoint.policies); });
router.post('/endpoint/policies', (req, res) => { const db = loadDb(); const p = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.endpoint.policies.push(p); saveDb(db); res.status(201).json(p); });
router.put('/endpoint/policies/:id', (req, res) => { const db = loadDb(); const idx = db.endpoint.policies.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.endpoint.policies[idx] = { ...db.endpoint.policies[idx], ...req.body }; saveDb(db); res.json(db.endpoint.policies[idx]); });
router.delete('/endpoint/policies/:id', (req, res) => { const db = loadDb(); db.endpoint.policies = db.endpoint.policies.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.get('/endpoint/alerts', (req, res) => { const db = loadDb(); res.json(db.endpoint.alerts); });

// ========== Cloud Security Routes ==========
router.get('/cloud/cspm', (req, res) => { const db = loadDb(); res.json(db.cloud.cspm); });
router.get('/cloud/workloads', (req, res) => { const db = loadDb(); res.json(db.cloud.workloads); });
router.post('/cloud/scan', (req, res) => { res.json({ status: 'scanning', provider: req.body.provider || 'all', benchmark: req.body.benchmark || 'cis' }); });
router.get('/cloud/iam/roles', (req, res) => { const db = loadDb(); res.json(db.cloud.iam); });
router.put('/cloud/findings/:id', (req, res) => { const db = loadDb(); const idx = db.cloud.cspm.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.cloud.cspm[idx] = { ...db.cloud.cspm[idx], ...req.body }; saveDb(db); res.json(db.cloud.cspm[idx]); });

// ========== IAM Security Routes ==========
router.get('/iam/users', (req, res) => { const db = loadDb(); res.json(db.iam.users); });
router.get('/iam/users/:id', (req, res) => { const db = loadDb(); const u = db.iam.users.find(x => x.id === req.params.id); u ? res.json(u) : res.status(404).json({ error: 'Not found' }); });
router.post('/iam/users', (req, res) => { const db = loadDb(); const u = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.iam.users.push(u); saveDb(db); res.status(201).json(u); });
router.put('/iam/users/:id', (req, res) => { const db = loadDb(); const idx = db.iam.users.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.iam.users[idx] = { ...db.iam.users[idx], ...req.body }; saveDb(db); res.json(db.iam.users[idx]); });
router.delete('/iam/users/:id', (req, res) => { const db = loadDb(); db.iam.users = db.iam.users.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.get('/iam/roles', (req, res) => { const db = loadDb(); res.json(db.iam.roles); });
router.get('/iam/access-reviews', (req, res) => { const db = loadDb(); res.json(db.iam.reviews); });
router.post('/iam/access-reviews/:id/execute', (req, res) => { res.json({ id: req.params.id, status: 'executing' }); });
router.get('/iam/audit', (req, res) => { const db = loadDb(); res.json(db.iam.audit); });

// ========== Compliance Routes ==========
router.get('/compliance/frameworks', (req, res) => { const db = loadDb(); res.json(db.compliance.frameworks); });
router.get('/compliance/controls', (req, res) => { const db = loadDb(); res.json(db.compliance.controls); });
router.put('/compliance/controls/:id', (req, res) => { const db = loadDb(); const idx = db.compliance.controls.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.compliance.controls[idx] = { ...db.compliance.controls[idx], ...req.body }; saveDb(db); res.json(db.compliance.controls[idx]); });
router.get('/compliance/audits', (req, res) => { const db = loadDb(); res.json(db.compliance.audits); });
router.post('/compliance/audits', (req, res) => { const db = loadDb(); const a = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.compliance.audits.push(a); saveDb(db); res.status(201).json(a); });
router.get('/compliance/remediations', (req, res) => { const db = loadDb(); res.json(db.compliance.remediations); });

// ========== Security Analytics Routes ==========
router.get('/analytics/dashboards', (req, res) => { const db = loadDb(); res.json(db.analytics.dashboards); });
router.post('/analytics/dashboards', (req, res) => { const db = loadDb(); const d = { id: generateId(), ...req.body, created: new Date().toISOString() }; db.analytics.dashboards.push(d); saveDb(db); res.status(201).json(d); });
router.get('/analytics/dashboards/:id', (req, res) => { const db = loadDb(); const d = db.analytics.dashboards.find(x => x.id === req.params.id); d ? res.json(d) : res.status(404).json({ error: 'Not found' }); });
router.put('/analytics/dashboards/:id', (req, res) => { const db = loadDb(); const idx = db.analytics.dashboards.findIndex(x => x.id === req.params.id); if (idx === -1) return res.status(404).json({ error: 'Not found' }); db.analytics.dashboards[idx] = { ...db.analytics.dashboards[idx], ...req.body }; saveDb(db); res.json(db.analytics.dashboards[idx]); });
router.delete('/analytics/dashboards/:id', (req, res) => { const db = loadDb(); db.analytics.dashboards = db.analytics.dashboards.filter(x => x.id !== req.params.id); saveDb(db); res.json({ success: true }); });
router.get('/analytics/reports', (req, res) => { const db = loadDb(); res.json(db.analytics.reports); });
router.post('/analytics/reports/generate', (req, res) => { res.json({ status: 'generating', type: req.body.report_type, timeframe: req.body.timeframe }); });
router.get('/analytics/anomalies', (req, res) => { const db = loadDb(); res.json(db.analytics.anomalies); });
router.get('/analytics/metrics', (req, res) => { const db = loadDb(); res.json(db.analytics.metrics); });

router.post('/summary', (req, res) => {
  const db = loadDb();
  res.json({
    soar: { playbooks: db.soar.playbooks.length, cases: db.soar.cases.length, connectors: db.soar.connectors.length },
    ti: { iocs: db.ti.iocs.length, feeds: db.ti.feeds.length, actors: db.ti.actors.length },
    sase: { policies: db.sase.policies.length, branches: db.sase.branches.length },
    siem: { sources: db.siem.sources.length, alerts: db.siem.alerts.length, rules: db.siem.rules.length },
    vuln: { findings: db.vuln.findings.length, scans: db.vuln.scans.length },
    endpoint: { devices: db.endpoint.devices.length, policies: db.endpoint.policies.length },
    cloud: { cspm: db.cloud.cspm.length, workloads: db.cloud.workloads.length },
    iam: { users: db.iam.users.length, roles: db.iam.roles.length },
    compliance: { frameworks: db.compliance.frameworks.length, controls: db.compliance.controls.length },
    analytics: { dashboards: db.analytics.dashboards.length, reports: db.analytics.reports.length },
  });
});

module.exports = router;
