import json
import os
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


class TicketTriage:
    """Multi-platform ticket ingestion, classification, urgency scoring, and auto-routing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_file = config.get('triage_tickets_file', 'data/triage_tickets.json')
        self.tickets: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            with open(self.data_file) as f:
                self.tickets = json.load(f)
        except:
            self.tickets = []

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.tickets[-2000:], f, indent=2)

    def _classify_ticket(self, title: str, description: str) -> str:
        text = f'{title} {description}'.lower()
        if any(w in text for w in ['crash', 'down', 'offline', 'unreachable', 'timeout', '500', 'error']):
            return 'incident'
        if any(w in text for w in ['bug', 'broken', 'not working', 'issue', 'problem', 'failed']):
            return 'bug'
        if any(w in text for w in ['feature', 'request', 'suggestion', 'would like', 'please add']):
            return 'feature_request'
        if any(w in text for w in ['help', 'how to', 'question', 'guide', 'tutorial']):
            return 'support'
        if any(w in text for w in ['billing', 'payment', 'invoice', 'charge', 'refund', 'subscription']):
            return 'billing'
        return 'general'

    def _calculate_urgency(self, ticket: Dict[str, Any]) -> int:
        score = 0
        classification = ticket.get('classification', 'general')
        urgency_map = {'incident': 9, 'bug': 6, 'billing': 4, 'support': 3, 'feature_request': 2, 'general': 1}
        score += urgency_map.get(classification, 1)

        text = f"{ticket.get('title', '')} {ticket.get('description', '')}".lower()
        critical_keywords = ['urgent', 'critical', 'emergency', 'blocker', 'down', 'crash', 'data loss']
        score += sum(2 for kw in critical_keywords if kw in text)

        source_priority = {'discord': 3, 'email': 2, 'dashboard': 1, 'api': 1}
        score += source_priority.get(ticket.get('source', ''), 1)

        return min(score, 10)

    def _assignee_for_classification(self, classification: str) -> str:
        routing = {
            'incident': 'oncall-team',
            'bug': 'engineering',
            'feature_request': 'product',
            'support': 'support-team',
            'billing': 'finance',
            'general': 'support-team'
        }
        return routing.get(classification, 'support-team')

    def _suggested_solutions(self, classification: str, title: str, description: str) -> List[str]:
        text = f'{title} {description}'.lower()
        suggestions = []
        if classification == 'incident':
            suggestions.append('Check server health endpoints and restart affected services')
            suggestions.append('Review recent deployments and roll back if necessary')
            suggestions.append('Check resource usage (CPU, memory, disk) for anomalies')
            suggestions.append('Verify DNS and network connectivity')
        elif classification == 'bug':
            suggestions.append('Gather logs from affected service and check for error patterns')
            suggestions.append('Attempt to reproduce the issue in a staging environment')
            suggestions.append('Check if issue is related to a recent update or change')
        elif classification == 'support':
            suggestions.append('Review documentation for common setup steps')
            suggestions.append('Check FAQ for similar questions')
        elif classification == 'billing':
            suggestions.append('Verify current subscription plan and payment method')
            suggestions.append('Check invoice history for discrepancies')
        elif classification == 'feature_request':
            suggestions.append('Document the use case and expected behavior')
            suggestions.append('Check if similar feature exists or is on the roadmap')
        if 'server' in text:
            suggestions.append('Verify server is running via the status endpoint')
        if 'backup' in text:
            suggestions.append('Check backup logs and storage availability')
        return suggestions[:5]

    async def ingest_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        classification = self._classify_ticket(
            ticket_data.get('title', ''),
            ticket_data.get('description', '')
        )
        ticket = {
            'id': f'ticket_{len(self.tickets)}_{int(datetime.now().timestamp())}',
            'title': ticket_data.get('title', 'Untitled'),
            'description': ticket_data.get('description', ''),
            'source': ticket_data.get('source', 'api'),
            'platform': ticket_data.get('platform', ''),
            'reporter': ticket_data.get('reporter', ''),
            'classification': classification,
            'urgency': 0,
            'assigned_to': None,
            'status': 'open',
            'escalated': False,
            'escalated_at': None,
            'suggested_solutions': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'resolved_at': None
        }
        ticket['urgency'] = self._calculate_urgency(ticket)
        ticket['assigned_to'] = self._assignee_for_classification(classification)
        ticket['suggested_solutions'] = self._suggested_solutions(classification, ticket['title'], ticket['description'])
        self.tickets.append(ticket)
        self._save()
        return ticket

    async def get_queue(self, status: Optional[str] = None, classification: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        results = self.tickets
        if status:
            results = [t for t in results if t.get('status') == status]
        if classification:
            results = [t for t in results if t.get('classification') == classification]
        results.sort(key=lambda t: (t.get('urgency', 0), t.get('created_at', '')), reverse=True)
        return results[:limit]

    async def escalate_ticket(self, ticket_id: str, reason: str = '') -> Dict[str, Any]:
        for ticket in self.tickets:
            if ticket['id'] == ticket_id:
                if ticket.get('escalated'):
                    raise ValueError(f'Ticket {ticket_id} already escalated')
                ticket['escalated'] = True
                ticket['escalated_at'] = datetime.now().isoformat()
                ticket['escalation_reason'] = reason
                ticket['status'] = 'escalated'
                ticket['updated_at'] = datetime.now().isoformat()
                self._save()
                return ticket
        raise ValueError(f'Ticket {ticket_id} not found')

    async def get_stats(self) -> Dict[str, Any]:
        total = len(self.tickets)
        open_tickets = [t for t in self.tickets if t.get('status') == 'open']
        escalated = [t for t in self.tickets if t.get('escalated')]
        resolved = [t for t in self.tickets if t.get('status') == 'resolved']
        classifications = Counter(t.get('classification', 'unknown') for t in self.tickets)
        sources = Counter(t.get('source', 'unknown') for t in self.tickets)
        avg_urgency = round(sum(t.get('urgency', 0) for t in self.tickets) / max(total, 1), 1)
        return {
            'total_tickets': total,
            'open': len(open_tickets),
            'escalated': len(escalated),
            'resolved': len(resolved),
            'avg_urgency': avg_urgency,
            'by_classification': dict(classifications),
            'by_source': dict(sources),
            'timestamp': datetime.now().isoformat()
        }

    async def close(self):
        self._save()
