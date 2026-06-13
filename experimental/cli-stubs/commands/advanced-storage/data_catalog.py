\"\"\"data_catalog CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('data_catalog', help='Manage data_catalog')
    parser.set_defaults(func=handle_data_catalog)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_data_catalog(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/data_catalog')
    for item in data:
        print(f'{item}')
