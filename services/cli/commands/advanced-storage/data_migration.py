\"\"\"data_migration CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('data_migration', help='Manage data_migration')
    parser.set_defaults(func=handle_data_migration)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_data_migration(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/data_migration')
    for item in data:
        print(f'{item}')
