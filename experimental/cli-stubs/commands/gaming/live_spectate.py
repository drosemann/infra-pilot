\"\"\"live_spectate CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('live_spectate', help='Manage live_spectate')
    parser.set_defaults(func=handle_live_spectate)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_live_spectate(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/live_spectate')
    for item in data:
        print(f'{item}')
