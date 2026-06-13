import json
import re
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphQLParsingError(Exception):
    pass


class GraphQLValidationError(Exception):
    pass


def _tokenize(query: str) -> List[Dict[str, Any]]:
    tokens = []
    i = 0
    while i < len(query):
        c = query[i]
        if c in '{}():,':
            tokens.append({'type': 'punctuation', 'value': c})
            i += 1
        elif c.isspace() or c == '\n':
            i += 1
        elif c == '#':
            end = query.find('\n', i)
            if end == -1:
                end = len(query)
            i = end
        elif c == '"':
            end = query.find('"', i + 1)
            if end == -1:
                raise GraphQLParsingError('Unterminated string')
            tokens.append({'type': 'string', 'value': query[i + 1:end]})
            i = end + 1
        elif query[i:i + 3] == '"""':
            end = query.find('"""', i + 3)
            if end == -1:
                raise GraphQLParsingError('Unterminated block string')
            tokens.append({'type': 'string', 'value': query[i + 3:end]})
            i = end + 3
        elif c.isalpha() or c == '_':
            end = i
            while end < len(query) and (query[end].isalnum() or query[end] == '_'):
                end += 1
            word = query[i:end]
            tokens.append({'type': 'identifier', 'value': word})
            i = end
        elif c in '!@$':
            tokens.append({'type': 'punctuation', 'value': c})
            i += 1
        elif c == '.':
            if i + 2 < len(query) and query[i:i + 3] == '...':
                tokens.append({'type': 'punctuation', 'value': '...'})
                i += 3
            else:
                tokens.append({'type': 'punctuation', 'value': '.'})
                i += 1
        elif c in '0123456789-':
            end = i
            if c == '-':
                end += 1
            while end < len(query) and (query[end].isdigit() or query[end] == '.'):
                end += 1
            tokens.append({'type': 'number', 'value': query[i:end]})
            i = end
        elif c == '[':
            tokens.append({'type': 'punctuation', 'value': '['})
            i += 1
        elif c == ']':
            tokens.append({'type': 'punctuation', 'value': ']'})
            i += 1
        else:
            i += 1
    return tokens


def _parse_selection_set(tokens: List[Dict[str, Any]], pos: int) -> tuple:
    selections = []
    if pos >= len(tokens) or tokens[pos]['value'] != '{':
        return selections, pos
    pos += 1
    while pos < len(tokens) and tokens[pos]['value'] != '}':
        if tokens[pos]['value'] == '...':
            pos += 1
            name_token = tokens[pos] if pos < len(tokens) else None
            if name_token and name_token['type'] == 'identifier':
                selections.append({'type': 'fragment_spread', 'name': name_token['value']})
                pos += 1
            continue
        if tokens[pos]['type'] != 'identifier':
            pos += 1
            continue
        field_name = tokens[pos]['value']
        pos += 1
        alias = None
        if pos < len(tokens) and tokens[pos]['value'] == ':':
            alias = field_name
            pos += 1
            if pos < len(tokens) and tokens[pos]['type'] == 'identifier':
                field_name = tokens[pos]['value']
                pos += 1
        arguments = {}
        if pos < len(tokens) and tokens[pos]['value'] == '(':
            pos += 1
            while pos < len(tokens) and tokens[pos]['value'] != ')':
                if tokens[pos]['type'] == 'identifier':
                    arg_name = tokens[pos]['value']
                    pos += 1
                    if pos < len(tokens) and tokens[pos]['value'] == ':':
                        pos += 1
                        arg_val, pos = _parse_value(tokens, pos)
                        arguments[arg_name] = arg_val
                else:
                    pos += 1
            pos += 1
        directives = []
        while pos < len(tokens) and tokens[pos]['value'] == '@':
            pos += 1
            if pos < len(tokens) and tokens[pos]['type'] == 'identifier':
                directives.append(tokens[pos]['value'])
                pos += 1
        sub_selections = []
        if pos < len(tokens) and tokens[pos]['value'] == '{':
            sub_selections, pos = _parse_selection_set(tokens, pos)
        selections.append({
            'name': field_name,
            'alias': alias,
            'arguments': arguments,
            'selections': sub_selections,
            'directives': directives
        })
    if pos < len(tokens):
        pos += 1
    return selections, pos


def _parse_value(tokens: List[Dict[str, Any]], pos: int) -> tuple:
    if pos >= len(tokens):
        return None, pos
    tok = tokens[pos]
    if tok['type'] == 'string':
        return tok['value'], pos + 1
    if tok['type'] == 'number':
        if '.' in tok['value']:
            return float(tok['value']), pos + 1
        return int(tok['value']), pos + 1
    if tok['value'] == 'true':
        return True, pos + 1
    if tok['value'] == 'false':
        return False, pos + 1
    if tok['value'] == 'null':
        return None, pos + 1
    if tok['value'] == '[':
        pos += 1
        items = []
        while pos < len(tokens) and tokens[pos]['value'] != ']':
            item, pos = _parse_value(tokens, pos)
            items.append(item)
            if pos < len(tokens) and tokens[pos]['value'] == ',':
                pos += 1
        if pos < len(tokens):
            pos += 1
        return items, pos
    if tok['value'] == '{':
        pos += 1
        obj = {}
        while pos < len(tokens) and tokens[pos]['value'] != '}':
            if tokens[pos]['type'] == 'identifier':
                key = tokens[pos]['value']
                pos += 1
                if pos < len(tokens) and tokens[pos]['value'] == ':':
                    pos += 1
                    val, pos = _parse_value(tokens, pos)
                    obj[key] = val
            else:
                pos += 1
        if pos < len(tokens):
            pos += 1
        return obj, pos
    if tok['type'] == 'identifier':
        return tok['value'], pos + 1
    return None, pos


def _parse_operation(tokens: List[Dict[str, Any]], pos: int) -> Dict[str, Any]:
    operation_type = 'query'
    operation_name = None
    if pos < len(tokens) and tokens[pos]['type'] == 'identifier' and tokens[pos]['value'] in ('query', 'mutation', 'subscription'):
        operation_type = tokens[pos]['value']
        pos += 1
    if pos < len(tokens) and tokens[pos]['type'] == 'identifier':
        operation_name = tokens[pos]['value']
        pos += 1
    variable_defs = {}
    if pos < len(tokens) and tokens[pos]['value'] == '(':
        pos += 1
        while pos < len(tokens) and tokens[pos]['value'] != ')':
            if tokens[pos]['value'] == '$' and pos + 1 < len(tokens) and tokens[pos + 1]['type'] == 'identifier':
                var_name = tokens[pos + 1]['value']
                pos += 2
                if pos < len(tokens) and tokens[pos]['value'] == ':':
                    pos += 1
                    var_type = ''
                    while pos < len(tokens) and tokens[pos]['type'] != 'punctuation' and tokens[pos]['value'] not in (')', ','):
                        var_type += tokens[pos]['value']
                        pos += 1
                    variable_defs[var_name] = {'type': var_type}
                    default_val, pos = _parse_value(tokens, pos) if pos < len(tokens) and tokens[pos]['value'] == '=' else (None, pos)
                    if default_val is not None:
                        variable_defs[var_name]['default'] = default_val
            else:
                pos += 1
        if pos < len(tokens):
            pos += 1
    directives = []
    while pos < len(tokens) and tokens[pos]['value'] == '@':
        pos += 1
        if pos < len(tokens) and tokens[pos]['type'] == 'identifier':
            directives.append(tokens[pos]['value'])
            pos += 1
    selections, pos = _parse_selection_set(tokens, pos)
    return {
        'type': operation_type,
        'name': operation_name,
        'variable_definitions': variable_defs,
        'selections': selections,
        'directives': directives
    }


def parse_graphql(query: str) -> Dict[str, Any]:
    tokens = _tokenize(query)
    operations = []
    pos = 0
    while pos < len(tokens):
        if tokens[pos]['type'] == 'identifier' and tokens[pos]['value'] in ('query', 'mutation', 'subscription'):
            op, pos = _parse_operation(tokens, pos)
            operations.append(op)
        elif tokens[pos]['type'] == 'punctuation' and tokens[pos]['value'] == '{':
            op = {
                'type': 'query',
                'name': None,
                'variable_definitions': {},
                'selections': {},
                'directives': []
            }
            selections, pos = _parse_selection_set(tokens, pos)
            op['selections'] = selections
            operations.append(op)
        else:
            pos += 1
    return {'operations': operations}


def _calculate_complexity(selections: List[Dict[str, Any]], depth: int = 0, max_depth: int = 10) -> int:
    if depth > max_depth:
        return 0
    complexity = 0
    for sel in selections:
        complexity += 1 + depth
        if sel.get('selections'):
            complexity += _calculate_complexity(sel['selections'], depth + 1, max_depth)
    return complexity


class GraphQLHandler:
    """GraphQL API - Minimal GraphQL parser/executor with subscriptions"""

    def __init__(self, config: Dict[str, Any], resolvers: Optional[Dict[str, Callable]] = None):
        self.config = config
        self.max_depth = config.get('graphql_max_depth', 10)
        self.max_complexity = config.get('graphql_max_complexity', 100)
        self.resolvers = resolvers or {}
        self.subscriptions: Dict[str, List[Callable]] = {}
        self._type_defs = self._build_schema()

    def _build_schema(self) -> str:
        return """
type Query {
  servers(limit: Int, offset: Int): [Server]
  users(limit: Int, offset: Int): [User]
  alerts(limit: Int, offset: Int, status: String, severity: String): [Alert]
  backups(limit: Int, offset: Int): [Backup]
  logs(limit: Int, offset: Int, level: String): [Log]
  metrics(service: String): Metrics
  announcements(limit: Int, offset: Int): [Announcement]
  server(id: ID!): Server
  user(id: ID!): User
  alert(id: ID!): Alert
}

type Mutation {
  createServer(input: ServerInput!): Server
  updateServer(id: ID!, input: ServerInput!): Server
  deleteServer(id: ID!): Boolean
  createAlert(input: AlertInput!): Alert
  acknowledgeAlert(id: ID!): Alert
  createBackup(service: String!): Backup
  sendAnnouncement(input: AnnouncementInput!): Announcement
}

type Subscription {
  serverEvents: ServerEvent
  alertEvents: AlertEvent
  userEvents: UserEvent
}

type Server {
  id: ID
  name: String
  status: String
  cpu: Float
  memory: Float
  players: Int
  created_at: String
}

type User {
  id: ID
  email: String
  username: String
  roles: [String]
  created_at: String
}

type Alert {
  id: ID
  title: String
  message: String
  severity: String
  status: String
  source: String
  created_at: String
}

type Backup {
  id: ID
  service: String
  size: Int
  status: String
  created_at: String
}

type Log {
  id: ID
  level: String
  message: String
  service: String
  timestamp: String
}

type Metrics {
  cpu_percent: Float
  memory_percent: Float
  disk_usage: Float
  server_count: Int
  active_players: Int
  timestamp: String
}

type Announcement {
  id: ID
  title: String
  content: String
  scheduled_at: String
  status: String
}

type ServerEvent {
  event_type: String
  server_id: ID
  data: String
  timestamp: String
}

type AlertEvent {
  event_type: String
  alert_id: ID
  data: String
  timestamp: String
}

type UserEvent {
  event_type: String
  user_id: ID
  data: String
  timestamp: String
}

input ServerInput {
  name: String
  status: String
}

input AlertInput {
  title: String!
  message: String!
  severity: String
  source: String
}

input AnnouncementInput {
  title: String!
  content: String!
  scheduled_at: String
}
"""

    def get_schema_sdl(self) -> str:
        return self._type_defs

    def set_resolver(self, name: str, resolver: Callable):
        self.resolvers[name] = resolver

    def _resolve_field(self, field: Dict[str, Any], context: Dict[str, Any], root_value: Any = None) -> Any:
        field_name = field['name']
        resolver_key = field_name
        if root_value is not None:
            if isinstance(root_value, dict) and field_name in root_value:
                val = root_value[field_name]
                if field.get('selections') and isinstance(val, list):
                    return [self._resolve_selection_set(field['selections'], item, context) for item in val]
                if field.get('selections') and isinstance(val, dict):
                    return self._resolve_selection_set(field['selections'], val, context)
                return val
            return None
        resolver = self.resolvers.get(resolver_key)
        if resolver:
            args = {k: v for k, v in field.get('arguments', {}).items()}
            result = resolver(args, context)
            if field.get('selections') and result is not None:
                if isinstance(result, list):
                    return [self._resolve_selection_set(field['selections'], item, context) for item in result]
                if isinstance(result, dict):
                    return self._resolve_selection_set(field['selections'], result, context)
            return result
        return None

    def _resolve_selection_set(self, selections: List[Dict[str, Any]], root_value: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for field in selections:
            field_name = field['name']
            alias = field.get('alias') or field_name
            value = self._resolve_field(field, context, root_value)
            if value is not None:
                result[alias] = value
        return result

    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            parsed = parse_graphql(query)
        except GraphQLParsingError as e:
            return {'errors': [{'message': str(e)}]}
        ctx = context or {}
        ctx['variables'] = variables or {}
        results = []
        for operation in parsed.get('operations', []):
            complexity = _calculate_complexity(operation.get('selections', []), max_depth=self.max_depth)
            if complexity > self.max_complexity:
                return {'errors': [{'message': f'Query too complex: {complexity} > {self.max_complexity}'}]}
            depth = self._max_depth(operation.get('selections', []), 0)
            if depth > self.max_depth:
                return {'errors': [{'message': f'Query too deep: {depth} > {self.max_depth}'}]}
            op_type = operation.get('type', 'query')
            if op_type == 'subscription':
                sub_name = operation.get('selections', [{}])[0].get('name', '') if operation.get('selections') else ''
                return {'data': None, 'subscription': sub_name}
            result = self._resolve_selection_set(operation.get('selections', []), None, ctx)
            results.append(result)
        data = results[0] if len(results) == 1 else results
        return {'data': data}

    def _max_depth(self, selections: List[Dict[str, Any]], current: int) -> int:
        if not selections:
            return current
        max_d = current
        for sel in selections:
            if sel.get('selections'):
                d = self._max_depth(sel['selections'], current + 1)
                if d > max_d:
                    max_d = d
        return max_d

    async def subscribe(self, subscription_name: str, callback: Callable) -> str:
        sub_id = f'sub_{int(time.time())}_{os.urandom(4).hex()}' if __import__('os') else f'sub_{int(time.time())}_xxxx'
        sub_id = f'sub_{int(time.time())}_{__import__("os").urandom(4).hex()}'
        self.subscriptions.setdefault(subscription_name, []).append({'id': sub_id, 'callback': callback})
        return sub_id

    async def publish(self, subscription_name: str, data: Any):
        for sub in self.subscriptions.get(subscription_name, []):
            try:
                await sub['callback'](data)
            except Exception as e:
                logger.warning(f"Subscription callback failed: {e}")

    async def unsubscribe(self, sub_id: str) -> bool:
        for name in list(self.subscriptions.keys()):
            self.subscriptions[name] = [s for s in self.subscriptions[name] if s['id'] != sub_id]
        return True

    async def initialize(self):
        logger.info("GraphQLHandler initialized")

    async def close(self):
        self.subscriptions.clear()
        logger.info("GraphQLHandler closed")
