from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)


class CostAllocationManager:
    """Cost allocation and chargeback with resource tagging, cost breakdown, and budget management"""

    MODES = ['chargeback', 'showback']

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tags_file = config.get('cost_tags_file', 'data/cost_tags.json')
        self.allocations_file = config.get('cost_allocations_file', 'data/cost_allocations.json')
        self.budgets_file = config.get('cost_budgets_file', 'data/cost_budgets.json')
        self.tags: List[Dict[str, Any]] = []
        self.allocations: List[Dict[str, Any]] = []
        self.budgets: List[Dict[str, Any]] = []
        self.mode = config.get('cost_mode', 'showback')
        self._load_data()

    def _load_data(self):
        for path, attr in [(self.tags_file, 'tags'), (self.allocations_file, 'allocations'), (self.budgets_file, 'budgets')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        setattr(self, attr, json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

    def _save_tags(self):
        try:
            os.makedirs(os.path.dirname(self.tags_file), exist_ok=True)
            with open(self.tags_file, 'w') as f:
                json.dump(self.tags, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cost tags: {e}")

    def _save_allocations(self):
        try:
            os.makedirs(os.path.dirname(self.allocations_file), exist_ok=True)
            with open(self.allocations_file, 'w') as f:
                json.dump(self.allocations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save allocations: {e}")

    def _save_budgets(self):
        try:
            os.makedirs(os.path.dirname(self.budgets_file), exist_ok=True)
            with open(self.budgets_file, 'w') as f:
                json.dump(self.budgets, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save budgets: {e}")

    async def create_tag(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tag = {
            'id': f'tag_{int(datetime.now().timestamp())}_{len(self.tags)}',
            'key': data.get('key', ''),
            'value': data.get('value', ''),
            'resource_id': data.get('resource_id', ''),
            'created_at': datetime.now().isoformat()
        }
        self.tags.append(tag)
        self._save_tags()
        return tag

    async def get_tags(self) -> List[Dict[str, Any]]:
        return self.tags

    async def delete_tag(self, tag_id: str) -> bool:
        for i, tag in enumerate(self.tags):
            if tag['id'] == tag_id:
                self.tags.pop(i)
                self._save_tags()
                return True
        return False

    async def get_cost_breakdown(self, tag_key: Optional[str] = None, period: Optional[str] = None) -> Dict[str, Any]:
        filtered = self.allocations
        if tag_key:
            tag_values = {t['resource_id'] for t in self.tags if t['key'] == tag_key}
            filtered = [a for a in filtered if a.get('resource_id') in tag_values]
        if period:
            filtered = [a for a in filtered if a.get('period') == period]
        total_cost = sum(a.get('cost', 0) for a in filtered)
        breakdown = {}
        for a in filtered:
            cat = a.get('category', 'uncategorized')
            breakdown[cat] = breakdown.get(cat, 0) + a.get('cost', 0)
        return {
            'total_cost': total_cost,
            'period': period or 'all',
            'tag_key': tag_key,
            'breakdown': breakdown,
            'entries': len(filtered)
        }

    async def record_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        allocation = {
            'id': f'alloc_{int(datetime.now().timestamp())}_{len(self.allocations)}',
            'resource_id': data.get('resource_id', ''),
            'resource_type': data.get('resource_type', 'compute'),
            'cost': data.get('cost', 0),
            'category': data.get('category', 'uncategorized'),
            'period': data.get('period', datetime.now().strftime('%Y-%m')),
            'mode': self.mode,
            'created_at': datetime.now().isoformat()
        }
        self.allocations.append(allocation)
        self._save_allocations()
        return allocation

    async def generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tag_key = data.get('tag_key')
        period = data.get('period', datetime.now().strftime('%Y-%m'))
        breakdown = await self.get_cost_breakdown(tag_key, period)
        report = {
            'id': f'report_{int(datetime.now().timestamp())}',
            'mode': self.mode,
            'period': period,
            'generated_at': datetime.now().isoformat(),
            'total_cost': breakdown['total_cost'],
            'breakdown': breakdown['breakdown'],
            'entries': breakdown['entries'],
            'budgets': [b for b in self.budgets if b.get('period') == period]
        }
        return report

    async def list_reports(self) -> List[Dict[str, Any]]:
        periods = sorted(set(a.get('period', 'unknown') for a in self.allocations), reverse=True)
        return [{'period': p, 'mode': self.mode, 'entries': len([a for a in self.allocations if a.get('period') == p])} for p in periods]

    async def create_budget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        budget = {
            'id': f'budget_{int(datetime.now().timestamp())}_{len(self.budgets)}',
            'name': data.get('name', 'Unnamed Budget'),
            'amount': data.get('amount', 0),
            'period': data.get('period', datetime.now().strftime('%Y-%m')),
            'category': data.get('category', 'general'),
            'spent': 0,
            'created_at': datetime.now().isoformat(),
            'notify_thresholds': data.get('notify_thresholds', [50, 80, 90, 100])
        }
        self.budgets.append(budget)
        self._save_budgets()
        return budget

    async def get_budgets(self) -> List[Dict[str, Any]]:
        return self.budgets

    async def update_budget(self, budget_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for budget in self.budgets:
            if budget['id'] == budget_id:
                budget.update(updates)
                budget['updated_at'] = datetime.now().isoformat()
                self._save_budgets()
                return budget
        return None
