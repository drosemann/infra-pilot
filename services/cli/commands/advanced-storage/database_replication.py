\"\"\"database_replication CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('database_replication', help='Manage database_replication')
    parser.set_defaults(func=handle_database_replication)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_database_replication(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/database_replication')
    for item in data:
        print(f'{item}')
