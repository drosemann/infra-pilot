from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging
import asyncio

logger = logging.getLogger(__name__)


class ServiceMeshManager:
    """Istio/Linkerd abstraction: sidecar injection, mTLS, traffic routing, canary deployments"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_file = config.get('mesh_config_file', 'data/mesh_configs.json')
        self.routes_file = config.get('mesh_routes_file', 'data/mesh_routes.json')
        self.mesh_enabled = False
        self.mesh_type = config.get('mesh_provider', 'istio')
        self.configs: Dict[str, Any] = {}
        self.routes: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.configs = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load mesh configs: {e}")
        if os.path.exists(self.routes_file):
            try:
                with open(self.routes_file, 'r') as f:
                    self.routes = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load mesh routes: {e}")

    def _save_configs(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save mesh configs: {e}")

    def _save_routes(self):
        try:
            with open(self.routes_file, 'w') as f:
                json.dump(self.routes, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save mesh routes: {e}")

    async def initialize(self):
        logger.info(f"ServiceMeshManager initialized ({self.mesh_type})")

    async def close(self):
        logger.info("ServiceMeshManager closed")

    async def enable_mesh(self, mesh_config: Dict[str, Any]) -> Dict[str, Any]:
        self.mesh_enabled = True
        self.mesh_type = mesh_config.get('provider', self.mesh_type)
        self.configs = {
            'enabled': True,
            'provider': self.mesh_type,
            'mtls': mesh_config.get('mtls', True),
            'sidecar_injection': mesh_config.get('sidecar_injection', True),
            'namespace': mesh_config.get('namespace', 'default'),
            'updated_at': datetime.now().isoformat()
        }
        self._save_configs()
        return self.configs

    async def disable_mesh(self) -> Dict[str, Any]:
        self.mesh_enabled = False
        self.configs['enabled'] = False
        self.configs['updated_at'] = datetime.now().isoformat()
        self._save_configs()
        return self.configs

    async def get_status(self) -> Dict[str, Any]:
        return {
            'enabled': self.mesh_enabled,
            'provider': self.mesh_type,
            'config': self.configs,
            'active_routes': len(self.routes),
            'canaries_active': len([r for r in self.routes if r.get('type') == 'canary'])
        }

    async def create_route(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        route = {
            'id': f"route_{len(self.routes)}_{int(datetime.now().timestamp())}",
            'name': route_data.get('name', ''),
            'source': route_data.get('source', ''),
            'destination': route_data.get('destination', ''),
            'port': route_data.get('port', 80),
            'protocol': route_data.get('protocol', 'http'),
            'match': route_data.get('match', {}),
            'type': route_data.get('type', 'standard'),
            'created_at': datetime.now().isoformat()
        }
        self.routes.append(route)
        self._save_routes()
        return route

    async def list_routes(self) -> List[Dict[str, Any]]:
        return self.routes

    async def delete_route(self, route_id: str) -> bool:
        for i, r in enumerate(self.routes):
            if r['id'] == route_id:
                self.routes.pop(i)
                self._save_routes()
                return True
        return False

    async def create_canary(self, canary_data: Dict[str, Any]) -> Dict[str, Any]:
        canary = {
            'id': f"canary_{int(datetime.now().timestamp())}",
            'name': canary_data.get('name', ''),
            'target_service': canary_data.get('target_service', ''),
            'new_version': canary_data.get('new_version', ''),
            'current_version': canary_data.get('current_version', ''),
            'traffic_percent': canary_data.get('traffic_percent', 10),
            'metrics_gates': canary_data.get('metrics_gates', {}),
            'status': 'running',
            'created_at': datetime.now().isoformat()
        }
        route = {
            'id': f"canary_route_{int(datetime.now().timestamp())}",
            'name': f"canary-{canary['name']}",
            'source': canary['target_service'],
            'destination': f"{canary['target_service']}-canary",
            'port': 80,
            'protocol': 'http',
            'match': {'headers': {'version': canary['new_version']}, 'weight': canary['traffic_percent']},
            'type': 'canary',
            'canary_id': canary['id'],
            'created_at': datetime.now().isoformat()
        }
        self.routes.append(route)
        self._save_routes()
        return canary

    async def get_canary(self, canary_id: str) -> Optional[Dict[str, Any]]:
        for r in self.routes:
            if r.get('canary_id') == canary_id:
                return r
        return None
