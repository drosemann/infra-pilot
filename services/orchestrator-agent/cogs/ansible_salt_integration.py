import json
import uuid
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AnsibleRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ansible_dir = config.get("ansible_dir", "/etc/infrapilot/ansible")
        self.ansible_playbook_cmd = config.get("ansible_playbook_cmd", "ansible-playbook")
        self.ansible_galaxy_cmd = config.get("ansible_galaxy_cmd", "ansible-galaxy")
        self.inventory_file = config.get("inventory_file", f"{self.ansible_dir}/inventory.yml")
        self.vault_password_file = config.get("vault_password_file")
        self._executions: Dict[str, Dict] = {}
        self._playbooks: Dict[str, Dict] = {}
        self._initialized = False

    async def initialize(self) -> None:
        self._scan_playbooks()
        self._initialized = True
        logger.info(f"AnsibleRunner initialized (dir: {self.ansible_dir})")

    async def close(self) -> None:
        self._executions.clear()
        logger.info("AnsibleRunner closed")

    def _scan_playbooks(self) -> None:
        import glob as glob_mod
        import os
        pattern = f"{self.ansible_dir}/**/*.yml"
        for playbook_path in glob_mod.glob(pattern, recursive=True):
            playbook_id = str(uuid.uuid4())
            name = os.path.splitext(os.path.basename(playbook_path))[0]
            self._playbooks[playbook_id] = {
                "playbook_id": playbook_id,
                "name": name,
                "path": playbook_path,
                "size": os.path.getsize(playbook_path),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(playbook_path)).isoformat(),
            }

    def list_playbooks(self) -> List[Dict]:
        return list(self._playbooks.values())

    def get_playbook(self, playbook_id: str) -> Optional[Dict]:
        return self._playbooks.get(playbook_id)

    async def execute_playbook(self, playbook_id: str, inventory_override: Optional[str] = None,
                                extra_vars: Optional[Dict] = None,
                                tags: Optional[List[str]] = None,
                                limit: Optional[str] = None) -> Dict:
        playbook = self._playbooks.get(playbook_id)
        if not playbook:
            raise ValueError(f"Playbook {playbook_id} not found")

        execution_id = str(uuid.uuid4())
        cmd = [self.ansible_playbook_cmd, playbook["path"]]
        if inventory_override:
            cmd.extend(["-i", inventory_override])
        else:
            cmd.extend(["-i", self.inventory_file])
        if self.vault_password_file:
            cmd.extend(["--vault-password-file", self.vault_password_file])
        if extra_vars:
            for key, value in extra_vars.items():
                cmd.extend(["-e", f"{key}={json.dumps(value) if isinstance(value, (dict, list)) else value}"])
        if tags:
            cmd.extend(["--tags", ",".join(tags)])
        if limit:
            cmd.extend(["--limit", limit])

        execution = {
            "execution_id": execution_id,
            "playbook_id": playbook_id,
            "playbook_name": playbook["name"],
            "command": " ".join(cmd),
            "status": ExecutionStatus.QUEUED.value,
            "started_at": None,
            "completed_at": None,
            "output": [],
            "return_code": None,
            "error": None,
        }
        self._executions[execution_id] = execution

        asyncio.create_task(self._run_execution(execution_id, cmd))
        logger.info(f"Ansible execution {execution_id} started: {playbook['name']}")
        return execution

    async def _run_execution(self, execution_id: str, cmd: List[str]) -> None:
        execution = self._executions[execution_id]
        execution["status"] = ExecutionStatus.RUNNING.value
        execution["started_at"] = datetime.utcnow().isoformat()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3600)
            execution["output"] = (stdout.decode() + stderr.decode()).split("\n")
            execution["return_code"] = process.returncode
            if process.returncode == 0:
                execution["status"] = ExecutionStatus.SUCCESS.value
            else:
                execution["status"] = ExecutionStatus.FAILED.value
                execution["error"] = stderr.decode()[:1000]
        except asyncio.TimeoutError:
            execution["status"] = ExecutionStatus.TIMEOUT.value
            execution["error"] = "Execution timed out after 3600 seconds"
        except Exception as e:
            execution["status"] = ExecutionStatus.FAILED.value
            execution["error"] = str(e)

        execution["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"Ansible execution {execution_id} completed: {execution['status']}")

    def get_execution(self, execution_id: str) -> Optional[Dict]:
        return self._executions.get(execution_id)

    def get_execution_output(self, execution_id: str, tail: int = 100) -> List[str]:
        execution = self._executions.get(execution_id)
        if not execution:
            return []
        return execution.get("output", [])[-tail:]

    def list_executions(self, playbook_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        executions = list(self._executions.values())
        if playbook_id:
            executions = [e for e in executions if e["playbook_id"] == playbook_id]
        executions.sort(key=lambda e: e.get("started_at", ""), reverse=True)
        return executions[:limit]

    def cancel_execution(self, execution_id: str) -> bool:
        execution = self._executions.get(execution_id)
        if not execution or execution["status"] not in (ExecutionStatus.QUEUED.value, ExecutionStatus.RUNNING.value):
            return False
        execution["status"] = ExecutionStatus.CANCELLED.value
        execution["error"] = "Cancelled by user"
        return True


class SaltRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.salt_cmd = config.get("salt_cmd", "salt")
        self.salt_ssh_cmd = config.get("salt_ssh_cmd", "salt-ssh")
        self.salt_dir = config.get("salt_dir", "/etc/infrapilot/salt")
        self._executions: Dict[str, Dict] = {}
        self._states: Dict[str, Dict] = {}
        self._minions: List[str] = config.get("default_minions", [])
        self._initialized = False

    async def initialize(self) -> None:
        self._scan_states()
        self._initialized = True
        logger.info(f"SaltRunner initialized with {len(self._minions)} minions")

    async def close(self) -> None:
        self._executions.clear()
        self._minions.clear()
        logger.info("SaltRunner closed")

    def _scan_states(self) -> None:
        import glob as glob_mod
        import os
        pattern = f"{self.salt_dir}/**/*.sls"
        for state_path in glob_mod.glob(pattern, recursive=True):
            state_id = str(uuid.uuid4())
            name = os.path.splitext(os.path.basename(state_path))[0]
            rel_path = os.path.relpath(state_path, self.salt_dir)
            self._states[state_id] = {
                "state_id": state_id,
                "name": name,
                "path": state_path,
                "relative_path": rel_path,
                "modified_at": datetime.fromtimestamp(os.path.getmtime(state_path)).isoformat(),
            }

    def list_states(self) -> List[Dict]:
        return list(self._states.values())

    def get_state(self, state_id: str) -> Optional[Dict]:
        return self._states.get(state_id)

    def list_minions(self) -> List[str]:
        return self._minions

    def add_minion(self, minion_id: str) -> None:
        if minion_id not in self._minions:
            self._minions.append(minion_id)

    def remove_minion(self, minion_id: str) -> bool:
        if minion_id in self._minions:
            self._minions.remove(minion_id)
            return True
        return False

    async def apply_state(self, state_id: str, target_minions: Optional[List[str]] = None,
                           pillar: Optional[Dict] = None) -> Dict:
        state = self._states.get(state_id)
        if not state:
            raise ValueError(f"State {state_id} not found")

        execution_id = str(uuid.uuid4())
        minions = target_minions or self._minions
        target = ",".join(minions) if minions else "*"

        cmd_parts = [self.salt_cmd, target, "state.apply", state["name"]]
        if pillar:
            cmd_parts.extend(["pillar={}".format(json.dumps(pillar))])

        execution = {
            "execution_id": execution_id,
            "state_id": state_id,
            "state_name": state["name"],
            "target": target,
            "command": " ".join(cmd_parts),
            "status": ExecutionStatus.QUEUED.value,
            "started_at": None,
            "completed_at": None,
            "output": [],
            "return_code": None,
            "error": None,
        }
        self._executions[execution_id] = execution

        asyncio.create_task(self._run_execution(execution_id, cmd_parts))
        return execution

    async def _run_execution(self, execution_id: str, cmd: List[str]) -> None:
        execution = self._executions[execution_id]
        execution["status"] = ExecutionStatus.RUNNING.value
        execution["started_at"] = datetime.utcnow().isoformat()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3600)
            execution["output"] = (stdout.decode() + stderr.decode()).split("\n")
            execution["return_code"] = process.returncode
            execution["status"] = ExecutionStatus.SUCCESS.value if process.returncode == 0 else ExecutionStatus.FAILED.value
            if process.returncode != 0:
                execution["error"] = stderr.decode()[:1000]
        except asyncio.TimeoutError:
            execution["status"] = ExecutionStatus.TIMEOUT.value
            execution["error"] = "Execution timed out"
        except Exception as e:
            execution["status"] = ExecutionStatus.FAILED.value
            execution["error"] = str(e)

        execution["completed_at"] = datetime.utcnow().isoformat()

    def get_execution(self, execution_id: str) -> Optional[Dict]:
        return self._executions.get(execution_id)

    def list_executions(self, limit: int = 50) -> List[Dict]:
        executions = list(self._executions.values())
        executions.sort(key=lambda e: e.get("started_at", ""), reverse=True)
        return executions[:limit]


class AnsibleSaltManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ansible = AnsibleRunner(config.get("ansible", {}))
        self.salt = SaltRunner(config.get("salt", {}))
        self._initialized = False

    async def initialize(self) -> None:
        await self.ansible.initialize()
        await self.salt.initialize()
        self._initialized = True
        logger.info("AnsibleSaltManager initialized")

    async def close(self) -> None:
        await self.ansible.close()
        await self.salt.close()
        logger.info("AnsibleSaltManager closed")

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "ansible_playbooks": len(self.ansible._playbooks),
            "ansible_executions": len(self.ansible._executions),
            "salt_states": len(self.salt._states),
            "salt_minions": len(self.salt._minions),
            "salt_executions": len(self.salt._executions),
        }
