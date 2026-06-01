import json
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


RUNBOOK_TEMPLATES = [
    {
        "name": "Database Migration Rollback",
        "version": "1.2.0",
        "category": "maintenance",
        "author": "SRE Team",
        "description": "Rollback a failed database migration",
        "difficulty": "intermediate",
        "estimated_duration": "15 minutes",
        "tags": ["database", "migration", "rollback"],
        "variables": [
            {"name": "db_name", "type": "string", "description": "Database name", "required": True},
            {"name": "migration_version", "type": "string", "description": "Version to rollback to", "required": True},
            {"name": "dry_run", "type": "boolean", "description": "Perform dry run first", "default": True},
        ],
        "steps": [
            {"order": 1, "name": "Check current migration status", "command": "migrate status -db {{db_name}}", "expected": "FAILED", "critical": True},
            {"order": 2, "name": "Backup current state", "command": "pg_dump {{db_name}} > /tmp/{{db_name}}_{{timestamp}}.sql", "timeout": 120},
            {"order": 3, "name": "Execute rollback", "command": "migrate rollback -db {{db_name}} -to {{migration_version}}", "timeout": 300},
            {"order": 4, "name": "Verify rollback", "command": "migrate status -db {{db_name}}", "expected": "OK", "critical": True},
            {"order": 5, "name": "Verify application connectivity", "command": "curl -f http://app/health", "timeout": 30},
        ],
        "rollback": [
            {"order": 1, "name": "Re-apply failed migration", "command": "migrate up -db {{db_name}}"},
            {"order": 2, "name": "Restore from backup", "command": "psql {{db_name}} < /tmp/{{db_name}}_{{timestamp}}.sql"},
        ],
        "rating": 4.5,
        "usage_count": 128,
    },
    {
        "name": "SSL Certificate Renewal",
        "version": "1.0.0",
        "category": "maintenance",
        "author": "Security Team",
        "description": "Renew Let's Encrypt SSL certificate",
        "difficulty": "beginner",
        "estimated_duration": "10 minutes",
        "tags": ["ssl", "certificate", "letsencrypt"],
        "variables": [
            {"name": "domain", "type": "string", "description": "Domain to renew", "required": True},
            {"name": "email", "type": "string", "description": "Contact email", "required": True},
        ],
        "steps": [
            {"order": 1, "name": "Check certificate expiry", "command": "openssl x509 -checkend 86400 -noout -in /etc/letsencrypt/live/{{domain}}/cert.pem", "critical": False},
            {"order": 2, "name": "Request renewal", "command": "certbot renew --cert-name {{domain}} --non-interactive --agree-tos --email {{email}}", "timeout": 60},
            {"order": 3, "name": "Verify new certificate", "command": "openssl x509 -dates -noout -in /etc/letsencrypt/live/{{domain}}/cert.pem"},
            {"order": 4, "name": "Reload web server", "command": "nginx -s reload", "timeout": 10},
            {"order": 5, "name": "Verify HTTPS", "command": "curl -o /dev/null -s -w '%{http_code}' https://{{domain}}", "expected": "200"},
        ],
        "rollback": [
            {"order": 1, "name": "Restore previous certificate", "command": "certbot rollback --cert-name {{domain}}"},
            {"order": 2, "name": "Reload web server", "command": "nginx -s reload"},
        ],
        "rating": 4.8,
        "usage_count": 256,
    },
    {
        "name": "Incident Response: Service Outage",
        "version": "2.0.0",
        "category": "incident_response",
        "author": "Incident Management Team",
        "description": "Standard response procedure for service outages",
        "difficulty": "advanced",
        "estimated_duration": "30-60 minutes",
        "tags": ["incident", "outage", "sre"],
        "variables": [
            {"name": "service_name", "type": "string", "description": "Affected service", "required": True},
            {"name": "severity", "type": "enum", "options": ["SEV1", "SEV2", "SEV3"], "description": "Incident severity", "required": True},
            {"name": "alert_source", "type": "string", "description": "How the outage was detected", "default": "monitoring"},
        ],
        "steps": [
            {"order": 1, "name": "Acknowledge incident", "command": "echo 'Incident acknowledged for {{service_name}}'", "critical": True},
            {"order": 2, "name": "Check service health", "command": "curl -f http://{{service_name}}/health", "timeout": 10},
            {"order": 3, "name": "Check recent deployments", "command": "kubectl rollout history deployment/{{service_name}}", "timeout": 10},
            {"order": 4, "name": "Check logs for errors", "command": "kubectl logs -l app={{service_name}} --tail=100 --since=1h", "timeout": 15},
            {"order": 5, "name": "Check resource usage", "command": "kubectl top pod -l app={{service_name}}", "timeout": 10},
            {"order": 6, "name": "Rollback if recent deployment found", "command": "kubectl rollout undo deployment/{{service_name}}", "timeout": 60, "if_condition": "recent_deploy"},
            {"order": 7, "name": "Restart pods", "command": "kubectl rollout restart deployment/{{service_name}}", "timeout": 60},
            {"order": 8, "name": "Verify recovery", "command": "curl -f http://{{service_name}}/health", "expected": "200"},
        ],
        "rollback": [],
        "rating": 4.2,
        "usage_count": 89,
    },
    {
        "name": "Container Image Vulnerability Remediation",
        "version": "1.1.0",
        "category": "security",
        "author": "Security Team",
        "description": "Remediate critical vulnerabilities in container images",
        "difficulty": "intermediate",
        "estimated_duration": "20 minutes",
        "tags": ["security", "vulnerability", "container"],
        "variables": [
            {"name": "image_name", "type": "string", "description": "Vulnerable image", "required": True},
            {"name": "new_tag", "type": "string", "description": "Patched image tag", "required": True},
            {"name": "deployment_name", "type": "string", "description": "K8s deployment name", "required": True},
        ],
        "steps": [
            {"order": 1, "name": "Scan current image", "command": "trivy image {{image_name}}:current", "timeout": 120},
            {"order": 2, "name": "Pull patched image", "command": "docker pull {{image_name}}:{{new_tag}}", "timeout": 180},
            {"order": 3, "name": "Scan patched image", "command": "trivy image {{image_name}}:{{new_tag}}", "timeout": 120},
            {"order": 4, "name": "Update deployment", "command": "kubectl set image deployment/{{deployment_name}} app={{image_name}}:{{new_tag}}", "timeout": 30},
            {"order": 5, "name": "Rolling restart", "command": "kubectl rollout status deployment/{{deployment_name}}", "timeout": 180},
            {"order": 6, "name": "Verify deployment", "command": "kubectl get pods -l app={{deployment_name}} -o jsonpath='{.items[*].status.phase}'", "expected": "Running"},
        ],
        "rollback": [
            {"order": 1, "name": "Revert to previous image", "command": "kubectl set image deployment/{{deployment_name}} app={{image_name}}:current"},
            {"order": 2, "name": "Wait for rollback", "command": "kubectl rollout status deployment/{{deployment_name}}", "timeout": 180},
        ],
        "rating": 4.6,
        "usage_count": 67,
    },
    {
        "name": "Database Backup and Verification",
        "version": "1.0.0",
        "category": "backup_restore",
        "author": "DBA Team",
        "description": "Perform verified backup of database with integrity check",
        "difficulty": "beginner",
        "estimated_duration": "30 minutes",
        "tags": ["database", "backup", "verification"],
        "variables": [
            {"name": "db_type", "type": "enum", "options": ["postgresql", "mysql", "mongodb"], "description": "Database type", "required": True},
            {"name": "db_name", "type": "string", "description": "Database name", "required": True},
            {"name": "backup_path", "type": "string", "description": "Backup destination", "default": "/backups"},
        ],
        "steps": [
            {"order": 1, "name": "Create backup", "command": "pg_dump -Fc {{db_name}} > {{backup_path}}/{{db_name}}_{{timestamp}}.dump", "timeout": 600},
            {"order": 2, "name": "Verify backup file", "command": "file {{backup_path}}/{{db_name}}_{{timestamp}}.dump | grep -q 'PostgreSQL'", "critical": True},
            {"order": 3, "name": "Check backup size", "command": "ls -lh {{backup_path}}/{{db_name}}_{{timestamp}}.dump"},
            {"order": 4, "name": "Compute checksum", "command": "sha256sum {{backup_path}}/{{db_name}}_{{timestamp}}.dump > {{backup_path}}/{{db_name}}_{{timestamp}}.sha256"},
            {"order": 5, "name": "Upload to remote storage", "command": "aws s3 cp {{backup_path}}/{{db_name}}_{{timestamp}}.dump s3://backups/{{db_name}}/", "timeout": 300},
            {"order": 6, "name": "Verify upload", "command": "aws s3 ls s3://backups/{{db_name}}/{{db_name}}_{{timestamp}}.dump", "critical": True},
        ],
        "rollback": [],
        "rating": 4.9,
        "usage_count": 312,
    },
    {
        "name": "Kubernetes Node Drain and Maintenance",
        "version": "1.3.0",
        "category": "maintenance",
        "author": "Platform Team",
        "description": "Safely drain a Kubernetes node for maintenance",
        "difficulty": "advanced",
        "estimated_duration": "45 minutes",
        "tags": ["kubernetes", "node", "maintenance"],
        "variables": [
            {"name": "node_name", "type": "string", "description": "Node to drain", "required": True},
            {"name": "grace_period", "type": "integer", "description": "Pod grace period in seconds", "default": 300},
            {"name": "ignore_daemonsets", "type": "boolean", "description": "Ignore daemonset pods", "default": True},
        ],
        "steps": [
            {"order": 1, "name": "Cordon node", "command": "kubectl cordon {{node_name}}", "critical": True},
            {"order": 2, "name": "List pods on node", "command": "kubectl get pods --field-selector spec.nodeName={{node_name}} -o wide"},
            {"order": 3, "name": "Drain node", "command": "kubectl drain {{node_name}} --grace-period={{grace_period}} --ignore-daemonsets={{ignore_daemonsets}} --delete-emptydir-data", "timeout": 600, "critical": True},
            {"order": 4, "name": "Verify node is drained", "command": "kubectl get pods --field-selector spec.nodeName={{node_name}} | tail -n +2 | wc -l", "expected": "0"},
            {"order": 5, "name": "Perform maintenance", "command": "echo 'Node ready for maintenance: {{node_name}}'"},
        ],
        "rollback": [
            {"order": 1, "name": "Uncordon node", "command": "kubectl uncordon {{node_name}}"},
            {"order": 2, "name": "Verify pods scheduled", "command": "kubectl get pods --field-selector spec.nodeName={{node_name}}"},
        ],
        "rating": 4.3,
        "usage_count": 45,
    },
]


CATEGORIES = [
    {"id": "incident_response", "name": "Incident Response", "description": "Security incidents, outages, data breaches"},
    {"id": "maintenance", "name": "Maintenance", "description": "Database migration, certificate renewal, patching"},
    {"id": "deployment", "name": "Deployment", "description": "Blue-green, canary, rollback"},
    {"id": "monitoring", "name": "Monitoring", "description": "Alert response, threshold tuning, dashboards"},
    {"id": "backup_restore", "name": "Backup/Restore", "description": "Database backup, file restore, DR failover"},
    {"id": "security", "name": "Security", "description": "Key rotation, access review, vulnerability remediation"},
    {"id": "networking", "name": "Networking", "description": "Firewall rules, DNS, load balancers"},
    {"id": "storage", "name": "Storage", "description": "Volume expansion, snapshots, migration"},
]


class RunbookLibraryManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._templates: Dict[str, Dict] = {}
        self._instances: Dict[str, Dict] = {}
        self._ratings: Dict[str, List[Dict]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        for template in RUNBOOK_TEMPLATES:
            template_id = str(uuid.uuid4())
            self._templates[template_id] = {"template_id": template_id, **template}
            self._ratings[template_id] = []
        self._initialized = True
        logger.info(f"RunbookLibraryManager initialized with {len(self._templates)} templates")

    async def close(self) -> None:
        self._templates.clear()
        self._instances.clear()
        logger.info("RunbookLibraryManager closed")

    def create_template(self, name: str, description: str, category: str,
                        steps: List[Dict], variables: List[Dict],
                        author: str = "community", tags: Optional[List[str]] = None,
                        rollback: Optional[List[Dict]] = None,
                        difficulty: str = "beginner",
                        estimated_duration: str = "15 minutes") -> Dict:
        template_id = str(uuid.uuid4())
        template = {
            "template_id": template_id,
            "name": name,
            "version": "1.0.0",
            "category": category,
            "author": author,
            "description": description,
            "difficulty": difficulty,
            "estimated_duration": estimated_duration,
            "tags": tags or [],
            "variables": variables,
            "steps": steps,
            "rollback": rollback or [],
            "rating": 0.0,
            "usage_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._templates[template_id] = template
        self._ratings[template_id] = []
        logger.info(f"Runbook template {template_id} created: {name}")
        return template

    def get_template(self, template_id: str) -> Optional[Dict]:
        return self._templates.get(template_id)

    def update_template(self, template_id: str, updates: Dict) -> Optional[Dict]:
        template = self._templates.get(template_id)
        if not template:
            return None
        for key, value in updates.items():
            if key not in ("template_id", "created_at", "rating", "usage_count"):
                template[key] = value
        template["version"] = self._bump_version(template.get("version", "1.0.0"))
        template["updated_at"] = datetime.utcnow().isoformat()
        return template

    def delete_template(self, template_id: str) -> bool:
        if template_id not in self._templates:
            return False
        del self._templates[template_id]
        del self._ratings[template_id]
        return True

    def _bump_version(self, version: str) -> str:
        parts = version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)

    def search_templates(self, query: str, category: Optional[str] = None,
                         tag: Optional[str] = None, difficulty: Optional[str] = None,
                         limit: int = 50) -> List[Dict]:
        results = list(self._templates.values())
        query_lower = query.lower()
        results = [
            t for t in results
            if query_lower in t["name"].lower()
            or query_lower in t["description"].lower()
            or query_lower in t.get("tags", [])
        ]
        if category:
            results = [t for t in results if t["category"] == category]
        if tag:
            results = [t for t in results if tag in t.get("tags", [])]
        if difficulty:
            results = [t for t in results if t.get("difficulty") == difficulty]
        return sorted(results, key=lambda t: t.get("rating", 0), reverse=True)[:limit]

    def list_templates(self, category: Optional[str] = None,
                       sort_by: str = "rating") -> List[Dict]:
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t["category"] == category]
        if sort_by == "rating":
            templates.sort(key=lambda t: t.get("rating", 0), reverse=True)
        elif sort_by == "usage":
            templates.sort(key=lambda t: t.get("usage_count", 0), reverse=True)
        elif sort_by == "newest":
            templates.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        return templates

    def list_categories(self) -> List[Dict]:
        return CATEGORIES

    def instantiate_template(self, template_id: str, variable_values: Dict[str, Any],
                              initiated_by: str = "system") -> Dict:
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        instance_id = str(uuid.uuid4())
        rendered_steps = self._render_template_steps(template["steps"], variable_values)
        rendered_rollback = self._render_template_steps(template.get("rollback", []), variable_values)

        instance = {
            "instance_id": instance_id,
            "template_id": template_id,
            "template_name": template["name"],
            "variable_values": variable_values,
            "steps": rendered_steps,
            "rollback_steps": rendered_rollback,
            "status": "created",
            "current_step": 0,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
            "initiated_by": initiated_by,
            "results": [],
        }
        self._instances[instance_id] = instance
        template["usage_count"] = template.get("usage_count", 0) + 1
        logger.info(f"Runbook {instance_id} instantiated from {template['name']}")
        return instance

    def _render_template_steps(self, steps: List[Dict], variables: Dict) -> List[Dict]:
        import re
        rendered = []
        for step in steps:
            command = step.get("command", "")
            for var_name, var_value in variables.items():
                command = command.replace("{{" + var_name + "}}", str(var_value))
            command = command.replace("{{timestamp}}", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
            rendered.append({
                **step,
                "command": command,
                "actual_command": command,
            })
        return rendered

    def get_instance(self, instance_id: str) -> Optional[Dict]:
        return self._instances.get(instance_id)

    def execute_instance_step(self, instance_id: str) -> Optional[Dict]:
        instance = self._instances.get(instance_id)
        if not instance:
            return None
        if instance["current_step"] >= len(instance["steps"]):
            instance["status"] = "completed"
            instance["completed_at"] = datetime.utcnow().isoformat()
            return instance
        step = instance["steps"][instance["current_step"]]
        result = {
            "step_order": step.get("order"),
            "step_name": step.get("name"),
            "status": "executed",
            "executed_at": datetime.utcnow().isoformat(),
            "output": f"Executed: {step.get('actual_command', step.get('command', ''))}",
            "error": None,
        }
        instance["results"].append(result)
        instance["current_step"] += 1
        return result

    def vote_template(self, template_id: str, rating: int, comment: str = "",
                       voter: str = "anonymous") -> Dict:
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        rating = max(1, min(5, rating))
        vote = {
            "rating": rating,
            "comment": comment,
            "voter": voter,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._ratings[template_id].append(vote)
        ratings = self._ratings[template_id]
        template["rating"] = round(sum(v["rating"] for v in ratings) / len(ratings), 1)
        return {"template_id": template_id, "new_rating": template["rating"], "total_votes": len(ratings)}

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_templates": len(self._templates),
            "total_instances": len(self._instances),
            "categories": len(CATEGORIES),
            "total_votes": sum(len(v) for v in self._ratings.values()),
            "most_used": max(self._templates.values(), key=lambda t: t.get("usage_count", 0)).get("name", "N/A") if self._templates else None,
        }

    def search_templates_fulltext(self, query: str) -> List[Dict]:
        return self.search_templates(query, limit=20)
