\"\"\"immutable_vault CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('immutable_vault', help='Manage immutable_vault')
    parser.set_defaults(func=handle_immutable_vault)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_immutable_vault(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/immutable_vault')
    for item in data:
        print(f'{item}')
