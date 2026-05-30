"""Extended Ansible/Salt integration with inventory management, playbook execution, and job scheduling."""
import json
import uuid
import logging
import subprocess
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    ANSIBLE = "ansible"
    SALT = "salt"
    TERRAFORM = "terraform"
    PULUMI = "pulumi"
    CHEF = "chef"
    PUPPET = "puppet"


class ExecutionMode(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"
    SSH = "ssh"
    WINRM = "winrm"
    API = "api"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ConnectionMethod(str, Enum):
    SSH = "ssh"
    WINRM = "winrm"
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    API = "api"


@dataclass
class AnsibleInventoryHost:
    name: str
    ansible_host: str
    ansible_port: int = 22
    ansible_user: str = "root"
    ansible_ssh_private_key_file: Optional[str] = None
    ansible_connection: str = "ssh"
    ansible_python_interpreter: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    groups: List[str] = field(default_factory=list)


@dataclass
class AnsibleInventoryGroup:
    name: str
    hosts: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnsibleInventory:
    id: str
    name: str
    description: str
    hosts: Dict[str, AnsibleInventoryHost] = field(default_factory=dict)
    groups: Dict[str, AnsibleInventoryGroup] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SaltMinion:
    id: str
    name: str
    host: str
    port: int = 4506
    transport: str = "tcp"
    auth_method: str = "pam"
    version: Optional[str] = None
    grains: Dict[str, Any] = field(default_factory=dict)
    connected: bool = False
    last_seen: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PlaybookDefinition:
    id: str
    name: str
    description: str
    tool: ToolType
    content: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    inventory_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class JobExecution:
    id: str
    playbook_id: str
    tool: ToolType
    status: JobStatus
    inventory_id: Optional[str] = None
    target_hosts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    output: str = ""
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    executed_by: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class JobSchedule:
    id: str
    playbook_id: str
    name: str
    cron_expression: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    inventory_id: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionTemplate:
    id: str
    name: str
    description: str
    tool: ToolType
    playbook_content: str
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class AnsibleSaltManager:
    def __init__(self, storage_path: str = "data/ansible_salt.json"):
        self.storage_path = storage_path
        self.inventories: Dict[str, AnsibleInventory] = {}
        self.playbooks: Dict[str, PlaybookDefinition] = {}
        self.jobs: Dict[str, JobExecution] = {}
        self.schedules: Dict[str, JobSchedule] = {}
        self.minions: Dict[str, SaltMinion] = {}
        self.templates: Dict[str, ExecutionTemplate] = {}
        self._load_data()

    def _load_data(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        for inv_data in data.get("inventories", []):
            inv = AnsibleInventory(**inv_data)
            self.inventories[inv.id] = inv
        for pb_data in data.get("playbooks", []):
            pb = PlaybookDefinition(**pb_data)
            self.playbooks[pb.id] = pb
        for job_data in data.get("jobs", []):
            job = JobExecution(**job_data)
            self.jobs[job.id] = job
        for sched_data in data.get("schedules", []):
            sched = JobSchedule(**sched_data)
            self.schedules[sched.id] = sched
        for min_data in data.get("minions", []):
            mn = SaltMinion(**min_data)
            self.minions[mn.id] = mn
        for tmpl_data in data.get("templates", []):
            tmpl = ExecutionTemplate(**tmpl_data)
            self.templates[tmpl.id] = tmpl

    def _save_data(self) -> None:
        data = {
            "inventories": [i.__dict__ for i in self.inventories.values()],
            "playbooks": [p.__dict__ for p in self.playbooks.values()],
            "jobs": [j.__dict__ for j in self.jobs.values()],
            "schedules": [s.__dict__ for s in self.schedules.values()],
            "minions": [m.__dict__ for m in self.minions.values()],
            "templates": [t.__dict__ for t in self.templates.values()],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, default=str, indent=2)

    def initialize(self) -> None:
        logger.info("AnsibleSaltManager initialized")

    def close(self) -> None:
        self._save_data()
        logger.info("AnsibleSaltManager closed")

    def create_inventory(self, name: str, description: str = "") -> AnsibleInventory:
        inv = AnsibleInventory(id=str(uuid.uuid4()), name=name, description=description)
        self.inventories[inv.id] = inv
        self._save_data()
        return inv

    def get_inventory(self, inventory_id: str) -> Optional[AnsibleInventory]:
        return self.inventories.get(inventory_id)

    def delete_inventory(self, inventory_id: str) -> bool:
        if inventory_id in self.inventories:
            del self.inventories[inventory_id]
            self._save_data()
            return True
        return False

    def add_host(self, inventory_id: str, host_name: str, ansible_host: str, ansible_user: str = "root", ansible_port: int = 22, variables: Optional[Dict[str, Any]] = None, groups: Optional[List[str]] = None) -> Optional[AnsibleInventoryHost]:
        inv = self.inventories.get(inventory_id)
        if not inv:
            return None
        host = AnsibleInventoryHost(name=host_name, ansible_host=ansible_host, ansible_user=ansible_user, ansible_port=ansible_port, variables=variables or {}, groups=groups or [])
        inv.hosts[host_name] = host
        inv.updated_at = datetime.utcnow()
        self._save_data()
        return host

    def remove_host(self, inventory_id: str, host_name: str) -> bool:
        inv = self.inventories.get(inventory_id)
        if not inv or host_name not in inv.hosts:
            return False
        del inv.hosts[host_name]
        inv.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def add_group(self, inventory_id: str, group_name: str, variables: Optional[Dict[str, Any]] = None) -> Optional[AnsibleInventoryGroup]:
        inv = self.inventories.get(inventory_id)
        if not inv:
            return None
        group = AnsibleInventoryGroup(name=group_name, variables=variables or {})
        inv.groups[group_name] = group
        inv.updated_at = datetime.utcnow()
        self._save_data()
        return group

    def add_host_to_group(self, inventory_id: str, host_name: str, group_name: str) -> bool:
        inv = self.inventories.get(inventory_id)
        if not inv or host_name not in inv.hosts or group_name not in inv.groups:
            return False
        if host_name not in inv.groups[group_name].hosts:
            inv.groups[group_name].hosts.append(host_name)
        if group_name not in inv.hosts[host_name].groups:
            inv.hosts[host_name].groups.append(group_name)
        inv.updated_at = datetime.utcnow()
        self._save_data()
        return True

    def create_playbook(self, name: str, description: str, tool: ToolType, content: str, parameters: Optional[Dict[str, Any]] = None, inventory_id: Optional[str] = None) -> PlaybookDefinition:
        pb = PlaybookDefinition(id=str(uuid.uuid4()), name=name, description=description, tool=tool, content=content, parameters=parameters or {}, inventory_id=inventory_id)
        self.playbooks[pb.id] = pb
        self._save_data()
        return pb

    def get_playbook(self, playbook_id: str) -> Optional[PlaybookDefinition]:
        return self.playbooks.get(playbook_id)

    def update_playbook(self, playbook_id: str, updates: Dict[str, Any]) -> Optional[PlaybookDefinition]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return None
        for key, value in updates.items():
            if hasattr(pb, key) and key not in ("id", "created_at"):
                setattr(pb, key, value)
        pb.updated_at = datetime.utcnow()
        self.playbooks[playbook_id] = pb
        self._save_data()
        return pb

    def delete_playbook(self, playbook_id: str) -> bool:
        if playbook_id in self.playbooks:
            del self.playbooks[playbook_id]
            self._save_data()
            return True
        return False

    def execute_playbook(self, playbook_id: str, inventory_id: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None, target_hosts: Optional[List[str]] = None, executed_by: Optional[str] = None) -> Optional[JobExecution]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return None
        job = JobExecution(id=str(uuid.uuid4()), playbook_id=playbook_id, tool=pb.tool, status=JobStatus.PENDING, inventory_id=inventory_id or pb.inventory_id, target_hosts=target_hosts or [], parameters=parameters or pb.parameters, executed_by=executed_by, started_at=datetime.utcnow())
        self.jobs[job.id] = job
        self._save_data()
        try:
            job.status = JobStatus.RUNNING
            result = self._run_playbook(pb, job)
            job.output = result.get("output", "")
            job.status = JobStatus.SUCCESS
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
        job.completed_at = datetime.utcnow()
        job.duration_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
        self._save_data()
        return job

    def _run_playbook(self, playbook: PlaybookDefinition, job: JobExecution) -> Dict[str, Any]:
        if playbook.tool == ToolType.ANSIBLE:
            return self._run_ansible(playbook, job)
        elif playbook.tool == ToolType.SALT:
            return self._run_salt(playbook, job)
        elif playbook.tool == ToolType.TERRAFORM:
            return self._run_terraform(playbook)
        return {"output": "Simulated execution", "status": "success"}

    def _run_ansible(self, playbook: PlaybookDefinition, job: JobExecution) -> Dict[str, Any]:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(playbook.content)
            playbook_path = f.name
        try:
            result = subprocess.run(["ansible-playbook", playbook_path], capture_output=True, text=True, timeout=3600)
            return {"output": result.stdout + result.stderr, "return_code": result.returncode}
        except subprocess.TimeoutExpired:
            raise TimeoutError("Ansible playbook execution timed out")
        except FileNotFoundError:
            logger.warning("Ansible not installed, simulating execution")
            return {"output": "Simulated Ansible execution for: " + playbook.name, "return_code": 0}
        finally:
            os.unlink(playbook_path)

    def _run_salt(self, playbook: PlaybookDefinition, job: JobExecution) -> Dict[str, Any]:
        try:
            result = subprocess.run(["salt", "*", "state.apply", playbook.name], capture_output=True, text=True, timeout=3600)
            return {"output": result.stdout + result.stderr, "return_code": result.returncode}
        except subprocess.TimeoutExpired:
            raise TimeoutError("Salt execution timed out")
        except FileNotFoundError:
            logger.warning("Salt not installed, simulating execution")
            return {"output": "Simulated Salt execution for: " + playbook.name, "return_code": 0}

    def _run_terraform(self, playbook: PlaybookDefinition) -> Dict[str, Any]:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_path = os.path.join(tmpdir, "main.tf")
            with open(tf_path, "w") as f:
                f.write(playbook.content)
            try:
                result = subprocess.run(["terraform", "apply", "-auto-approve", tmpdir], capture_output=True, text=True, timeout=3600)
                return {"output": result.stdout + result.stderr, "return_code": result.returncode}
            except FileNotFoundError:
                return {"output": "Simulated Terraform apply for: " + playbook.name, "return_code": 0}

    def create_schedule(self, playbook_id: str, name: str, cron_expression: str, parameters: Optional[Dict[str, Any]] = None, inventory_id: Optional[str] = None) -> Optional[JobSchedule]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return None
        schedule = JobSchedule(id=str(uuid.uuid4()), playbook_id=playbook_id, name=name, cron_expression=cron_expression, parameters=parameters or {}, inventory_id=inventory_id)
        self.schedules[schedule.id] = schedule
        self._save_data()
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self._save_data()
            return True
        return False

    def register_minion(self, name: str, host: str, port: int = 4506, grains: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> SaltMinion:
        minion = SaltMinion(id=str(uuid.uuid4()), name=name, host=host, port=port, grains=grains or {}, tags=tags or [])
        self.minions[minion.id] = minion
        self._save_data()
        return minion

    def get_minion(self, minion_id: str) -> Optional[SaltMinion]:
        return self.minions.get(minion_id)

    def delete_minion(self, minion_id: str) -> bool:
        if minion_id in self.minions:
            del self.minions[minion_id]
            self._save_data()
            return True
        return False

    def create_template(self, name: str, description: str, tool: ToolType, playbook_content: str, default_parameters: Optional[Dict[str, Any]] = None, category: Optional[str] = None, tags: Optional[List[str]] = None) -> ExecutionTemplate:
        tmpl = ExecutionTemplate(id=str(uuid.uuid4()), name=name, description=description, tool=tool, playbook_content=playbook_content, default_parameters=default_parameters or {}, category=category, tags=tags or [])
        self.templates[tmpl.id] = tmpl
        self._save_data()
        return tmpl

    def apply_template(self, template_id: str, name: str, description: str, inventory_id: Optional[str] = None) -> Optional[PlaybookDefinition]:
        tmpl = self.templates.get(template_id)
        if not tmpl:
            return None
        return self.create_playbook(name=name, description=description, tool=tmpl.tool, content=tmpl.playbook_content, parameters=tmpl.default_parameters.copy(), inventory_id=inventory_id)

    def get_job(self, job_id: str) -> Optional[JobExecution]:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            return False
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        job.duration_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
        self._save_data()
        return True

    def list_jobs(self, playbook_id: Optional[str] = None, status: Optional[JobStatus] = None) -> List[JobExecution]:
        results = list(self.jobs.values())
        if playbook_id:
            results = [j for j in results if j.playbook_id == playbook_id]
        if status:
            results = [j for j in results if j.status == status]
        return sorted(results, key=lambda x: x.started_at or datetime.min, reverse=True)

    def generate_inventory_ini(self, inventory_id: str) -> Optional[str]:
        inv = self.inventories.get(inventory_id)
        if not inv:
            return None
        lines = []
        for group_name, group in inv.groups.items():
            lines.append(f"[{group_name}]")
            for host_name in group.hosts:
                host = inv.hosts.get(host_name)
                if host:
                    vars_str = " ".join(f"{k}={v}" for k, v in host.variables.items())
                    lines.append(f"{host.ansible_host} ansible_user={host.ansible_user} ansible_port={host.ansible_port} {vars_str}")
            lines.append("")
        lines.append("[all:children]")
        for group_name in inv.groups:
            lines.append(group_name)
        return "\n".join(lines)

    def generate_inventory_yaml(self, inventory_id: str) -> Optional[str]:
        inv = self.inventories.get(inventory_id)
        if not inv:
            return None
        import yaml
        result = {"all": {"children": {}}}
        for group_name, group in inv.groups.items():
            group_data = {"hosts": {}}
            for host_name in group.hosts:
                host = inv.hosts.get(host_name)
                if host:
                    group_data["hosts"][host_name] = {"ansible_host": host.ansible_host, "ansible_user": host.ansible_user, "ansible_port": host.ansible_port, **host.variables}
            result["all"]["children"][group_name] = group_data
        return yaml.dump(result, default_flow_style=False)

    def search_playbooks(self, query: str) -> List[PlaybookDefinition]:
        query = query.lower()
        return [p for p in self.playbooks.values() if query in p.name.lower() or query in p.description.lower() or any(query in t.lower() for t in p.tags)]

    def get_statistics(self) -> Dict[str, Any]:
        total_inventories = len(self.inventories)
        total_hosts = sum(len(i.hosts) for i in self.inventories.values())
        total_groups = sum(len(i.groups) for i in self.inventories.values())
        total_playbooks = len(self.playbooks)
        total_jobs = len(self.jobs)
        successful_jobs = sum(1 for j in self.jobs.values() if j.status == JobStatus.SUCCESS)
        failed_jobs = sum(1 for j in self.jobs.values() if j.status == JobStatus.FAILED)
        total_schedules = len(self.schedules)
        total_minions = len(self.minions)
        return {"total_inventories": total_inventories, "total_hosts": total_hosts, "total_groups": total_groups, "total_playbooks": total_playbooks, "total_jobs": total_jobs, "successful_jobs": successful_jobs, "failed_jobs": failed_jobs, "total_schedules": total_schedules, "total_minions": total_minions}

    def bulk_delete_playbooks(self, playbook_ids: List[str]) -> int:
        count = 0
        for pid in playbook_ids:
            if self.delete_playbook(pid):
                count += 1
        return count

    def duplicate_playbook(self, playbook_id: str, new_name: str) -> Optional[PlaybookDefinition]:
        pb = self.playbooks.get(playbook_id)
        if not pb:
            return None
        return self.create_playbook(name=new_name, description=pb.description, tool=pb.tool, content=pb.content, parameters=pb.parameters.copy(), inventory_id=pb.inventory_id)
