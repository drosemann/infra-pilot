\"\"\"storage_tiering CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('storage_tiering', help='Manage storage_tiering')
    parser.set_defaults(func=handle_storage_tiering)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_storage_tiering(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/storage_tiering')
    for item in data:
        print(f'{item}')
