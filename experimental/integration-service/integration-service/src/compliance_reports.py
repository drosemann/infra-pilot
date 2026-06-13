from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class ComplianceReportManager:
    """SOC 2, HIPAA, PCI-DSS report generation with evidence collection and control mapping"""

    FRAMEWORKS = ['SOC_2', 'HIPAA', 'PCI_DSS']

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.frameworks_file = config.get('compliance_frameworks_file', 'data/compliance_frameworks.json')
        self.evidence_file = config.get('compliance_evidence_file', 'data/compliance_evidence.json')
        self.reports_file = config.get('compliance_reports_file', 'data/compliance_reports.json')
        self.frameworks: Dict[str, Any] = {}
        self.evidence: List[Dict[str, Any]] = []
        self.reports: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        for path, attr in [
            (self.frameworks_file, 'frameworks'),
            (self.evidence_file, 'evidence'),
            (self.reports_file, 'reports'),
        ]:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")

    def _save(self, attr: str, path: str):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(getattr(self, attr), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")

    async def create_framework(self, framework: Dict[str, Any]) -> Dict[str, Any]:
        fw_id = framework.get('id', f'fw_{len(self.frameworks)}_{int(datetime.now().timestamp())}')
        framework['id'] = fw_id
        framework['created_at'] = datetime.now().isoformat()
        if framework.get('name') not in self.FRAMEWORKS:
            self.FRAMEWORKS.append(framework.get('name', ''))
        self.frameworks[fw_id] = framework
        self._save('frameworks', self.frameworks_file)
        return framework

    async def get_frameworks(self) -> Dict[str, Any]:
        return self.frameworks

    async def add_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        ev_id = evidence.get('id', f'evidence_{len(self.evidence)}_{int(datetime.now().timestamp())}')
        entry = {
            'id': ev_id,
            'framework_id': evidence.get('framework_id', ''),
            'control_id': evidence.get('control_id', ''),
            'type': evidence.get('type', 'documentation'),
            'description': evidence.get('description', ''),
            'file_path': evidence.get('file_path', ''),
            'collected_by': evidence.get('collected_by', 'system'),
            'collected_at': datetime.now().isoformat(),
            'expires_at': evidence.get('expires_at'),
            'status': 'active',
        }
        self.evidence.append(entry)
        self._save('evidence', self.evidence_file)
        return entry

    async def get_evidence(self, framework_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if framework_id:
            return [e for e in self.evidence if e.get('framework_id') == framework_id]
        return self.evidence

    async def generate_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        report_id = f'report_{len(self.reports)}_{int(datetime.now().timestamp())}'
        framework_id = report_config.get('framework_id', '')
        framework = self.frameworks.get(framework_id, {})
        controls = framework.get('controls', [])
        matching_evidence = [e for e in self.evidence if e.get('framework_id') == framework_id]

        control_statuses = []
        for control in controls:
            ctrl_id = control.get('id', '')
            ctrl_evidence = [e for e in matching_evidence if e.get('control_id') == ctrl_id]
            control_statuses.append({
                'control_id': ctrl_id,
                'control_name': control.get('name', ''),
                'control_description': control.get('description', ''),
                'status': 'compliant' if ctrl_evidence else 'non_compliant',
                'evidence_count': len(ctrl_evidence),
                'evidence_items': ctrl_evidence,
            })

        report = {
            'id': report_id,
            'framework_id': framework_id,
            'framework_name': framework.get('name', ''),
            'title': report_config.get('title', f'Compliance Report - {framework.get("name", "")}'),
            'generated_at': datetime.now().isoformat(),
            'period_start': report_config.get('period_start', ''),
            'period_end': report_config.get('period_end', ''),
            'generated_by': report_config.get('generated_by', 'system'),
            'control_statuses': control_statuses,
            'summary': {
                'total_controls': len(controls),
                'compliant': sum(1 for c in control_statuses if c['status'] == 'compliant'),
                'non_compliant': sum(1 for c in control_statuses if c['status'] == 'non_compliant'),
            },
            'status': 'generated',
        }
        self.reports.append(report)
        self._save('reports', self.reports_file)
        return report

    async def get_reports(self) -> List[Dict[str, Any]]:
        return self.reports

    async def export_report(self, report_id: str, export_format: str = 'json') -> Dict[str, Any]:
        report = next((r for r in self.reports if r['id'] == report_id), None)
        if not report:
            return {'error': 'Report not found'}

        export = {
            'report': report,
            'export_format': export_format,
            'exported_at': datetime.now().isoformat(),
            'auditor_ready': True,
        }

        if export_format == 'json':
            export['content'] = json.dumps(report, indent=2)
        elif export_format == 'csv':
            lines = ['control_id,status,evidence_count']
            for cs in report.get('control_statuses', []):
                lines.append(f"{cs['control_id']},{cs['status']},{cs['evidence_count']}")
            export['content'] = '\n'.join(lines)

        report['last_exported_at'] = datetime.now().isoformat()
        self._save('reports', self.reports_file)
        return export
