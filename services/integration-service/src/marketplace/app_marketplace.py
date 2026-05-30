import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class MarketplaceApp:
    id: str
    name: str
    slug: str
    description: str
    summary: str
    version: str
    app_type: str
    categories: List[str]
    tags: List[str]
    icon_url: str
    screenshots: List[str]
    website_url: str
    source_url: str
    docs_url: str
    min_cpu: int
    min_ram_mb: int
    min_disk_gb: int
    ports: List[int]
    dependencies: List[str]
    config_schema: Dict[str, Any]
    docker_compose_template: str
    env_template: Dict[str, str]
    is_verified: bool
    downloads_count: int
    rating: float

@dataclass
class InstalledApp:
    id: str
    user_id: str
    app_id: str
    app_name: str
    status: str
    version_installed: str
    version_available: str
    config: Dict[str, Any]
    resource_usage: Dict[str, float]
    url: str
    deployed_at: str
    updated_at: str

class AppMarketplaceManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_path = config.get('data_path', 'data')
        self.catalog_file = os.path.join(self.data_path, 'app_catalog.json')
        self.installed_file = os.path.join(self.data_path, 'app_installed.json')
        self.catalog: Dict[str, MarketplaceApp] = {}
        self.installed: Dict[str, InstalledApp] = {}
        self._load_data()

    def _load_data(self):
        os.makedirs(self.data_path, exist_ok=True)
        for file_key, attr, cls in [
            (self.catalog_file, 'catalog', MarketplaceApp),
            (self.installed_file, 'installed', InstalledApp),
        ]:
            try:
                if os.path.exists(file_key):
                    with open(file_key, 'r') as f:
                        data = json.load(f)
                    storage = getattr(self, attr)
                    storage.clear()
                    for item in data:
                        storage[item['id']] = cls(**item)
            except Exception as e:
                logger.warning(f"Failed to load {attr}: {e}")

    def _save_data(self):
        for file_key, attr in [(self.catalog_file, 'catalog'), (self.installed_file, 'installed')]:
            try:
                storage = getattr(self, attr)
                data = [asdict(v) for v in storage.values()]
                with open(file_key, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to save {attr}: {e}")

    async def initialize(self):
        logger.info("AppMarketplaceManager initialized")
        if not self.catalog:
            await self._seed_catalog()

    async def close(self):
        self._save_data()

    async def _seed_catalog(self):
        apps = [
            {'name': 'WordPress', 'description': 'Popular CMS and blogging platform', 'categories': ['CMS', 'Blogging'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 10, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Nextcloud', 'description': 'Self-hosted productivity platform with file sync, calendar, contacts', 'categories': ['Productivity', 'File Sharing'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 20, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Minecraft Server', 'description': 'Vanilla Java Edition Minecraft server', 'categories': ['Gaming', 'Minecraft'], 'min_cpu': 2, 'min_ram_mb': 2048, 'min_disk_gb': 10, 'ports': [25565], 'is_verified': True},
            {'name': 'GitLab CE', 'description': 'Self-hosted Git repository manager and CI/CD', 'categories': ['Development', 'DevOps'], 'min_cpu': 4, 'min_ram_mb': 4096, 'min_disk_gb': 50, 'ports': [80, 443, 22], 'is_verified': True},
            {'name': 'Jellyfin', 'description': 'Media streaming server for movies, TV, music', 'categories': ['Media', 'Streaming'], 'min_cpu': 2, 'min_ram_mb': 2048, 'min_disk_gb': 50, 'ports': [8096, 8920], 'is_verified': True},
            {'name': 'Nginx Proxy Manager', 'description': 'Reverse proxy management with SSL', 'categories': ['Networking', 'Proxy'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 5, 'ports': [80, 443, 81], 'is_verified': True},
            {'name': 'PostgreSQL', 'description': 'Advanced open-source relational database', 'categories': ['Database', 'Development'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 10, 'ports': [5432], 'is_verified': True},
            {'name': 'Redis', 'description': 'In-memory data structure store, used as cache and message broker', 'categories': ['Database', 'Cache'], 'min_cpu': 1, 'min_ram_mb': 256, 'min_disk_gb': 1, 'ports': [6379], 'is_verified': True},
            {'name': 'MongoDB', 'description': 'NoSQL document database', 'categories': ['Database', 'Development'], 'min_cpu': 2, 'min_ram_mb': 2048, 'min_disk_gb': 20, 'ports': [27017], 'is_verified': True},
            {'name': 'Plausible Analytics', 'description': 'Privacy-friendly web analytics', 'categories': ['Analytics', 'Monitoring'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 10, 'ports': [8000], 'is_verified': True},
            {'name': 'Matomo', 'description': 'Full-featured web analytics platform', 'categories': ['Analytics', 'Marketing'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 20, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Grafana', 'description': 'Open-source monitoring and observability platform', 'categories': ['Monitoring', 'DevOps'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 10, 'ports': [3000], 'is_verified': True},
            {'name': 'Prometheus', 'description': 'Systems monitoring and alerting toolkit', 'categories': ['Monitoring', 'DevOps'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 50, 'ports': [9090], 'is_verified': True},
            {'name': 'Vaultwarden', 'description': 'Lightweight password manager (Bitwarden-compatible)', 'categories': ['Security', 'Productivity'], 'min_cpu': 1, 'min_ram_mb': 256, 'min_disk_gb': 1, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Pi-hole', 'description': 'DNS-based ad blocker and network-wide content filter', 'categories': ['Networking', 'Security'], 'min_cpu': 1, 'min_ram_mb': 256, 'min_disk_gb': 1, 'ports': [53, 80], 'is_verified': True},
            {'name': 'Home Assistant', 'description': 'Open-source home automation platform', 'categories': ['IoT', 'Automation'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 10, 'ports': [8123], 'is_verified': True},
            {'name': 'Gitea', 'description': 'Lightweight self-hosted Git service', 'categories': ['Development', 'DevOps'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 10, 'ports': [3000, 22], 'is_verified': True},
            {'name': 'Uptime Kuma', 'description': 'Self-hosted uptime monitoring tool', 'categories': ['Monitoring', 'DevOps'], 'min_cpu': 1, 'min_ram_mb': 256, 'min_disk_gb': 1, 'ports': [3001], 'is_verified': True},
            {'name': 'MinIO', 'description': 'S3-compatible object storage', 'categories': ['Storage', 'Infrastructure'], 'min_cpu': 2, 'min_ram_mb': 2048, 'min_disk_gb': 50, 'ports': [9000, 9001], 'is_verified': True},
            {'name': 'Drupal', 'description': 'Enterprise content management framework', 'categories': ['CMS', 'Enterprise'], 'min_cpu': 2, 'min_ram_mb': 2048, 'min_disk_gb': 20, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Ghost', 'description': 'Modern publishing platform for creators', 'categories': ['Blogging', 'CMS'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 5, 'ports': [2368], 'is_verified': True},
            {'name': 'Directus', 'description': 'Open-source headless CMS and API builder', 'categories': ['CMS', 'Development'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 10, 'ports': [8055], 'is_verified': True},
            {'name': 'Strapi', 'description': 'Leading open-source headless CMS', 'categories': ['CMS', 'Development'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 10, 'ports': [1337], 'is_verified': True},
            {'name': 'N8N', 'description': 'Workflow automation tool', 'categories': ['Automation', 'Productivity'], 'min_cpu': 1, 'min_ram_mb': 1024, 'min_disk_gb': 5, 'ports': [5678], 'is_verified': True},
            {'name': 'Node-RED', 'description': 'Flow-based visual programming for IoT', 'categories': ['IoT', 'Automation'], 'min_cpu': 1, 'min_ram_mb': 256, 'min_disk_gb': 1, 'ports': [1880], 'is_verified': True},
            {'name': 'Freshrss', 'description': 'Self-hosted RSS feed aggregator', 'categories': ['Media', 'Productivity'], 'min_cpu': 1, 'min_ram_mb': 256, 'min_disk_gb': 1, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Synapse (Matrix)', 'description': 'Matrix homeserver for decentralized communication', 'categories': ['Communication', 'Social'], 'min_cpu': 4, 'min_ram_mb': 4096, 'min_disk_gb': 50, 'ports': [8008, 8448], 'is_verified': True},
            {'name': 'Element Web', 'description': 'Matrix web client', 'categories': ['Communication', 'Social'], 'min_cpu': 1, 'min_ram_mb': 512, 'min_disk_gb': 1, 'ports': [80, 443], 'is_verified': True},
            {'name': 'Ollama', 'description': 'Run local LLMs like Llama 3, Mistral, Gemma', 'categories': ['AI', 'Machine Learning'], 'min_cpu': 4, 'min_ram_mb': 8192, 'min_disk_gb': 50, 'ports': [11434], 'is_verified': True},
            {'name': 'Jitsi Meet', 'description': 'Secure video conferencing platform', 'categories': ['Communication', 'Video'], 'min_cpu': 4, 'min_ram_mb': 4096, 'min_disk_gb': 10, 'ports': [80, 443, 10000], 'is_verified': True},
        ]
        for app_data in apps:
            aid = str(uuid.uuid4())
            slug = app_data['name'].lower().replace(' ', '-').replace('(', '').replace(')', '')
            app = MarketplaceApp(
                id=aid, name=app_data['name'], slug=slug,
                description=app_data['description'],
                summary=app_data['description'][:100],
                version='1.0.0', app_type='docker',
                categories=app_data['categories'], tags=app_data['categories'],
                icon_url=f'https://cdn.jsdelivr.net/gh/walkxcode/dashboard-icons/png/{slug}.png',
                screenshots=[], website_url=f'https://{slug}.org',
                source_url=f'https://github.com/{slug}', docs_url=f'https://docs.{slug}.org',
                min_cpu=app_data['min_cpu'], min_ram_mb=app_data['min_ram_mb'],
                min_disk_gb=app_data['min_disk_gb'], ports=app_data['ports'],
                dependencies=[], config_schema={},
                docker_compose_template=self._generate_compose_template(app_data['name'], app_data['ports']),
                env_template=self._generate_env_template(app_data['name']),
                is_verified=app_data['is_verified'], downloads_count=0, rating=4.5,
            )
            self.catalog[aid] = app
        self._save_data()
        logger.info(f"Seeded {len(apps)} apps to marketplace catalog")

    def _generate_compose_template(self, name: str, ports: List[int]) -> str:
        import json as j
        service_name = name.lower().replace(' ', '-').replace('(', '').replace(')', '')
        port_mappings = {f'{p}:{p}': f'${{PORT_{i}}}' for i, p in enumerate(ports[:5])}
        template = {
            'version': '3.8',
            'services': {
                service_name: {
                    'image': f'{service_name}:latest',
                    'restart': 'unless-stopped',
                    'ports': [f'${{PORT_{i}}}:{p}' for i, p in enumerate(ports[:5])],
                    'environment': {},
                    'volumes': [f'{service_name}_data:/data'],
                }
            },
            'volumes': {f'{service_name}_data': {}}
        }
        return j.dumps(template, indent=2)

    def _generate_env_template(self, name: str) -> Dict[str, str]:
        return {}

    async def list_apps(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        apps = list(self.catalog.values())
        if category:
            apps = [a for a in apps if category in a.categories]
        return [asdict(a) for a in sorted(apps, key=lambda x: x.downloads_count, reverse=True)]

    async def get_app(self, app_id: str) -> Optional[Dict[str, Any]]:
        app = self.catalog.get(app_id)
        return asdict(app) if app else None

    async def deploy_app(self, app_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        app = self.catalog.get(app_id)
        if not app:
            return None
        installed_id = str(uuid.uuid4())
        now = datetime.now()
        installed = InstalledApp(
            id=installed_id,
            user_id=config.get('user_id', ''),
            app_id=app_id,
            app_name=app.name,
            status='deploying',
            version_installed=app.version,
            version_available=app.version,
            config=config.get('env_vars', {}),
            resource_usage={'cpu': 0, 'ram_mb': 0, 'disk_gb': 0},
            url=f'https://{config.get("domain", f"{app.slug}.example.com")}',
            deployed_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        self.installed[installed.id] = installed
        app.downloads_count += 1
        self._save_data()
        return asdict(installed)

    async def list_installed(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(i) for i in self.installed.values() if i.user_id == user_id]

    async def get_installed(self, installed_id: str) -> Optional[Dict[str, Any]]:
        installed = self.installed.get(installed_id)
        return asdict(installed) if installed else None

    async def update_installed(self, installed_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        installed = self.installed.get(installed_id)
        if not installed:
            return None
        for key in ['config', 'status', 'version_installed', 'url']:
            if key in data:
                setattr(installed, key, data[key])
        installed.updated_at = datetime.now().isoformat()
        self._save_data()
        return asdict(installed)

    async def uninstall_app(self, installed_id: str) -> bool:
        if installed_id in self.installed:
            del self.installed[installed_id]
            self._save_data()
            return True
        return False

    async def get_categories(self) -> List[Dict[str, Any]]:
        categories = {}
        for app in self.catalog.values():
            for cat in app.categories:
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
        return [{'name': k, 'count': v} for k, v in sorted(categories.items(), key=lambda x: -x[1])]

    async def validate_config(self, app_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        app = self.catalog.get(app_id)
        if not app:
            return {'valid': False, 'errors': ['App not found']}
        errors = []
        required_fields = list(app.env_template.keys()) if app.env_template else []
        for field in required_fields:
            if field not in config:
                errors.append(f'Missing required field: {field}')
        return {'valid': len(errors) == 0, 'errors': errors}
