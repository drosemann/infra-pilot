\"\"\"backup_chain CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('backup_chain', help='Manage backup_chain')
    parser.set_defaults(func=handle_backup_chain)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_backup_chain(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/backup_chain')
    for item in data:
        print(f'{item}')
