\"\"\"mod_publishing CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('mod_publishing', help='Manage mod_publishing')
    parser.set_defaults(func=handle_mod_publishing)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_mod_publishing(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/mod_publishing')
    for item in data:
        print(f'{item}')
