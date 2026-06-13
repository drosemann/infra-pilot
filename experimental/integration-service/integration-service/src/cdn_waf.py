from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class CDNProvider:
    """Abstract CDN provider"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def provision(self, domain: str, origin: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def purge(self, domain: str, files: Optional[List[str]] = None) -> bool:
        raise NotImplementedError

    async def get_status(self, domain: str) -> Dict[str, Any]:
        raise NotImplementedError


class BunnyCDNProvider(CDNProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('bunny_api_key', '')

    async def provision(self, domain: str, origin: str) -> Dict[str, Any]:
        logger.info(f"BunnyCDN: provisioning {domain} -> {origin}")
        return {'provider': 'bunny', 'domain': domain, 'origin': origin, 'status': 'provisioned'}

    async def purge(self, domain: str, files: Optional[List[str]] = None) -> bool:
        logger.info(f"BunnyCDN: purging {domain}")
        return True

    async def get_status(self, domain: str) -> Dict[str, Any]:
        return {'provider': 'bunny', 'domain': domain, 'status': 'active'}


class CloudflareCDNProvider(CDNProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_token = config.get('cloudflare_api_token', '')
        self.zone_id = config.get('cloudflare_zone_id', '')

    async def provision(self, domain: str, origin: str) -> Dict[str, Any]:
        logger.info(f"Cloudflare CDN: provisioning {domain} -> {origin}")
        return {'provider': 'cloudflare', 'domain': domain, 'origin': origin, 'status': 'provisioned'}

    async def purge(self, domain: str, files: Optional[List[str]] = None) -> bool:
        logger.info(f"Cloudflare CDN: purging {domain}")
        return True

    async def get_status(self, domain: str) -> Dict[str, Any]:
        return {'provider': 'cloudflare', 'domain': domain, 'status': 'active'}


class WAFRuleManager:
    """WAF rule management"""

    def __init__(self, rules_file: str):
        self.rules_file = rules_file
        self.rules: List[Dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self):
        os.makedirs(os.path.dirname(self.rules_file) or '.', exist_ok=True)
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    self.rules = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load WAF rules: {e}")

    def _save_rules(self):
        try:
            with open(self.rules_file, 'w') as f:
                json.dump(self.rules, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save WAF rules: {e}")

    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        rule = {
            'id': f"waf_{len(self.rules)}_{int(datetime.now().timestamp())}",
            'name': rule_data.get('name', ''),
            'description': rule_data.get('description', ''),
            'action': rule_data.get('action', 'block'),
            'priority': rule_data.get('priority', 50),
            'filter': rule_data.get('filter', ''),
            'enabled': rule_data.get('enabled', True),
            'created_at': datetime.now().isoformat()
        }
        self.rules.append(rule)
        self._save_rules()
        return rule

    async def list_rules(self) -> List[Dict[str, Any]]:
        return self.rules

    async def delete_rule(self, rule_id: str) -> bool:
        for i, r in enumerate(self.rules):
            if r['id'] == rule_id:
                self.rules.pop(i)
                self._save_rules()
                return True
        return False


class CDNWAFManager:
    """One-click CDN setup with caching rules and WAF management"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.config_file = config.get('cdn_config_file', 'data/cdn_configs.json')
        self.waf_rules_file = config.get('waf_rules_file', 'data/waf_rules.json')
        self.configs: List[Dict[str, Any]] = []
        self.cdn_provider: Optional[CDNProvider] = None
        self.waf_manager = WAFRuleManager(self.waf_rules_file)
        self._load_data()
        self._init_provider()

    def _init_provider(self):
        provider_type = self.config.get('cdn_provider', 'bunny')
        if provider_type == 'cloudflare':
            self.cdn_provider = CloudflareCDNProvider(self.config)
        else:
            self.cdn_provider = BunnyCDNProvider(self.config)

    def _load_data(self):
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.configs = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load CDN configs: {e}")

    def _save_configs(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save CDN configs: {e}")

    async def initialize(self):
        logger.info("CDNWAFManager initialized")

    async def close(self):
        logger.info("CDNWAFManager closed")

    async def provision(self, provision_data: Dict[str, Any]) -> Dict[str, Any]:
        domain = provision_data.get('domain', '')
        origin = provision_data.get('origin', '')
        if not domain or not origin:
            return {'error': 'domain and origin are required'}

        result = await self.cdn_provider.provision(domain, origin)
        config = {
            'id': f"cdn_{len(self.configs)}_{int(datetime.now().timestamp())}",
            'domain': domain,
            'origin': origin,
            'provider': result.get('provider', ''),
            'status': result.get('status', 'provisioned'),
            'caching_rules': provision_data.get('caching_rules', []),
            'created_at': datetime.now().isoformat()
        }
        self.configs.append(config)
        self._save_configs()
        return config

    async def get_status(self, domain: str) -> Optional[Dict[str, Any]]:
        for c in self.configs:
            if c['domain'] == domain:
                status = await self.cdn_provider.get_status(domain)
                return {**c, 'cdn_status': status}
        return None

    async def purge(self, domain: str, files: Optional[List[str]] = None) -> bool:
        return await self.cdn_provider.purge(domain, files)

    async def list_configs(self) -> List[Dict[str, Any]]:
        return self.configs

    async def create_caching_rule(self, cdn_id: str, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, c in enumerate(self.configs):
            if c['id'] == cdn_id:
                rule = {
                    'id': f"cache_{int(datetime.now().timestamp())}",
                    'path': rule_data.get('path', '/*'),
                    'ttl': rule_data.get('ttl', 3600),
                    'enabled': rule_data.get('enabled', True),
                    'created_at': datetime.now().isoformat()
                }
                if 'caching_rules' not in self.configs[i]:
                    self.configs[i]['caching_rules'] = []
                self.configs[i]['caching_rules'].append(rule)
                self._save_configs()
                return rule
        return None

    async def delete_caching_rule(self, cdn_id: str, rule_id: str) -> bool:
        for i, c in enumerate(self.configs):
            if c['id'] == cdn_id:
                rules = c.get('caching_rules', [])
                for j, r in enumerate(rules):
                    if r['id'] == rule_id:
                        self.configs[i]['caching_rules'].pop(j)
                        self._save_configs()
                        return True
        return False

    async def create_waf_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.waf_manager.create_rule(rule_data)

    async def list_waf_rules(self) -> List[Dict[str, Any]]:
        return await self.waf_manager.list_rules()

    async def delete_waf_rule(self, rule_id: str) -> bool:
        return await self.waf_manager.delete_rule(rule_id)
